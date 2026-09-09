from pathlib import Path


def test_paper_preparation_doc_retains_hard_boundary() -> None:
    root = Path(__file__).resolve().parents[1]
    text = (root / "docs/PAPER_PREPARATION_V10.md").read_text(encoding="utf-8")
    assert "PAPER NOT STARTED" in text
    assert "no MetaTrader order API is present" in text
    assert "no broker adapter is present" in text
    assert "LIVE remains NOT AUTHORIZED" in text
