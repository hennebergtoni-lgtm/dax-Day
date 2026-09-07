from daxlab.reference.recovered_engine import (
    load_exact_candidate_engine,
    load_oracle_engine,
)


def _assert_shared_reference_surface(engine):
    params = list(engine.grid())
    assert len(params) == 144
    assert set(engine.COST_SCENARIOS) == {"normal", "stress_1.5x", "stress_2x"}
    assert hasattr(engine, "simulate_day")
    assert hasattr(engine, "daily_context")


def test_oracle_engine_loads_with_reference_surface():
    oracle = load_oracle_engine()
    _assert_shared_reference_surface(oracle)
    # The frozen oracle predates the FAST cache API; do not retrofit semantics into it.
    assert not hasattr(oracle, "cached_metrics")


def test_exact_candidate_engine_loads_with_fast_reference_surface():
    candidate = load_exact_candidate_engine()
    _assert_shared_reference_surface(candidate)
    assert hasattr(candidate, "cached_metrics")
    assert hasattr(candidate, "cached_trades")
