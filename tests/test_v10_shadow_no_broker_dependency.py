from pathlib import Path


def test_shadow_soak_module_has_no_metatrader_dependency() -> None:
    root = Path(__file__).resolve().parents[1]
    text = (root / "src/daxlab/runtime/shadow_soak.py").read_text(encoding="utf-8")
    assert "import MetaTrader5" not in text
    assert "from MetaTrader5" not in text
