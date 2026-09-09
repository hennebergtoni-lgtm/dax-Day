from pathlib import Path


def test_v10_has_no_live_execution_module_or_script() -> None:
    root = Path(__file__).resolve().parents[1]
    assert not (root / "src/daxlab/runtime/live_execution.py").exists()
    assert not (root / "scripts/live_trading.py").exists()
