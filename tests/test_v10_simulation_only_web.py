import json
from pathlib import Path


def test_paper_web_capability_is_simulation_only() -> None:
    root = Path(__file__).resolve().parents[1]
    paper = json.loads((root / "web/status.json").read_text())["paper_preparation"]
    assert paper["execution_capability"] == "SIMULATION_ONLY"
