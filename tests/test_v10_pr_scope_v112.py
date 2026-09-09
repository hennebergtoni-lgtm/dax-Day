from pathlib import Path


def test_v10_pr_scope_requires_v112_probe_and_replay_smoke() -> None:
    root = Path(__file__).resolve().parents[1]
    text = (root / "docs/V10_PR_SCOPE.md").read_text(encoding="utf-8")
    assert "frozen V11.2 engine probe and guarded replay smoke clean" in text
