from pathlib import Path


def test_soak_implementation_embeds_synthetic_only_marker() -> None:
    root = Path(__file__).resolve().parents[1]
    text = (root / "src/daxlab/runtime/shadow_soak.py").read_text(encoding="utf-8")
    assert "SYNTHETIC_ONLY_NOT_BROKER_EVIDENCE" in text
