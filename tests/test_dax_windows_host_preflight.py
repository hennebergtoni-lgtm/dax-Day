from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "dax_windows_host_preflight", ROOT / "scripts/dax_windows_host_preflight.py"
)
assert SPEC and SPEC.loader
preflight = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = preflight
SPEC.loader.exec_module(preflight)

FAILURE_SCENARIOS = {
    "multiple_distinct_valid_python_runtimes": "PYTHON_RUNTIME_AMBIGUOUS",
    "multiple_resolvers_same_runtime": "NONE",
    "microsoft_store_alias": "PYTHON_CANDIDATE_STORE_ALIAS_REJECTED",
    "path_duplicate": "NONE",
    "one_valid_candidate_among_many": "NONE",
    "python_missing": "PYTHON_COMMAND_RESULT_NULL",
    "python_wrong_version": "PYTHON_VERSION_UNSUPPORTED",
    "python_path_invalid": "PYTHON_EXECUTABLE_PATH_FAILED",
    "python_architecture_mismatch": "PYTHON_HOST_ARCHITECTURE_MISMATCH",
    "import_missing": "IMPORT_DAXLAB_FAILED",
    "wrong_import_origin": "IMPORT_DAXLAB_ORIGIN_MISMATCH",
    "module_shadowing": "IMPORT_COLLECTOR_ORIGIN_MISMATCH",
    "collector_missing": "HOST_LANE_SCRIPT_MISSING",
    "collector_invalid": "PYTHON_COLLECTOR_SOURCE_INVALID",
    "collector_no_output": "HOST_LANE_PROCESS_NO_OUTPUT",
    "collector_multiline_output": "HOST_LANE_PROCESS_MULTILINE_OUTPUT",
    "collector_invalid_json": "HOST_LANE_PROCESS_JSON_INVALID",
    "collector_wrong_exit_code": "HOST_LANE_PROCESS_EXIT_MISMATCH",
    "runtime_root_read_only": "FILESYSTEM_READ_WRITE_FAILED",
    "runtime_root_unavailable": "FILESYSTEM_RUNTIME_ROOT_UNAVAILABLE",
    "namespace_exists": "EVIDENCE_NAMESPACE_EXISTS",
    "temp_unavailable": "FILESYSTEM_TEMP_UNAVAILABLE",
    "git_missing": "GIT_EXECUTABLE_MISSING",
    "git_fetch_fail": "FETCH_FAILED",
    "git_clone_fail": "LOCAL_CLONE_FAILED",
    "git_checkout_fail": "ISOLATED_CHECKOUT_FAILED",
    "path_too_long": "FILESYSTEM_LONG_PATH_FAILED",
    "cleanup_denied": "DEPLOYMENT_CLEANUP_FAILED_RETAINED",
    "dns_fail": "NETWORK_GITHUB_DNS_FAILED",
    "tls_fail": "NETWORK_GITHUB_TLS_FAILED",
    "github_unavailable": "NETWORK_GITHUB_HTTPS_FAILED",
    "ig_http_transport_unavailable": "NETWORK_IG_HTTPS_TRANSPORT_FAILED",
    "ig_provider_health_unauthenticated": "IG_PROVIDER_HEALTH_NO_PUBLIC_ENDPOINT",
    "proxy_interference": "NETWORK_PROXY_PRESENT",
    "credentials_file_missing": "CREDENTIAL_FILE_UNAVAILABLE",
    "credentials_malformed": "CREDENTIAL_SHAPE_INVALID",
    "clock_abnormal": "HOST_CLOCK_ABNORMAL",
    "publication_partial": "EVIDENCE_PUBLICATION_FAILED",
    "publication_readback_mismatch": "EVIDENCE_PUBLICATION_FAILED",
}


def _args(tmp_path: Path) -> argparse.Namespace:
    credentials = tmp_path / "credentials.env"
    credentials.write_text(
        "IG_USERNAME=user\nIG_PASSWORD=password\nIG_API_KEY=key\n",
        encoding="utf-8",
    )
    return argparse.Namespace(
        expected_head="a" * 40,
        deployment_root=ROOT,
        deployment_source_root=ROOT,
        runtime_root=tmp_path,
        namespace=Path(".runtime/readiness"),
        credentials_file=credentials,
        powershell_version="7.5.0",
        powershell_edition="Core",
        powershell_executable="pwsh.exe",
        powershell_language_mode="FullLanguage",
        powershell_architecture=f"{preflight.struct.calcsize('P') * 8}_BIT",
        git_clone="PASS",
        git_checkout="PASS",
        git_long_path="PASS",
        git_hooks_isolation="PASS",
        allow_non_windows_ci=True,
        allowed_origins=("PINNED",),
    )


def _safe_run(args: list[str], *, cwd=None) -> str:
    if "--version" in args:
        return "git version 2.50.0"
    if "get-url" in args:
        return "PINNED"
    if "rev-parse" in args:
        return "a" * 40
    if "-I" in args:
        return "1"
    raise AssertionError(args)


def _patch_success(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in tuple(sys.modules):
        if (
            name == "daxlab"
            or name.startswith("daxlab.")
            or name == "run_ig_predemo_readiness_2238"
        ):
            monkeypatch.delitem(sys.modules, name)
    monkeypatch.setattr(preflight.shutil, "which", lambda name: "/usr/bin/git")
    monkeypatch.setattr(preflight, "_run", _safe_run)
    monkeypatch.setattr(preflight, "_dns", lambda host: 2)
    monkeypatch.setattr(preflight, "_tls", lambda host: "TLSv1.3")
    monkeypatch.setattr(preflight, "_https", lambda url: "HTTP_2XX")


def test_aggregate_preflight_passes_and_preserves_none_false(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_success(monkeypatch)
    payload = preflight.collect(_args(tmp_path))
    assert payload["status"] == "PASS"
    assert payload["execution_capability"] == "NONE"
    assert payload["order_execution_enabled"] is False
    assert len(payload["checks"]) == 52
    assert {item["check"] for item in payload["checks"]} == set(
        preflight.CHECK_FAILURE_CODES
    )
    assert {item["dimension"] for item in payload["checks"]} >= {
        "HOST", "POWERSHELL", "GIT", "FILESYSTEM", "PYTHON",
        "IMPORT", "NETWORK", "CREDENTIAL", "EVIDENCE", "SAFETY",
    }
    windows_status = next(
        item for item in payload["checks"] if item["check"] == "WINDOWS_IDENTITY"
    )["status"]
    expected_windows_status = (
        "PASS" if preflight.platform.system() == "Windows" else "NOT_REQUIRED"
    )
    assert windows_status == expected_windows_status
    assert payload["linux_worker"] == "NOT_REQUIRED_FOR_REAL_HOST"
    assert payload["failure_phase"] == "NONE"
    assert payload["failure_dimensions"] == []
    provider = next(
        item for item in payload["checks"] if item["check"] == "IG_PROVIDER_HEALTH"
    )
    assert provider["status"] == "UNKNOWN"
    assert provider["required"] is False


def test_import_origin_mismatch_is_detected_for_daxlab_and_collector(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    matrix = preflight.Matrix()

    class ShadowedModule:
        __file__ = str(tmp_path / "shadow" / "module.py")

    monkeypatch.setattr(preflight.importlib, "import_module", lambda _: ShadowedModule())
    preflight._project_import_checks(matrix, ROOT)
    statuses = {item.check: item for item in matrix.checks}
    assert statuses["IMPORT_DAXLAB_ORIGIN"].status == "FAIL"
    assert statuses["IMPORT_DAXLAB_ORIGIN"].reason_code == "IMPORT_DAXLAB_ORIGIN_MISMATCH"
    assert statuses["IMPORT_COLLECTOR_ORIGIN"].status == "FAIL"
    assert statuses["IMPORT_COLLECTOR_ORIGIN"].reason_code == "IMPORT_COLLECTOR_ORIGIN_MISMATCH"


def test_exact_local_clone_origin_is_accepted_without_exposing_path(tmp_path: Path) -> None:
    source = tmp_path / "source repo"
    source.mkdir()
    other = tmp_path / "other"
    other.mkdir()
    assert preflight._origin_matches(str(source), source, ()) is True
    assert preflight._origin_matches(str(other), source, ()) is False


@pytest.mark.parametrize("check_id,error_code", sorted(preflight.CHECK_FAILURE_CODES.items()))
def test_every_expected_failure_has_a_stable_code(check_id: str, error_code: str) -> None:
    matrix = preflight.Matrix()
    matrix.run("INJECTED", check_id, "PASS", lambda: (_ for _ in ()).throw(OSError("secret")))
    assert matrix.checks == [preflight.Check(
        dimension="INJECTED", check=check_id, status="FAIL", reason_code=error_code,
        observed_contract="EXCEPTION", required_contract="PASS", required=True,
        exception_class="OSError",
    )]
    assert "secret" not in repr(matrix.checks)


def test_required_failure_scenarios_all_map_to_documented_fixed_codes() -> None:
    sources = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            ROOT / "scripts/dax_windows_host_preflight.py",
            ROOT / "scripts/dax_windows_host_lane.psm1",
            ROOT / "scripts/run_ig_predemo_readiness_2238.ps1",
            ROOT / "scripts/run_ig_predemo_readiness_2238.py",
        )
    )
    assert len(FAILURE_SCENARIOS) == 39
    for code in FAILURE_SCENARIOS.values():
        assert code in sources


def test_architecture_and_git_failures_aggregate(tmp_path: Path, monkeypatch) -> None:
    _patch_success(monkeypatch)
    args = _args(tmp_path)
    args.powershell_architecture = "32_BIT" if preflight.struct.calcsize("P") == 8 else "64_BIT"
    args.git_clone = "FAIL"
    args.git_checkout = "FAIL"
    payload = preflight.collect(args)
    failures = {item["check"]: item["reason_code"] for item in payload["checks"]}
    assert failures["PYTHON_HOST_ARCHITECTURE"] == "PYTHON_HOST_ARCHITECTURE_MISMATCH"
    assert failures["GIT_CLONE"] == "GIT_CLONE_UNVERIFIED"
    assert failures["GIT_CHECKOUT"] == "GIT_CHECKOUT_UNVERIFIED"
    assert payload["failure_phase"] == "PREFLIGHT"
    assert payload["failure_dimensions"] == ["GIT", "PYTHON"]


def test_network_failures_aggregate_without_credential_or_login_side_effect(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_success(monkeypatch)
    monkeypatch.setattr(preflight, "_dns", lambda host: (_ for _ in ()).throw(OSError("secret dns")))
    monkeypatch.setattr(preflight, "_tls", lambda host: (_ for _ in ()).throw(TimeoutError("secret tls")))
    monkeypatch.setattr(preflight, "_https", lambda url: (_ for _ in ()).throw(OSError("secret https")))
    payload = preflight.collect(_args(tmp_path))
    failed = {item["check"]: item for item in payload["checks"] if item["status"] == "FAIL"}
    assert set(failed) >= {
        "NETWORK_GITHUB_DNS", "NETWORK_GITHUB_TLS", "NETWORK_GITHUB_HTTPS",
        "NETWORK_IG_DNS", "NETWORK_IG_TLS", "NETWORK_IG_HTTPS_TRANSPORT",
    }
    provider = next(
        item for item in payload["checks"] if item["check"] == "IG_PROVIDER_HEALTH"
    )
    assert provider["status"] == "BLOCKED"
    assert provider["required"] is False
    assert payload["status"] == "BLOCKED"
    assert "secret" not in json.dumps(payload)


def test_ig_http_5xx_proves_transport_but_not_provider_health(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_success(monkeypatch)
    monkeypatch.setattr(
        preflight, "_https",
        lambda url: "HTTP_5XX" if "demo-api.ig.com" in url else "HTTP_2XX",
    )
    payload = preflight.collect(_args(tmp_path))
    checks = {item["check"]: item for item in payload["checks"]}
    assert checks["NETWORK_IG_HTTPS_TRANSPORT"]["status"] == "PASS"
    assert checks["NETWORK_IG_HTTPS_TRANSPORT"]["observed_contract"] == "HTTP_5XX"
    assert checks["IG_PROVIDER_HEALTH"]["status"] == "UNKNOWN"
    assert checks["IG_PROVIDER_HEALTH"]["reason_code"] == (
        "IG_PROVIDER_HEALTH_NO_PUBLIC_ENDPOINT"
    )
    assert checks["IG_PROVIDER_HEALTH"]["required"] is False
    assert payload["status"] == "PASS"
    assert payload["failure_phase"] == "NONE"


def test_ig_http_without_response_is_network_failure_with_correct_phase(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_success(monkeypatch)

    def https(url: str) -> str:
        if "demo-api.ig.com" in url:
            raise TimeoutError("secret transport")
        return "HTTP_2XX"

    monkeypatch.setattr(preflight, "_https", https)
    payload = preflight.collect(_args(tmp_path))
    checks = {item["check"]: item for item in payload["checks"]}
    assert checks["NETWORK_IG_HTTPS_TRANSPORT"]["status"] == "FAIL"
    assert checks["NETWORK_IG_HTTPS_TRANSPORT"]["reason_code"] == (
        "NETWORK_IG_HTTPS_TRANSPORT_FAILED"
    )
    assert checks["IG_PROVIDER_HEALTH"]["status"] == "BLOCKED"
    assert payload["status"] == "BLOCKED"
    assert payload["failure_phase"] == "NETWORK"
    assert payload["failure_dimensions"] == ["NETWORK"]
    assert "secret" not in json.dumps(payload)


@pytest.mark.parametrize(
    "content,failed_check",
    [
        ("", "CREDENTIAL_SHAPE"),
        ("IG_USERNAME=x\nIG_PASSWORD=y\n", "CREDENTIAL_SHAPE"),
        ("IG_USERNAME=x\nBROKER_TOKEN=z\nIG_PASSWORD=y\nIG_API_KEY=k\n", "CREDENTIAL_SHAPE"),
        ("IG_USERNAME=x\nIG_USERNAME=y\nIG_PASSWORD=z\nIG_API_KEY=k\n", "CREDENTIAL_SHAPE"),
        ("malformed\n", "CREDENTIAL_SHAPE"),
    ],
)
def test_credential_shape_is_classified_without_values(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, content: str, failed_check: str
) -> None:
    _patch_success(monkeypatch)
    args = _args(tmp_path)
    args.credentials_file.write_text(content, encoding="utf-8")
    payload = preflight.collect(args)
    item = next(value for value in payload["checks"] if value["check"] == failed_check)
    assert item["status"] == "FAIL"
    assert item["reason_code"] == "CREDENTIAL_SHAPE_INVALID"
    assert all(value not in json.dumps(payload) for value in ("BROKER_TOKEN", "malformed"))


def test_missing_credentials_blocks_shape_but_other_checks_continue(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_success(monkeypatch)
    args = _args(tmp_path)
    args.credentials_file.unlink()
    payload = preflight.collect(args)
    statuses = {item["check"]: item["status"] for item in payload["checks"]}
    assert statuses["CREDENTIAL_FILE"] == "FAIL"
    assert statuses["CREDENTIAL_ENCODING"] == "BLOCKED"
    assert statuses["CREDENTIAL_SHAPE"] == "BLOCKED"
    assert statuses["NETWORK_IG_TLS"] == "PASS"


def test_existing_namespace_blocks_without_overwrite(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_success(monkeypatch)
    args = _args(tmp_path)
    (tmp_path / args.namespace).mkdir(parents=True)
    marker = tmp_path / args.namespace / "original.txt"
    marker.write_text("retain", encoding="utf-8")
    payload = preflight.collect(args)
    item = next(value for value in payload["checks"] if value["check"] == "NAMESPACE_AVAILABLE")
    assert item["status"] == "FAIL"
    assert marker.read_text(encoding="utf-8") == "retain"


def test_unavailable_runtime_root_blocks_filesystem_but_keeps_network_matrix(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_success(monkeypatch)
    args = _args(tmp_path)
    args.runtime_root = tmp_path / "missing"
    payload = preflight.collect(args)
    statuses = {item["check"]: item["status"] for item in payload["checks"]}
    assert statuses["RUNTIME_ROOT"] == "FAIL"
    assert statuses["FILESYSTEM_ATOMIC"] == "BLOCKED"
    assert statuses["NETWORK_GITHUB_HTTPS"] == "PASS"


def test_clock_abnormal_is_fixed_and_does_not_short_circuit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_success(monkeypatch)
    monkeypatch.setattr(preflight.time, "time", lambda: 1.0)
    payload = preflight.collect(_args(tmp_path))
    item = next(value for value in payload["checks"] if value["check"] == "HOST_UTC_CLOCK")
    assert item["status"] == "FAIL"
    assert item["reason_code"] == "HOST_CLOCK_ABNORMAL"
    assert any(value["check"] == "NETWORK_IG_TLS" for value in payload["checks"])


def test_publish_is_hash_bound_exclusive_and_readable(tmp_path: Path) -> None:
    payload = {
        "expected_head": "b" * 40,
        "status": "BLOCKED",
        "checks": [],
        "execution_capability": "NONE",
        "order_execution_enabled": False,
    }
    namespace, fingerprint = preflight.publish(tmp_path, payload)
    root = tmp_path / namespace
    manifest = json.loads((root / "MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["files"]["PREFLIGHT.json"] == fingerprint
    assert manifest["execution_capability"] == "NONE"
    assert manifest["order_execution_enabled"] is False
    assert b"\r\n" not in (root / "PREFLIGHT.json").read_bytes()


def test_publish_handles_spaces_and_non_ascii_runtime_path(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime space ü"
    runtime.mkdir()
    namespace, _ = preflight.publish(runtime, {
        "expected_head": "b" * 40, "status": "PASS", "checks": [],
        "execution_capability": "NONE", "order_execution_enabled": False,
    })
    assert (runtime / namespace / "PREFLIGHT.json").is_file()


def test_publication_failure_returns_fixed_safe_code(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _patch_success(monkeypatch)
    args = _args(tmp_path)
    monkeypatch.setattr(preflight, "collect", lambda _: {
        "expected_head": "a" * 40, "status": "PASS", "checks": [],
        "execution_capability": "NONE", "order_execution_enabled": False,
    })
    monkeypatch.setattr(preflight, "publish", lambda *_: (_ for _ in ()).throw(PermissionError("secret")))
    monkeypatch.setattr(preflight, "parser", lambda: type("P", (), {"parse_args": lambda self, argv: args})())
    assert preflight.main([]) == 2
    result = json.loads(capsys.readouterr().out)
    assert result["error_code"] == "EVIDENCE_PREFLIGHT_PUBLICATION_FAILED"
    assert result["failure_phase"] == "EVIDENCE"
    assert result["failure_dimensions"] == ["EVIDENCE"]
    assert result["publication_exception_class"] == "PermissionError"
    assert "secret" not in json.dumps(result)


def test_proxy_names_are_observed_without_values_or_false_block(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_success(monkeypatch)
    monkeypatch.setenv("HTTPS_PROXY", "http://user:secret@example.invalid")
    payload = preflight.collect(_args(tmp_path))
    item = next(value for value in payload["checks"] if value["check"] == "NETWORK_PROXY")
    assert item["status"] == "UNKNOWN"
    assert item["required"] is False
    assert "secret" not in json.dumps(payload)


def test_wrapper_orders_preflight_before_authenticated_collector() -> None:
    source = (ROOT / "scripts/run_ig_predemo_readiness_2238.ps1").read_text(encoding="utf-8")
    assert source.index("dax_windows_host_preflight.py") < source.index("AUTH READ-ONLY START")
    assert source.index("AUTH READ-ONLY START") < source.index("run_ig_predemo_readiness_2238.py")
    assert "Write-DaxHostPreflight" in source
    assert "$script:runnerPhase = $preflightPhase" in source
    assert "'NETWORK' { 'NETWORK_UNCLASSIFIED_FAILURE' }" in source
    assert "-I -S" not in source
    assert "execution disabled" in source
    assert "order_send" not in source and "/positions/otc" not in source
