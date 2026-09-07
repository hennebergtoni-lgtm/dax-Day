from daxlab.reference.recovered_engine import (
    load_exact_candidate_engine,
    load_oracle_engine,
)


def _assert_reference_surface(engine):
    params = list(engine.grid())
    assert len(params) == 144
    assert set(engine.COST_SCENARIOS) == {"normal", "stress_1.5x", "stress_2x"}
    assert hasattr(engine, "simulate_day")
    assert hasattr(engine, "daily_context")
    assert hasattr(engine, "cached_metrics")


def test_oracle_engine_loads_with_reference_surface():
    _assert_reference_surface(load_oracle_engine())


def test_exact_candidate_engine_loads_with_reference_surface():
    _assert_reference_surface(load_exact_candidate_engine())
