from daxlab.runtime.paper_contracts import PaperFillModelConfig


def test_fill_model_fingerprint_changes_only_when_model_changes() -> None:
    first = PaperFillModelConfig()
    second = PaperFillModelConfig()
    changed = PaperFillModelConfig(slippage_points=0.2)
    assert first.fingerprint == second.fingerprint
    assert first.fingerprint != changed.fingerprint
