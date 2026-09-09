from pathlib import Path


def test_v10_scope_document_explicitly_excludes_live_and_broker_adapter() -> None:
    root = Path(__file__).resolve().parents[1]
    roadmap = (root / "docs/NEXT_50_MILESTONES_V10_161_210.md").read_text(encoding="utf-8")
    assert "does **not** authorize LIVE real-money execution" in roadmap
    assert "no broker adapter and no order submission function" in roadmap
