from pathlib import Path


def test_paper_preparation_doc_forbids_credentials_and_account_identifiers() -> None:
    root = Path(__file__).resolve().parents[1]
    text = (root / "docs/PAPER_PREPARATION_V10.md").read_text(encoding="utf-8")
    assert "no credentials or account identifiers belong in these contracts" in text
