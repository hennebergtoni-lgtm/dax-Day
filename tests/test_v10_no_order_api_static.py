from pathlib import Path


def test_v10_soak_and_paper_contracts_have_no_broker_order_api() -> None:
    root = Path(__file__).resolve().parents[1]
    paths = [
        root / "src/daxlab/runtime/shadow_soak.py",
        root / "src/daxlab/runtime/paper_contracts.py",
        root / "scripts/shadow_soak_smoke.py",
    ]
    forbidden = ("order_send", "order_check", "MetaTrader5", "mt5.login", "initialize(")
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text, f"forbidden broker execution surface {token!r} in {path.name}"
