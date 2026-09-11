import pandas as pd

from daxlab.reference.recovered_engine import (
    load_exact_candidate_engine,
    load_oracle_engine,
)


_PARAM_FIELDS = (
    "orb_min",
    "entry_mode",
    "stop_mode",
    "rr",
    "direction",
    "prev_filter",
    "or_atr_filter",
    "or_range_filter",
    "cpr_filter",
    "skip_macro",
)
_COSTS = {"spread": 0.2, "slippage": 0.1, "commission": 0.1}


def _normalized_grid(engine: object) -> list[tuple[object, ...]]:
    return [tuple(getattr(params, field) for field in _PARAM_FIELDS) for params in engine.grid()]


def _no_trade_day() -> pd.DataFrame:
    times = ["09:00", "09:05", "09:10", "09:15"]
    return pd.DataFrame(
        {
            "date": ["2026-09-11"] * 4,
            "time": times,
            "datetime": pd.to_datetime([f"2026-09-11 {value}" for value in times]),
            "open": [100.0, 100.5, 101.5, 103.0],
            "high": [101.0, 102.0, 104.0, 103.5],
            "low": [99.0, 100.5, 101.0, 102.5],
            "close": [100.0, 101.5, 103.0, 103.0],
        }
    )


def _directional_day(*, bullish: bool) -> pd.DataFrame:
    datetimes = pd.date_range("2026-09-11 09:00", periods=103, freq="5min")
    if bullish:
        high = [101.0] + [120.0] * 102
        low = [99.0] + [100.0] * 102
        close = [100.0] + [110.0] * 102
    else:
        high = [101.0] + [100.0] * 102
        low = [99.0] + [80.0] * 102
        close = [100.0] + [90.0] * 102
    return pd.DataFrame(
        {
            "date": ["2026-09-11"] * 103,
            "time": datetimes.strftime("%H:%M"),
            "datetime": datetimes,
            "open": [100.0] * 103,
            "high": high,
            "low": low,
            "close": close,
        }
    )


def test_oracle_and_exact_candidate_have_identical_144_variant_grid() -> None:
    oracle = load_oracle_engine()
    exact = load_exact_candidate_engine()

    oracle_grid = _normalized_grid(oracle)
    exact_grid = _normalized_grid(exact)

    assert len(oracle_grid) == 144
    assert len(exact_grid) == 144
    assert oracle_grid == exact_grid


def test_oracle_and_exact_candidate_match_on_no_trade_case() -> None:
    oracle = load_oracle_engine()
    exact = load_exact_candidate_engine()
    oracle_params = list(oracle.grid())[0]
    exact_params = list(exact.grid())[0]
    context = {"prev_range": 200.0, "atr": 50.0, "cpr_width": 50.0}
    day = _no_trade_day()

    oracle_result = oracle.simulate_day(day.copy(), oracle_params, context, _COSTS)
    exact_result = exact.simulate_day(day.copy(), exact_params, context, _COSTS)

    assert oracle_result == []
    assert exact_result == []
    assert oracle_result == exact_result


def test_oracle_and_exact_candidate_match_on_positive_trade_paths() -> None:
    oracle = load_oracle_engine()
    exact = load_exact_candidate_engine()
    oracle_grid = list(oracle.grid())
    exact_grid = list(exact.grid())
    context = {"prev_range": 500.0, "atr": 10.0, "cpr_width": 50.0}

    nonempty_cases = 0
    mismatches = 0
    for day in (_directional_day(bullish=True), _directional_day(bullish=False)):
        for oracle_params, exact_params in zip(oracle_grid, exact_grid, strict=True):
            oracle_result = oracle.simulate_day(day.copy(), oracle_params, context, _COSTS)
            exact_result = exact.simulate_day(day.copy(), exact_params, context, _COSTS)
            if oracle_result or exact_result:
                nonempty_cases += 1
            if oracle_result != exact_result:
                mismatches += 1

    assert nonempty_cases == 144
    assert mismatches == 0
