from pathlib import Path


def test_v10_new_runtime_surfaces_do_not_reference_mt5_order_send() -> None:
    root = Path(__file__).resolve().parents[1]
    for relative in (
        "src/daxlab/runtime/shadow_soak.py",
        "src/daxlab/runtime/paper_contracts.py",
        "scripts/shadow_soak_smoke.py",
    ):
        text = (root / relative).read_text(encoding="utf-8")
        assert "order_send" not in text
        assert "order_check" not in text
