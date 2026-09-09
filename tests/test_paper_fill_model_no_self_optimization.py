from pathlib import Path


def test_paper_fill_model_contains_no_optimizer_or_parameter_mutation_surface() -> None:
    root = Path(__file__).resolve().parents[1]
    text = (root / "src/daxlab/runtime/paper_contracts.py").read_text(encoding="utf-8").lower()
    for forbidden in ("optimize", "optimizer", "self_tune", "promote"):
        assert forbidden not in text
