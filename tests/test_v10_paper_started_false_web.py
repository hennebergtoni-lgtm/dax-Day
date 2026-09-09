import json
from pathlib import Path


def test_paper_started_flag_is_false() -> None:
    root = Path(__file__).resolve().parents[1]
    paper = json.loads((root / "web/status.json").read_text())["paper_preparation"]
    assert paper["paper_started"] is False
