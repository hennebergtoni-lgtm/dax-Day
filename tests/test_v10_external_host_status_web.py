import json
from pathlib import Path


def test_web_external_host_state_remains_blocked() -> None:
    root = Path(__file__).resolve().parents[1]
    web = json.loads((root / "web/status.json").read_text())
    host = web["host_readiness"]
    assert host["state"] == "AWAITING_REAL_WINDOWS_HOST"
    assert host["real_host_evidence_present"] is False
    assert host["order_execution_enabled"] is False
