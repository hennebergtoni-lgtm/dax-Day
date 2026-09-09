import json
from pathlib import Path


def test_web_soak_marker_and_no_order_action_are_explicit() -> None:
    root = Path(__file__).resolve().parents[1]
    soak = json.loads((root / "web/status.json").read_text())["synthetic_shadow_soak"]
    assert soak["evidence_state"] == "SYNTHETIC_ONLY_NOT_BROKER_EVIDENCE"
    assert soak["action"] == "NO_ORDER_ONLY"
    assert soak["order_execution_enabled"] is False
