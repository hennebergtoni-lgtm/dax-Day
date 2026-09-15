from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "src" / "daxlab" / "runtime"
AUDIT = ROOT / "docs" / "BROKER_NEUTRAL_PREAUTH_LEAN_AUDIT_V1.md"


def test_all_broker_runtime_owners_remain_submission_free() -> None:
    files = sorted(RUNTIME.glob("broker_*.py"))
    assert files, "expected broker-neutral runtime owners"
    for path in files:
        source = path.read_text(encoding="utf-8")
        assert "import MetaTrader5" not in source, path.name
        assert "from MetaTrader5" not in source, path.name
        assert "order_send(" not in source, path.name
        assert "execution_capability=\"BROKER\"" not in source, path.name
        assert "order_execution_enabled=True" not in source, path.name


def test_lean_audit_forbids_speculative_broker_stack() -> None:
    text = AUDIT.read_text(encoding="utf-8")
    assert "No additional broker-neutral execution orchestrator is justified" in text
    assert "Architectural symmetry is not sufficient justification" in text
    assert "MT5 order adapter" in text
    assert "generic broker execution service" in text
    assert "PAPER/demo broker execution not authorized" in text
