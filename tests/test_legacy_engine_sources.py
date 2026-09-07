import hashlib

from daxlab.reference.legacy_loader import (
    CANDIDATE_SHA256,
    ORACLE_SHA256,
    candidate_source_bytes,
    load_candidate,
    load_oracle,
    oracle_source_bytes,
    verify_legacy_sources,
)


def test_exact_legacy_source_hashes_are_frozen() -> None:
    assert hashlib.sha256(oracle_source_bytes()).hexdigest() == ORACLE_SHA256
    assert hashlib.sha256(candidate_source_bytes()).hexdigest() == CANDIDATE_SHA256
    verify_legacy_sources()


def test_oracle_and_candidate_interfaces() -> None:
    oracle = load_oracle()
    candidate = load_candidate()
    common = ("grid", "daily_context", "backtest", "simulate_day", "metrics")
    for name in common:
        assert callable(getattr(oracle, name))
        assert callable(getattr(candidate, name))
    assert len(list(oracle.grid())) == 144
    assert len(list(candidate.grid())) == 144
    expected_costs = ["normal", "stress_1.5x", "stress_2x"]
    assert list(oracle.COST_SCENARIOS) == expected_costs
    assert list(candidate.COST_SCENARIOS) == expected_costs


def test_candidate_fast_interface_is_present() -> None:
    candidate = load_candidate()
    for name in ("build_fast_trade_cache", "cached_trades", "cached_metrics"):
        assert callable(getattr(candidate, name))
