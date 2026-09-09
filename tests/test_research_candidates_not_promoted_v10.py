import json
from pathlib import Path


def test_v10_does_not_silently_promote_research_candidates() -> None:
    root = Path(__file__).resolve().parents[1]
    registry = json.loads((root / "research/RESEARCH_FAMILY_REGISTRY_V1.json").read_text())
    states = {item["id"]: item["status"] for item in registry["families"]}
    assert states["ATR001"] == "RESEARCH"
    for family in (
        "BB001",
        "FIB001",
        "GAP001",
        "BOOST001",
        "LIQ001",
        "STRUCT001",
        "MOM001",
        "SESSION001",
        "ENTRY001",
        "EXIT001",
        "TWAP001",
    ):
        assert states[family] == "RESEARCH"
