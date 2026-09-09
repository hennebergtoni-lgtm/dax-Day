from pathlib import Path


def test_v10_pr_scope_requires_research_registry_integrity() -> None:
    root = Path(__file__).resolve().parents[1]
    text = (root / "docs/V10_PR_SCOPE.md").read_text(encoding="utf-8")
    assert "research registry and hypothesis ledger integrity clean" in text
