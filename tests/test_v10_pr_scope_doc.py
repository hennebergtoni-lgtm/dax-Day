from pathlib import Path


def test_v10_pr_scope_retains_non_live_boundaries() -> None:
    root = Path(__file__).resolve().parents[1]
    text = (root / "docs/V10_PR_SCOPE.md").read_text(encoding="utf-8")
    assert "synthetic evidence is not broker evidence" in text
    assert "real MT5 milestones 102–110 remain open" in text
    assert "Paper remains not started" in text
    assert "LIVE remains unauthorized" in text
    assert "V11.2 remains the immutable active reference" in text
