from pathlib import Path


def test_next_50_authorization_is_documented_as_non_live_only() -> None:
    root = Path(__file__).resolve().parents[1]
    roadmap = (root / "docs/NEXT_50_MILESTONES_V10_161_210.md").read_text(encoding="utf-8")
    assert "AUTHORIZED FOR NON-LIVE DEVELOPMENT" in roadmap
    assert "does **not** authorize LIVE real-money execution" in roadmap
