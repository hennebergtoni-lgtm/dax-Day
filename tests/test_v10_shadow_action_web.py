import json
from pathlib import Path


def test_static_web_does_not_publish_synthetic_shadow_runtime_state() -> None:
    root = Path(__file__).resolve().parents[1]
    web = json.loads((root / "web/status.json").read_text())

    assert "synthetic_shadow_soak" not in web
    assert web["runtime_truth_included"] is False
    assert web["historical_sequential_replay"]["action"] == "NO_ORDER_ONLY"
