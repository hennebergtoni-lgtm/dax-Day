from pathlib import Path


def test_v10_pr_scope_safety_boundary_is_explicit() -> None:
    root = Path(__file__).resolve().parents[1]
    text = (root / "docs/V10_PR_SCOPE.md").read_text(encoding="utf-8")
    assert "Non-negotiable boundaries" in text
    assert "no broker adapter or order submission function exists" in text
