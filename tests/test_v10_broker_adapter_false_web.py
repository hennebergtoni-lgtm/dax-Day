import json
from pathlib import Path


def test_broker_adapter_present_flag_is_false() -> None:
    root = Path(__file__).resolve().parents[1]
    paper = json.loads((root / "web/status.json").read_text())["paper_preparation"]
    assert paper["broker_adapter_present"] is False
