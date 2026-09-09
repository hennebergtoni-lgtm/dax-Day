from pathlib import Path


def test_soak_runtime_does_not_contain_real_host_evidence_claim() -> None:
    root = Path(__file__).resolve().parents[1]
    text = (root / "src/daxlab/runtime/shadow_soak.py").read_text(encoding="utf-8")
    assert "REAL_HOST_EVIDENCE" not in text
    assert "SYNTHETIC_ONLY_NOT_BROKER_EVIDENCE" in text
