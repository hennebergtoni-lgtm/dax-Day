from pathlib import Path


def test_v10_pr_scope_document_is_present_and_nonempty() -> None:
    root = Path(__file__).resolve().parents[1]
    text = (root / "docs/V10_PR_SCOPE.md").read_text(encoding="utf-8")
    assert len(text) > 500
