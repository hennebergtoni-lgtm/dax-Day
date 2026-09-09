from pathlib import Path


def test_v10_pr_scope_requires_full_ci_acceptance() -> None:
    root = Path(__file__).resolve().parents[1]
    text = (root / "docs/V10_PR_SCOPE.md").read_text(encoding="utf-8")
    assert "Ruff clean" in text
    assert "full pytest clean" in text
    assert "recovery reconstruction preflight clean" in text
