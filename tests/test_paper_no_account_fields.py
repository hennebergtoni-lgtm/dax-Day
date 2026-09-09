from pathlib import Path


def test_paper_contract_source_has_no_account_or_credential_fields() -> None:
    root = Path(__file__).resolve().parents[1]
    text = (root / "src/daxlab/runtime/paper_contracts.py").read_text(encoding="utf-8").lower()
    for forbidden in ("password", "account_id", "email", "phone", "api_key", "secret"):
        assert forbidden not in text
