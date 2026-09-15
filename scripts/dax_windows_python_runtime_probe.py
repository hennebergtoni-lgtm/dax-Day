"""Credential-free identity and project-parity probe for one Python runtime."""
from __future__ import annotations

import argparse
from hashlib import sha256
import importlib
import json
from pathlib import Path
import platform
import struct
import sys
from typing import Iterable


SCHEMA = "DAX_WINDOWS_PYTHON_RUNTIME_IDENTITY_V1"


def _blocked(code: str) -> dict[str, object]:
    return {
        "schema": SCHEMA,
        "status": "BLOCKED",
        "error_code": code,
        "execution_capability": "NONE",
        "order_execution_enabled": False,
    }


def probe(deployment_root: Path, powershell_architecture: str) -> dict[str, object]:
    if platform.python_implementation() != "CPython" or sys.version_info < (3, 11):
        return _blocked("PYTHON_CANDIDATE_VERSION_UNSUPPORTED")
    architecture = f"{struct.calcsize('P') * 8}_BIT"
    if architecture != powershell_architecture:
        return _blocked("PYTHON_CANDIDATE_ARCHITECTURE_MISMATCH")
    try:
        executable = Path(sys.executable).resolve(strict=True)
        root = deployment_root.resolve(strict=True)
        source_root = (root / "src").resolve(strict=True)
        scripts_root = (root / "scripts").resolve(strict=True)
        collector_path = (scripts_root / "run_ig_predemo_readiness_2238.py").resolve(strict=True)
        compile(collector_path.read_text(encoding="utf-8"), str(collector_path), "exec")
    except Exception:
        return _blocked("PYTHON_CANDIDATE_IDENTITY_INVALID")

    sys.path[:0] = [str(source_root), str(scripts_root)]
    try:
        daxlab = importlib.import_module("daxlab.adapters.ig_market_data")
        collector = importlib.import_module("run_ig_predemo_readiness_2238")
        daxlab_origin = Path(daxlab.__file__).resolve(strict=True)
        collector_origin = Path(collector.__file__).resolve(strict=True)
    except Exception:
        return _blocked("PYTHON_CANDIDATE_IMPORT_FAILED")
    try:
        if not daxlab_origin.is_relative_to(source_root) or collector_origin != collector_path:
            return _blocked("PYTHON_CANDIDATE_IMPORT_ORIGIN_MISMATCH")
    except Exception:
        return _blocked("PYTHON_CANDIDATE_IMPORT_ORIGIN_MISMATCH")

    version = platform.python_version()
    path_fingerprint = sha256(str(executable).casefold().encode("utf-8")).hexdigest()
    identity = "|".join((str(executable).casefold(), version, architecture,
                         str(source_root).casefold(), str(collector_path).casefold()))
    return {
        "schema": SCHEMA,
        "status": "PASS",
        "error_code": "NONE",
        "executable_path": str(executable),
        "executable_basename": executable.name,
        "executable_path_fingerprint": path_fingerprint,
        "identity_fingerprint": sha256(identity.encode("utf-8")).hexdigest(),
        "version": version,
        "architecture": architecture,
        "project_origin": "EXACT_DEPLOYMENT_SRC",
        "collector_origin": "EXACT_DEPLOYMENT_SCRIPT",
        "execution_capability": "NONE",
        "order_execution_enabled": False,
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--deployment-root", required=True, type=Path)
    result.add_argument(
        "--powershell-architecture", required=True, choices=("32_BIT", "64_BIT")
    )
    return result


def main(argv: Iterable[str] | None = None) -> int:
    try:
        args = parser().parse_args(argv)
        result = probe(args.deployment_root, args.powershell_architecture)
    except Exception:
        result = _blocked("PYTHON_CANDIDATE_PROBE_INTERNAL_FAILURE")
    print(json.dumps(result, sort_keys=True, ensure_ascii=True))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
