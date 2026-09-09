import json
from pathlib import Path


def test_v10_web_readiness_keeps_paper_and_live_blocked() -> None:
    root = Path(__file__).resolve().parents[1]
    readiness = json.loads((root / "web/status.json").read_text())["readiness"]
    assert readiness["paper"] == "BLOCKED"
    assert readiness["live"] == "BLOCKED"
