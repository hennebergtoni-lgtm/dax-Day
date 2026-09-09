from pathlib import Path


def test_v10_pr_scope_keeps_research_candidates_as_research() -> None:
    root = Path(__file__).resolve().parents[1]
    text = (root / "docs/V10_PR_SCOPE.md").read_text(encoding="utf-8")
    assert "research candidates remain research" in text
