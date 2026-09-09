from daxlab.runtime.paper_contracts import PaperFillModelConfig


def test_default_paper_cost_assumptions_match_current_normal_model_values() -> None:
    model = PaperFillModelConfig()
    assert (model.spread_points, model.slippage_points, model.commission_points) == (
        0.20,
        0.10,
        0.10,
    )
    assert model.latency_ms == 250
