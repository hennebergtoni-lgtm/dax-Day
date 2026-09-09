from pathlib import Path


def test_v10_pr_scope_keeps_paper_not_started() -> None:
    root = Path(__file__).resolve().parents[1]
    text = (root / "docs/V10_PR_SCOPE.md").read_text(encoding="utf-8")
    assert "Paper remains not started" in text
