from pathlib import Path


def test_paper_doc_keeps_historical_and_prospective_cost_evidence_separate() -> None:
    root = Path(__file__).resolve().parents[1]
    acceptance = (root / "docs/SHADOW_PAPER_ACCEPTANCE_V1.md").read_text(encoding="utf-8")
    assert "Historical research cost models remain separate evidence" in acceptance
