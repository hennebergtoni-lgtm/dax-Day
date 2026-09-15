"""Credential-free, aggregate Windows host-lane preflight.

This module performs only local capability checks, credential *shape* checks,
and unauthenticated DNS/TLS handshakes.  It never logs credential values and
never creates an IG session.  Results are published as a hash-bound diagnostic
bundle when the runtime root is writable.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
import importlib
import json
import locale
import os
from pathlib import Path
import platform
import shutil
import socket
import ssl
import struct
import subprocess
import sys
import tempfile
import time
from typing import Callable, Iterable, Mapping
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ig_demo_credential_contract import (  # noqa: E402
    REQUIRED_CREDENTIAL_KEYS,
    load_ig_demo_credential_values,
)


SCHEMA = "DAX_WINDOWS_HOST_PREFLIGHT_V1"
MANIFEST_SCHEMA = "DAX_WINDOWS_HOST_PREFLIGHT_MANIFEST_V1"
STATUSES = frozenset({"PASS", "FAIL", "BLOCKED", "UNKNOWN", "NOT_REQUIRED"})
SAFE_EXCEPTION_CLASSES = frozenset({
    "FileNotFoundError", "PermissionError", "TimeoutError", "OSError",
    "ValueError", "ImportError", "ModuleNotFoundError", "SSLError",
    "gaierror", "CalledProcessError", "JSONDecodeError", "UnicodeError",
    "RuntimeError",
})
CHECK_FAILURE_CODES: dict[str, str] = {
    "WINDOWS_IDENTITY": "HOST_WINDOWS_REQUIRED",
    "HOST_ARCHITECTURE": "HOST_ARCHITECTURE_INVALID",
    "HOST_LOCALE": "HOST_LOCALE_UNAVAILABLE",
    "HOST_TIMEZONE": "HOST_TIMEZONE_UNAVAILABLE",
    "HOST_UTC_CLOCK": "HOST_CLOCK_ABNORMAL",
    "TEMP_ROOT": "FILESYSTEM_TEMP_UNAVAILABLE",
    "TEMP_RW_CLEANUP": "FILESYSTEM_TEMP_RW_CLEANUP_FAILED",
    "POWERSHELL_RUNTIME": "POWERSHELL_RUNTIME_INVALID",
    "POWERSHELL_EXECUTABLE": "POWERSHELL_EXECUTABLE_INVALID",
    "POWERSHELL_LANGUAGE_MODE": "POWERSHELL_LANGUAGE_MODE_INVALID",
    "POWERSHELL_ARCHITECTURE": "POWERSHELL_ARCHITECTURE_INVALID",
    "GIT_EXECUTABLE": "GIT_EXECUTABLE_MISSING",
    "GIT_VERSION": "GIT_VERSION_FAILED",
    "GIT_ORIGIN": "GIT_ORIGIN_MISMATCH",
    "GIT_HEAD": "GIT_HEAD_MISMATCH",
    "GIT_CLONE": "GIT_CLONE_UNVERIFIED",
    "GIT_CHECKOUT": "GIT_CHECKOUT_UNVERIFIED",
    "GIT_LONG_PATH": "GIT_LONG_PATH_UNVERIFIED",
    "GIT_HOOKS_ISOLATION": "GIT_HOOKS_ISOLATION_UNVERIFIED",
    "RUNTIME_ROOT": "FILESYSTEM_RUNTIME_ROOT_UNAVAILABLE",
    "RUNTIME_REPARSE": "FILESYSTEM_RUNTIME_ROOT_REPARSE",
    "FILESYSTEM_RW": "FILESYSTEM_READ_WRITE_FAILED",
    "FILESYSTEM_ATOMIC": "FILESYSTEM_ATOMIC_REPLACE_FAILED",
    "FILESYSTEM_LONG_PATH": "FILESYSTEM_LONG_PATH_FAILED",
    "FILESYSTEM_CLEANUP": "FILESYSTEM_CLEANUP_FAILED_RETAINED",
    "PYTHON_VERSION": "PYTHON_VERSION_UNSUPPORTED",
    "PYTHON_ARCHITECTURE": "PYTHON_ARCHITECTURE_INVALID",
    "PYTHON_HOST_ARCHITECTURE": "PYTHON_HOST_ARCHITECTURE_MISMATCH",
    "PYTHON_EXECUTABLE": "PYTHON_EXECUTABLE_IDENTITY_INVALID",
    "PYTHON_STDLIB": "PYTHON_STDLIB_IMPORT_FAILED",
    "PYTHON_ISOLATED_MODE": "PYTHON_ISOLATED_MODE_FAILED",
    "PYTHON_THIRD_PARTY": "PYTHON_THIRD_PARTY_UNEXPECTED_REQUIREMENT",
    "IMPORT_DAXLAB": "IMPORT_DAXLAB_FAILED",
    "IMPORT_DAXLAB_ORIGIN": "IMPORT_DAXLAB_ORIGIN_MISMATCH",
    "IMPORT_COLLECTOR": "IMPORT_COLLECTOR_FAILED",
    "IMPORT_COLLECTOR_ORIGIN": "IMPORT_COLLECTOR_ORIGIN_MISMATCH",
    "COLLECTOR_SOURCE": "PYTHON_COLLECTOR_SOURCE_INVALID",
    "NETWORK_GITHUB_DNS": "NETWORK_GITHUB_DNS_FAILED",
    "NETWORK_GITHUB_TLS": "NETWORK_GITHUB_TLS_FAILED",
    "NETWORK_GITHUB_HTTPS": "NETWORK_GITHUB_HTTPS_FAILED",
    "NETWORK_IG_DNS": "NETWORK_IG_DNS_FAILED",
    "NETWORK_IG_TLS": "NETWORK_IG_TLS_FAILED",
    "NETWORK_IG_HTTPS": "NETWORK_IG_HTTPS_FAILED",
    "NETWORK_PROXY": "NETWORK_PROXY_PRESENT",
    "CREDENTIAL_FILE": "CREDENTIAL_FILE_UNAVAILABLE",
    "CREDENTIAL_ENCODING": "CREDENTIAL_ENCODING_INVALID",
    "CREDENTIAL_SHAPE": "CREDENTIAL_SHAPE_INVALID",
    "NAMESPACE_RULES": "EVIDENCE_NAMESPACE_INVALID",
    "NAMESPACE_AVAILABLE": "EVIDENCE_NAMESPACE_EXISTS",
    "JSON_UTF8": "EVIDENCE_JSON_UTF8_FAILED",
    "SAFETY_STATIC": "HOST_LANE_SAFETY_CONTRACT_FAILED",
}


@dataclass(frozen=True)
class Check:
    dimension: str
    check: str
    status: str
    reason_code: str
    observed_contract: str
    required_contract: str
    required: bool = True
    exception_class: str | None = None

    def __post_init__(self) -> None:
        if self.status not in STATUSES:
            raise ValueError("invalid preflight status")


def _safe_exception(exc: BaseException) -> str:
    name = type(exc).__name__
    return name if name in SAFE_EXCEPTION_CLASSES else "OTHER"


def _safe_text(value: object, *, limit: int = 120) -> str:
    text = str(value).replace("\r", " ").replace("\n", " ")
    return text[:limit] if text else "NONE"


class Matrix:
    def __init__(self) -> None:
        self.checks: list[Check] = []

    def add(self, dimension: str, check: str, status: str, reason: str,
            observed: object, required_contract: str, *, required: bool = True,
            exception: BaseException | None = None) -> None:
        self.checks.append(Check(
            dimension=dimension, check=check, status=status, reason_code=reason,
            observed_contract=_safe_text(observed),
            required_contract=required_contract, required=required,
            exception_class=None if exception is None else _safe_exception(exception),
        ))

    def run(self, dimension: str, check: str, required_contract: str,
            operation: Callable[[], object], *, required: bool = True,
            predicate: Callable[[object], bool] = bool,
            observed: Callable[[object], object] = lambda value: value) -> object | None:
        try:
            value = operation()
            if not predicate(value):
                self.add(dimension, check, "FAIL", CHECK_FAILURE_CODES[check],
                         observed(value), required_contract, required=required)
                return None
            self.add(dimension, check, "PASS", "NONE", observed(value),
                     required_contract, required=required)
            return value
        except Exception as exc:  # normalized, credential-free boundary
            self.add(dimension, check, "FAIL", CHECK_FAILURE_CODES[check],
                     "EXCEPTION", required_contract, required=required, exception=exc)
            return None

    @property
    def sufficient(self) -> bool:
        return all(
            item.status in {"PASS", "NOT_REQUIRED"}
            for item in self.checks if item.required
        )


def _run(args: list[str], *, cwd: Path | None = None) -> str:
    result = subprocess.run(
        args, cwd=cwd, check=True, capture_output=True, text=True,
        timeout=20, encoding="utf-8", errors="strict",
    )
    return result.stdout.strip()


def _dns(host: str) -> int:
    return len(socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM))


def _tls(host: str) -> str:
    context = ssl.create_default_context()
    with socket.create_connection((host, 443), timeout=10) as raw:
        with context.wrap_socket(raw, server_hostname=host) as wrapped:
            return wrapped.version() or "UNKNOWN"


def _https(url: str) -> str:
    request = Request(url, method="HEAD", headers={"User-Agent": "DAX-Host-Preflight/1"})
    try:
        with urlopen(request, timeout=10) as response:  # noqa: S310
            return f"HTTP_{int(response.status) // 100}XX"
    except HTTPError as exc:
        return f"HTTP_{int(exc.code) // 100}XX"


def _temp_probe() -> str:
    with tempfile.TemporaryDirectory(prefix="dax-hostlane-") as root:
        path = Path(root) / "probe.txt"
        path.write_text("ok", encoding="ascii")
        if path.read_text(encoding="ascii") != "ok":
            raise OSError("temp readback mismatch")
    if Path(root).exists():
        raise OSError("temp cleanup failed")
    return "CREATE_RW_DELETE_PASS"


def _is_reparse(path: Path) -> bool:
    attributes = getattr(path.stat(follow_symlinks=False), "st_file_attributes", 0)
    return path.is_symlink() or bool(attributes & 0x400)


def _origin_matches(remote: str, source_root: Path, allowed_origins: tuple[str, ...]) -> bool:
    if remote in allowed_origins:
        return True
    return Path(remote).resolve(strict=True) == source_root.resolve(strict=True)


def _credential_shape(path: Path) -> str:
    values = load_ig_demo_credential_values(path)
    if frozenset(values) != REQUIRED_CREDENTIAL_KEYS:
        raise RuntimeError("credential keys incomplete")
    return "EXACT_KEYS_PRESENT_VALUES_REDACTED"


def _filesystem_checks(matrix: Matrix, runtime_root: Path) -> None:
    root_ok = matrix.run(
        "FILESYSTEM", "RUNTIME_ROOT", "EXISTING_DIRECTORY",
        lambda: runtime_root.resolve(strict=True),
        predicate=lambda value: isinstance(value, Path) and value.is_dir(),
        observed=lambda _: "EXISTS_DIRECTORY",
    )
    if root_ok is None:
        for check, required in (
            ("RUNTIME_REPARSE", True), ("FILESYSTEM_RW", True),
            ("FILESYSTEM_ATOMIC", True), ("FILESYSTEM_LONG_PATH", True),
            ("FILESYSTEM_CLEANUP", True),
        ):
            matrix.add("FILESYSTEM", check, "BLOCKED", CHECK_FAILURE_CODES[check],
                       "RUNTIME_ROOT_BLOCKED", "PASS", required=required)
        return
    matrix.run(
        "FILESYSTEM", "RUNTIME_REPARSE", "NOT_SYMLINK_OR_REPARSE",
        lambda: not _is_reparse(runtime_root), predicate=lambda value: value is True,
        observed=lambda _: "NOT_REPARSE",
    )
    probe_root = runtime_root / ".runtime" / (".hostlane-probe-" + uuid4().hex)
    created = False
    try:
        probe_root.mkdir(parents=True, exist_ok=False)
        created = True
        source = probe_root / "source.json"
        target = probe_root / "target.json"
        payload = '{"probe":"utf8-✓"}\n'
        source.write_text(payload, encoding="utf-8")
        if source.read_text(encoding="utf-8") != payload:
            raise OSError("runtime readback mismatch")
        matrix.add("FILESYSTEM", "FILESYSTEM_RW", "PASS", "NONE",
                   "UTF8_WRITE_READ_PASS", "UTF8_WRITE_READ_PASS")
        os.replace(source, target)
        matrix.add("FILESYSTEM", "FILESYSTEM_ATOMIC", "PASS", "NONE",
                   "OS_REPLACE_PASS", "ATOMIC_REPLACE_PASS")
        long_parent = probe_root
        while len(str(long_parent)) < 280:
            long_parent = long_parent / ("p" * 24)
        long_parent.mkdir(parents=True)
        long_file = long_parent / "probe.txt"
        long_file.write_text("ok", encoding="ascii")
        if long_file.read_text(encoding="ascii") != "ok":
            raise OSError("long path readback mismatch")
        matrix.add("FILESYSTEM", "FILESYSTEM_LONG_PATH", "PASS", "NONE",
                   "LONG_PATH_RW_PASS", "LONG_PATH_RW_PASS")
    except Exception as exc:
        existing = {item.check for item in matrix.checks}
        for check in ("FILESYSTEM_RW", "FILESYSTEM_ATOMIC", "FILESYSTEM_LONG_PATH"):
            if check not in existing:
                matrix.add("FILESYSTEM", check, "FAIL", CHECK_FAILURE_CODES[check],
                           "EXCEPTION", "PASS", exception=exc)
    finally:
        if created:
            try:
                shutil.rmtree(probe_root)
                matrix.add("FILESYSTEM", "FILESYSTEM_CLEANUP", "PASS", "NONE",
                           "RUNNER_PROBE_REMOVED", "RUNNER_PROBE_REMOVED")
            except Exception as exc:
                matrix.add("FILESYSTEM", "FILESYSTEM_CLEANUP", "FAIL",
                           CHECK_FAILURE_CODES["FILESYSTEM_CLEANUP"],
                           "RUNNER_PROBE_RETAINED", "RUNNER_PROBE_REMOVED", exception=exc)


def _project_import_checks(matrix: Matrix, deployment_root: Path) -> None:
    source_root = deployment_root / "src"
    scripts_root = deployment_root / "scripts"
    collector = scripts_root / "run_ig_predemo_readiness_2238.py"
    matrix.run(
        "PYTHON", "COLLECTOR_SOURCE", "EXACT_HEAD_COLLECTOR_COMPILES",
        lambda: compile(collector.read_text(encoding="utf-8"), str(collector), "exec"),
        observed=lambda _: "COMPILE_PASS",
    )
    sys.path[:0] = [str(source_root), str(scripts_root)]
    daxlab = matrix.run(
        "IMPORT", "IMPORT_DAXLAB", "MODULE_IMPORT_PASS",
        lambda: importlib.import_module("daxlab.adapters.ig_market_data"),
        observed=lambda _: "IMPORT_PASS",
    )
    if daxlab is None:
        matrix.add("IMPORT", "IMPORT_DAXLAB_ORIGIN", "BLOCKED",
                   CHECK_FAILURE_CODES["IMPORT_DAXLAB_ORIGIN"], "IMPORT_BLOCKED",
                   "EXACT_DEPLOYMENT_SRC", required=True)
    else:
        matrix.run(
            "IMPORT", "IMPORT_DAXLAB_ORIGIN", "EXACT_DEPLOYMENT_SRC",
            lambda: Path(daxlab.__file__).resolve().is_relative_to(source_root.resolve()),
            predicate=lambda value: value is True, observed=lambda _: "EXACT_DEPLOYMENT_SRC",
        )
    runner = matrix.run(
        "IMPORT", "IMPORT_COLLECTOR", "MODULE_IMPORT_PASS",
        lambda: importlib.import_module("run_ig_predemo_readiness_2238"),
        observed=lambda _: "IMPORT_PASS",
    )
    if runner is None:
        matrix.add("IMPORT", "IMPORT_COLLECTOR_ORIGIN", "BLOCKED",
                   CHECK_FAILURE_CODES["IMPORT_COLLECTOR_ORIGIN"], "IMPORT_BLOCKED",
                   "EXACT_DEPLOYMENT_SCRIPT", required=True)
    else:
        matrix.run(
            "IMPORT", "IMPORT_COLLECTOR_ORIGIN", "EXACT_DEPLOYMENT_SCRIPT",
            lambda: Path(runner.__file__).resolve() == collector.resolve(),
            predicate=lambda value: value is True, observed=lambda _: "EXACT_DEPLOYMENT_SCRIPT",
        )


def _safety_static(collector: Path) -> str:
    source = collector.read_text(encoding="utf-8")
    forbidden = ("/positions/otc", "order_send", "order_execution_enabled=True")
    if any(token in source for token in forbidden):
        raise ValueError("unsafe collector surface")
    return "NONE_FALSE_NO_DEALING"


def collect(args: argparse.Namespace) -> dict[str, object]:
    matrix = Matrix()
    is_windows = platform.system() == "Windows"
    if is_windows:
        matrix.add("HOST", "WINDOWS_IDENTITY", "PASS", "NONE",
                   platform.version()[:80], "WINDOWS")
    elif args.allow_non_windows_ci:
        matrix.add("HOST", "WINDOWS_IDENTITY", "NOT_REQUIRED", "CI_NON_WINDOWS_ALLOWED",
                   platform.system(), "WINDOWS_REAL_HOST", required=False)
    else:
        matrix.add("HOST", "WINDOWS_IDENTITY", "FAIL", "HOST_WINDOWS_REQUIRED",
                   platform.system(), "WINDOWS")
    matrix.run("HOST", "HOST_ARCHITECTURE", "NONEMPTY_ARCHITECTURE",
               platform.machine, observed=lambda value: _safe_text(value))
    matrix.run("HOST", "HOST_LOCALE", "LOCALE_OBSERVABLE", locale.getlocale,
               observed=lambda value: "OBSERVED" if value else "NONE")
    matrix.run("HOST", "HOST_TIMEZONE", "TIMEZONE_OBSERVABLE",
               lambda: datetime.now().astimezone().tzname(), observed=lambda _: "OBSERVED")
    matrix.run("HOST", "HOST_UTC_CLOCK", "SANE_UTC_CLOCK",
               lambda: time.time(), predicate=lambda value: 1_700_000_000 < value < 4_102_444_800,
               observed=lambda _: "SANE_RANGE")
    matrix.run("HOST", "TEMP_ROOT", "EXISTING_WRITABLE_TEMP",
               lambda: Path(tempfile.gettempdir()).resolve(strict=True),
               predicate=lambda value: value.is_dir(), observed=lambda _: "AVAILABLE")
    matrix.run("HOST", "TEMP_RW_CLEANUP", "CREATE_RW_DELETE_PASS",
               _temp_probe, observed=lambda value: value)
    matrix.run("POWERSHELL", "POWERSHELL_RUNTIME", "VERSION_AND_EDITION_OBSERVED",
               lambda: (args.powershell_version, args.powershell_edition),
               predicate=lambda value: all(value),
               observed=lambda value: f"VERSION={value[0]};EDITION={value[1]}")
    matrix.run("POWERSHELL", "POWERSHELL_EXECUTABLE", "BASENAME_OBSERVED",
               lambda: args.powershell_executable,
               predicate=lambda value: isinstance(value, str) and bool(value)
               and value != "UNKNOWN",
               observed=lambda value: f"BASENAME={Path(value).name}")
    matrix.run("POWERSHELL", "POWERSHELL_LANGUAGE_MODE", "FULL_LANGUAGE",
               lambda: args.powershell_language_mode,
               predicate=lambda value: value == "FullLanguage", observed=lambda value: value)
    matrix.run("POWERSHELL", "POWERSHELL_ARCHITECTURE", "32_OR_64_BIT",
               lambda: args.powershell_architecture,
               predicate=lambda value: value in {"32_BIT", "64_BIT"}, observed=lambda value: value)

    deployment_root = args.deployment_root
    git_path = matrix.run("GIT", "GIT_EXECUTABLE", "APPLICATION_FOUND", lambda: shutil.which("git"),
                          observed=lambda value: Path(value).name if value else "NONE")
    if git_path:
        matrix.run("GIT", "GIT_VERSION", "VERSION_OBSERVED", lambda: _run([git_path, "--version"]),
                   observed=lambda value: value[:80])
        matrix.run("GIT", "GIT_ORIGIN", "PINNED_REPOSITORY_ORIGIN",
                   lambda: _run([git_path, "remote", "get-url", "origin"], cwd=deployment_root),
                   predicate=lambda value: _origin_matches(
                       value, args.deployment_source_root, args.allowed_origins
                   ),
                   observed=lambda _: "PINNED_ORIGIN")
        matrix.run("GIT", "GIT_HEAD", "EXPECTED_IMMUTABLE_HEAD",
                   lambda: _run([git_path, "rev-parse", "HEAD"], cwd=deployment_root),
                   predicate=lambda value: value == args.expected_head,
                   observed=lambda value: "MATCH" if value == args.expected_head else "MISMATCH")
    else:
        for check in ("GIT_VERSION", "GIT_ORIGIN", "GIT_HEAD"):
            matrix.add("GIT", check, "BLOCKED", CHECK_FAILURE_CODES[check],
                       "GIT_EXECUTABLE_BLOCKED", "PASS")
    for check, observed in (
        ("GIT_CLONE", args.git_clone), ("GIT_CHECKOUT", args.git_checkout),
        ("GIT_LONG_PATH", args.git_long_path), ("GIT_HOOKS_ISOLATION", args.git_hooks_isolation),
    ):
        matrix.add("GIT", check, "PASS" if observed == "PASS" else "FAIL",
                   "NONE" if observed == "PASS" else CHECK_FAILURE_CODES[check],
                   observed, "PASS")

    _filesystem_checks(matrix, args.runtime_root)
    matrix.run("PYTHON", "PYTHON_VERSION", "CPYTHON_3_11_PLUS", lambda: sys.version_info,
               predicate=lambda value: value >= (3, 11),
               observed=lambda value: f"{value.major}.{value.minor}.{value.micro}")
    matrix.run("PYTHON", "PYTHON_ARCHITECTURE", "32_OR_64_BIT",
               lambda: struct.calcsize("P") * 8, predicate=lambda value: value in {32, 64},
               observed=lambda value: f"{value}_BIT")
    matrix.run("PYTHON", "PYTHON_HOST_ARCHITECTURE", "MATCH_POWERSHELL_PROCESS",
               lambda: (struct.calcsize("P") * 8, args.powershell_architecture),
               predicate=lambda value: f"{value[0]}_BIT" == value[1],
               observed=lambda value: f"PYTHON={value[0]}_BIT;POWERSHELL={value[1]}")
    matrix.run("PYTHON", "PYTHON_EXECUTABLE", "ABSOLUTE_EXISTING_EXECUTABLE",
               lambda: Path(sys.executable).resolve(strict=True),
               observed=lambda value: f"BASENAME={value.name};HASH={sha256(str(value).encode()).hexdigest()[:16]}")
    matrix.run("PYTHON", "PYTHON_STDLIB", "REQUIRED_STDLIB_IMPORTS",
               lambda: tuple(importlib.import_module(name).__name__ for name in
                             ("json", "ssl", "socket", "urllib.request", "pathlib", "hashlib")),
               observed=lambda _: "REQUIRED_STDLIB_PASS")
    matrix.run("PYTHON", "PYTHON_ISOLATED_MODE", "ISOLATED_MODE_EXECUTES",
               lambda: _run([sys.executable, "-I", "-c", "import json,sys;print(sys.flags.isolated)"]),
               predicate=lambda value: value == "1", observed=lambda _: "SUPPORTED_NOT_REQUIRED_FOR_PAYLOAD")
    matrix.add("PYTHON", "PYTHON_THIRD_PARTY", "NOT_REQUIRED", "STDLIB_ONLY_HOST_LANE",
               "NO_THIRD_PARTY_DEPENDENCY", "NOT_REQUIRED", required=False)
    _project_import_checks(matrix, deployment_root)

    for host, prefix, url in (
        ("github.com", "GITHUB", "https://github.com/"),
        ("demo-api.ig.com", "IG", "https://demo-api.ig.com/gateway/deal/"),
    ):
        matrix.run("NETWORK", f"NETWORK_{prefix}_DNS", "DNS_RESOLUTION_PASS",
                   lambda host=host: _dns(host), predicate=lambda value: value > 0,
                   observed=lambda value: f"ADDRESS_COUNT={value}")
        matrix.run("NETWORK", f"NETWORK_{prefix}_TLS", "TLS_HANDSHAKE_PASS",
                   lambda host=host: _tls(host),
                   predicate=lambda value: value.startswith("TLS"), observed=lambda value: value)
        matrix.run("NETWORK", f"NETWORK_{prefix}_HTTPS", "HTTPS_STACK_REACHABLE",
                   lambda url=url: _https(url),
                   predicate=lambda value: value in {"HTTP_2XX", "HTTP_3XX", "HTTP_4XX"},
                   observed=lambda value: value)
    proxy_names = sorted(name for name in os.environ if name.casefold() in {
        "http_proxy", "https_proxy", "all_proxy", "no_proxy"
    })
    matrix.add("NETWORK", "NETWORK_PROXY", "UNKNOWN" if proxy_names else "PASS",
               "NETWORK_PROXY_PRESENT" if proxy_names else "NONE",
               "NAMES=" + ",".join(proxy_names) if proxy_names else "NONE",
               "OBSERVED_NON_BLOCKING", required=False)

    credential = args.credentials_file
    exists = matrix.run("CREDENTIAL", "CREDENTIAL_FILE", "EXISTING_READABLE_FILE",
                        lambda: credential.resolve(strict=True),
                        predicate=lambda value: value.is_file(), observed=lambda _: "EXISTS_FILE")
    if exists:
        matrix.run("CREDENTIAL", "CREDENTIAL_ENCODING", "UTF8_READABLE",
                   lambda: credential.read_text(encoding="utf-8"),
                   observed=lambda _: "UTF8_READ_PASS")
        matrix.run("CREDENTIAL", "CREDENTIAL_SHAPE", "EXACT_REQUIRED_KEYS_NONEMPTY",
                   lambda: _credential_shape(credential), observed=lambda value: value)
    else:
        for check in ("CREDENTIAL_ENCODING", "CREDENTIAL_SHAPE"):
            matrix.add("CREDENTIAL", check, "BLOCKED", CHECK_FAILURE_CODES[check],
                       "FILE_BLOCKED", "PASS")

    namespace = args.namespace
    namespace_valid = not namespace.is_absolute() and ".." not in namespace.parts
    matrix.add("EVIDENCE", "NAMESPACE_RULES", "PASS" if namespace_valid else "FAIL",
               "NONE" if namespace_valid else CHECK_FAILURE_CODES["NAMESPACE_RULES"],
               "SAFE_RELATIVE" if namespace_valid else "INVALID", "SAFE_RELATIVE")
    namespace_exists = args.runtime_root / namespace
    matrix.add("EVIDENCE", "NAMESPACE_AVAILABLE",
               "PASS" if namespace_valid and not namespace_exists.exists() else "FAIL",
               "NONE" if namespace_valid and not namespace_exists.exists()
               else CHECK_FAILURE_CODES["NAMESPACE_AVAILABLE"],
               "AVAILABLE" if namespace_valid and not namespace_exists.exists() else "EXISTS_OR_INVALID",
               "AVAILABLE")
    matrix.run("EVIDENCE", "JSON_UTF8", "STRICT_JSON_UTF8_ROUNDTRIP",
               lambda: json.loads(json.dumps({"utf8": "✓"}, ensure_ascii=False)),
               predicate=lambda value: value == {"utf8": "✓"}, observed=lambda _: "ROUNDTRIP_PASS")
    matrix.run("SAFETY", "SAFETY_STATIC", "NONE_FALSE_NO_DEALING",
               lambda: _safety_static(
                   deployment_root / "scripts" / "run_ig_predemo_readiness_2238.py"
               ), observed=lambda value: value)

    counts = {status: sum(item.status == status for item in matrix.checks) for status in STATUSES}
    return {
        "schema": SCHEMA,
        "status": "PASS" if matrix.sufficient else "BLOCKED",
        "error_code": "NONE" if matrix.sufficient else "PREFLIGHT_REQUIRED_CHECK_FAILED",
        "checks": [asdict(item) for item in matrix.checks],
        "counts": counts,
        "host_fingerprint": sha256(platform.node().encode()).hexdigest(),
        "expected_head": args.expected_head,
        "linux_worker": "NOT_REQUIRED_FOR_REAL_HOST",
        "execution_capability": "NONE",
        "order_execution_enabled": False,
    }


def publish(runtime_root: Path, payload: Mapping[str, object]) -> tuple[str, str]:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    relative = Path(".runtime") / "host_lane_preflight_2238" / f"{stamp}_{uuid4().hex}"
    final = runtime_root / relative
    staging = final.with_name(final.name + ".partial")
    staging.mkdir(parents=True, exist_ok=False)
    try:
        rendered = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        preflight_hash = sha256(rendered.encode("utf-8")).hexdigest()
        (staging / "PREFLIGHT.json").write_bytes(rendered.encode("utf-8"))
        manifest = {
            "schema": MANIFEST_SCHEMA, "exact_head": payload["expected_head"],
            "files": {"PREFLIGHT.json": preflight_hash},
            "execution_capability": "NONE", "order_execution_enabled": False,
        }
        manifest_rendered = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
        (staging / "MANIFEST.json").write_bytes(manifest_rendered.encode("utf-8"))
        os.replace(staging, final)
        observed = sha256((final / "PREFLIGHT.json").read_bytes()).hexdigest()
        if observed != preflight_hash:
            raise OSError("preflight readback mismatch")
        return str(relative).replace("\\", "/"), preflight_hash
    except Exception:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
        raise


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--expected-head", required=True)
    result.add_argument("--deployment-root", required=True, type=Path)
    result.add_argument("--deployment-source-root", required=True, type=Path)
    result.add_argument("--runtime-root", required=True, type=Path)
    result.add_argument("--namespace", required=True, type=Path)
    result.add_argument("--credentials-file", required=True, type=Path)
    result.add_argument("--powershell-version", required=True)
    result.add_argument("--powershell-edition", required=True)
    result.add_argument("--powershell-executable", required=True)
    result.add_argument("--powershell-language-mode", required=True)
    result.add_argument("--powershell-architecture", choices=("32_BIT", "64_BIT"), required=True)
    result.add_argument("--git-clone", choices=("PASS", "FAIL"), required=True)
    result.add_argument("--git-checkout", choices=("PASS", "FAIL"), required=True)
    result.add_argument("--git-long-path", choices=("PASS", "FAIL"), required=True)
    result.add_argument("--git-hooks-isolation", choices=("PASS", "FAIL"), required=True)
    result.add_argument("--allow-non-windows-ci", action="store_true")
    result.set_defaults(allowed_origins=(
        "https://github.com/hennebergtoni-lgtm/dax-Day.git",
        "https://github.com/hennebergtoni-lgtm/dax-Day",
        "git@github.com:hennebergtoni-lgtm/dax-Day.git",
    ))
    return result


def main(argv: Iterable[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        payload = collect(args)
        try:
            namespace, fingerprint = publish(args.runtime_root, payload)
        except Exception as exc:
            payload = dict(payload)
            payload["status"] = "BLOCKED"
            payload["error_code"] = "EVIDENCE_PREFLIGHT_PUBLICATION_FAILED"
            payload["publication_exception_class"] = _safe_exception(exc)
            namespace, fingerprint = None, None
        result = dict(payload)
        result["diagnostic_namespace"] = namespace
        result["diagnostic_fingerprint"] = fingerprint
    except Exception as exc:
        result = {
            "schema": SCHEMA, "status": "BLOCKED",
            "error_code": "PREFLIGHT_INTERNAL_FAILURE",
            "exception_class": _safe_exception(exc), "checks": [],
            "execution_capability": "NONE", "order_execution_enabled": False,
        }
    print(json.dumps(result, sort_keys=True, ensure_ascii=True))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
