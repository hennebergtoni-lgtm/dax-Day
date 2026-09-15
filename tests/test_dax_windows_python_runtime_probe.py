from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "dax_windows_python_runtime_probe",
    ROOT / "scripts" / "dax_windows_python_runtime_probe.py",
)
assert SPEC and SPEC.loader
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)


def test_runtime_probe_proves_exact_project_identity() -> None:
    architecture = f"{struct.calcsize('P') * 8}_BIT"
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "dax_windows_python_runtime_probe.py"),
            "--deployment-root",
            str(ROOT),
            "--powershell-architecture",
            architecture,
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    result = json.loads(completed.stdout)
    assert result["status"] == "PASS"
    assert result["error_code"] == "NONE"
    assert result["project_origin"] == "EXACT_DEPLOYMENT_SRC"
    assert result["collector_origin"] == "EXACT_DEPLOYMENT_SCRIPT"
    assert result["executable_path"] == str(Path(sys.executable).resolve())
    assert len(result["identity_fingerprint"]) == 64
    assert result["execution_capability"] == "NONE"
    assert result["order_execution_enabled"] is False


def test_runtime_probe_rejects_architecture_mismatch_before_import() -> None:
    architecture = "32_BIT" if struct.calcsize("P") * 8 == 64 else "64_BIT"
    result = probe.probe(ROOT, architecture)
    assert result == {
        "schema": probe.SCHEMA,
        "status": "BLOCKED",
        "error_code": "PYTHON_CANDIDATE_ARCHITECTURE_MISMATCH",
        "execution_capability": "NONE",
        "order_execution_enabled": False,
    }
