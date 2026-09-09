import json
from pathlib import Path


def test_web_research_family_count_and_atr_status_remain_unchanged() -> None:
    root = Path(__file__).resolve().parents[1]
    web = json.loads((root / "web/status.json").read_text())
    assert web["research_families"]["count"] == 13
    items = {item["id"]: item for item in web["research_families"]["items"]}
    assert items["ATR001"]["status"] == "RESEARCH"
    assert items["ATR001"]["evidence_maturity"] == "OOS_TESTED"
