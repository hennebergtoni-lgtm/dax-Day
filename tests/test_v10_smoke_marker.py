from pathlib import Path


def test_soak_smoke_labels_real_broker_evidence_absent() -> None:
    root = Path(__file__).resolve().parents[1]
    text = (root / "scripts/shadow_soak_smoke.py").read_text(encoding="utf-8")
    assert "Real MT5 broker evidence: NOT PRESENT" in text
    assert "Paper: NOT STARTED" in text
    assert "Live: NOT AUTHORIZED" in text
