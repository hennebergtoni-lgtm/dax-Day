import json
from pathlib import Path


def test_web_retains_credential_free_mt5_recovery_manifest_state() -> None:
    root = Path(__file__).resolve().parents[1]
    recovery = json.loads((root / "web/status.json").read_text())["recovery"]
    assert recovery["reconstruction_contract"] == "ACTIVE"
    assert recovery["mt5_host_evidence_manifest"] == "IMPLEMENTED_CREDENTIAL_FREE"
