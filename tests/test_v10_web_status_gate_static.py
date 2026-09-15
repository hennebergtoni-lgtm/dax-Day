from pathlib import Path


def test_web_integrity_gate_enforces_static_runtime_boundary_and_paper_block() -> None:
    root = Path(__file__).resolve().parents[1]
    text = (root / "scripts/check_web_status.py").read_text(encoding="utf-8")

    assert "_FORBIDDEN_DYNAMIC_SECTIONS" in text
    assert '"mt5_adapter"' in text
    assert '"host_readiness"' in text
    assert '"pre_host_gate"' in text
    assert '"synthetic_shadow_soak"' in text
    assert "runtime_truth_included" in text
    assert "paper_preparation" in text
    assert "paper_started" in text
    assert "broker_adapter_present" in text
    assert "Paper/Live BLOCKED" in text
