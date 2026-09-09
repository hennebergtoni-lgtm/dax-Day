import json
from pathlib import Path


def test_v10_web_retains_walk_forward_shape() -> None:
    root = Path(__file__).resolve().parents[1]
    wf = json.loads((root / "web/status.json").read_text())["walk_forward"]
    assert wf == {"train_days": 45, "oos_days": 20, "step_days": 20, "windows": 81}
