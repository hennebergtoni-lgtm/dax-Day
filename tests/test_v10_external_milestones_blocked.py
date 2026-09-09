from pathlib import Path


def test_v10_hard_review_keeps_external_mt5_milestones_incomplete() -> None:
    root = Path(__file__).resolve().parents[1]
    text = (root / "docs/V10_HARD_REVIEW.md").read_text(encoding="utf-8")
    assert "External milestones 102–110: NOT COMPLETE" in text
    assert "real Windows MT5 terminal" in text
    assert "Paper: NOT STARTED / BLOCKED" in text
    assert "Live: NOT AUTHORIZED / BLOCKED" in text
