from pathlib import Path


def test_v10_pr_scope_requires_3090_bar_soak_smoke() -> None:
    root = Path(__file__).resolve().parents[1]
    text = (root / "docs/V10_PR_SCOPE.md").read_text(encoding="utf-8")
    assert "3,090-bar synthetic SHADOW soak smoke clean" in text
