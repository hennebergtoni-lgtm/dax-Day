import json
from pathlib import Path


def test_web_keeps_v112_active_reference_immutable() -> None:
    root = Path(__file__).resolve().parents[1]
    web = json.loads((root / "web/status.json").read_text())
    assert web["active_reference"] == {
        "experiment_id": "V112_REFERENCE_V1",
        "strategy": "V11.2",
        "immutable": True,
        "status": "ACTIVE_REFERENCE",
    }
