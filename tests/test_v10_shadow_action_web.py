import json
from pathlib import Path


def test_web_exposes_synthetic_shadow_as_no_order_only() -> None:
    root = Path(__file__).resolve().parents[1]
    soak = json.loads((root / "web/status.json").read_text())["synthetic_shadow_soak"]
    assert soak["action"] == "NO_ORDER_ONLY"
