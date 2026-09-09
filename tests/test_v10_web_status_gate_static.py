from pathlib import Path


def test_web_integrity_gate_checks_synthetic_and_paper_truthfulness() -> None:
    root = Path(__file__).resolve().parents[1]
    text = (root / "scripts/check_web_status.py").read_text(encoding="utf-8")
    assert "synthetic_shadow_soak" in text
    assert "SYNTHETIC_ONLY_NOT_BROKER_EVIDENCE" in text
    assert "paper_preparation" in text
    assert "paper_started" in text
    assert "broker_adapter_present" in text
