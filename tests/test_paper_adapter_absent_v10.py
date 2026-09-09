from pathlib import Path


def test_v10_paper_preparation_has_no_broker_adapter_module() -> None:
    root = Path(__file__).resolve().parents[1]
    runtime = root / "src/daxlab/runtime"
    assert not (runtime / "paper_broker_adapter.py").exists()
    assert not (runtime / "live_execution.py").exists()
