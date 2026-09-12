import json
from pathlib import Path


def test_static_web_retains_repository_recovery_state_only() -> None:
    root = Path(__file__).resolve().parents[1]
    web = json.loads((root / "web/status.json").read_text())
    recovery = web["recovery"]

    assert recovery["reconstruction_contract"] == "ACTIVE"
    assert recovery["persistent_bundle"] == "IMPLEMENTED"
    assert recovery["ci_recovery_preflight"] == "GATED_BY_CI"
    assert "mt5_host_evidence_manifest" not in recovery
    assert web["runtime_truth_included"] is False
