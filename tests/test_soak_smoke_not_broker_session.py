from pathlib import Path


def test_synthetic_soak_does_not_claim_broker_session_metadata() -> None:
    root = Path(__file__).resolve().parents[1]
    smoke = (root / "scripts/shadow_soak_smoke.py").read_text(encoding="utf-8")
    assert "broker_timezone" not in smoke
    assert "BROKER_OBSERVED" not in smoke
    assert "Real MT5 broker evidence: NOT PRESENT" in smoke
