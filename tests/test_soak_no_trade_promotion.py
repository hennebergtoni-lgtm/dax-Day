from pathlib import Path


def test_soak_runtime_contains_no_research_promotion_surface() -> None:
    root = Path(__file__).resolve().parents[1]
    text = (root / "src/daxlab/runtime/shadow_soak.py").read_text(encoding="utf-8").lower()
    for forbidden in ("promote", "deployable", "atr001", "bb001", "research_family"):
        assert forbidden not in text
