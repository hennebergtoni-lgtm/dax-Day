from pathlib import Path


def test_hard_review_records_all_retained_blockers() -> None:
    root = Path(__file__).resolve().parents[1]
    text = (root / "docs/V10_HARD_REVIEW.md").read_text(encoding="utf-8")
    for required in (
        "Paper: NOT STARTED / BLOCKED",
        "Live: NOT AUTHORIZED / BLOCKED",
        "External milestones 102–110: NOT COMPLETE",
        "V11.2: unchanged frozen active reference",
        "Research candidates: not promoted",
    ):
        assert required in text
