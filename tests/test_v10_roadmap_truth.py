from pathlib import Path


def test_v10_roadmap_retains_real_host_and_live_blockers() -> None:
    root = Path(__file__).resolve().parents[1]
    text = (root / "docs/NEXT_50_MILESTONES_V10_161_210.md").read_text(encoding="utf-8")
    assert "SYNTHETIC_ONLY_NOT_BROKER_EVIDENCE" in text
    assert "Paper remains NOT STARTED" in text
    assert "LIVE remains NOT AUTHORIZED" in text
    assert "external MT5 milestones 102–110 remain incomplete" in text
    assert "V11.2 remains the immutable active reference" in text
