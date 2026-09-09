from pathlib import Path


def test_paper_contracts_define_no_order_submission_methods() -> None:
    root = Path(__file__).resolve().parents[1]
    text = (root / "src/daxlab/runtime/paper_contracts.py").read_text(encoding="utf-8")
    for forbidden in ("def submit", "def send_order", "def place_order", "def execute_order"):
        assert forbidden not in text
