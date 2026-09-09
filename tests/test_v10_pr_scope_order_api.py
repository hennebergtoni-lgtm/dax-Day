from pathlib import Path


def test_v10_pr_scope_keeps_order_submission_absent() -> None:
    root = Path(__file__).resolve().parents[1]
    text = (root / "docs/V10_PR_SCOPE.md").read_text(encoding="utf-8")
    assert "no broker adapter or order submission function exists" in text
