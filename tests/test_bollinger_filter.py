import pandas as pd
import pytest

from daxlab.research.bollinger_filter import (
    BollingerConfig,
    add_bollinger_state,
    align_last_completed_state,
    classify_htf_regime,
    filter_trades,
    prior_range_atr,
    resample_completed_htf,
    train_quantile,
)


def test_bollinger_uses_population_std_and_expected_position():
    bars = pd.DataFrame({"datetime": pd.date_range("2026-01-01 09:00", periods=4, freq="5min"), "close": [10.0, 11.0, 12.0, 13.0]})
    out = add_bollinger_state(bars, window=4, std_mult=2.0)
    row = out.iloc[-1]
    assert row.bb_mid == pytest.approx(11.5)
    assert row.bb_std == pytest.approx(1.11803398875)
    assert row.bb_position > 0.5


def test_entry_alignment_is_strictly_prior_not_same_bar():
    state = pd.DataFrame({"datetime": pd.to_datetime(["2026-01-01 09:00", "2026-01-01 09:05", "2026-01-01 09:10"]), "bb_bandwidth": [1.0, 2.0, 99.0]})
    entries = pd.DataFrame({"entry_time": pd.to_datetime(["2026-01-01 09:10"])})
    out = align_last_completed_state(entries, state)
    assert out.iloc[0].datetime == pd.Timestamp("2026-01-01 09:05")
    assert out.iloc[0].bb_bandwidth == 2.0


def test_train_quantile_rejects_bad_q_and_ignores_nan():
    s = pd.Series([1.0, 2.0, 3.0, None])
    assert train_quantile(s, 0.5) == pytest.approx(2.0)
    with pytest.raises(ValueError):
        train_quantile(s, 1.1)


def test_prior_range_atr_uses_only_prior_days():
    daily = pd.DataFrame({"date": pd.date_range("2026-01-01", periods=5), "high": [10, 20, 30, 40, 50], "low": [0, 0, 0, 0, 0]})
    out = prior_range_atr(daily, atr_days=2)
    assert out.iloc[3].prev_range == 30
    assert out.iloc[3].atr == pytest.approx(25)
    assert out.iloc[3].prev_range_atr == pytest.approx(1.2)


def test_completed_htf_state_is_timestamped_when_bar_is_known():
    bars = pd.DataFrame({"datetime": pd.date_range("2026-01-01 09:00", periods=12, freq="5min"), "close": list(range(12))})
    out = resample_completed_htf(bars, minutes=15, window=2)
    assert out.iloc[0].datetime == pd.Timestamp("2026-01-01 09:15")
    assert out.iloc[1].datetime == pd.Timestamp("2026-01-01 09:30")


def test_htf_regime_requires_persistence_and_handles_mean():
    htf = pd.DataFrame({"close": [10, 11, 12, 11, 10, 9], "bb_mid": [9, 10, 11, 11, 11, 10]})
    out = classify_htf_regime(htf, lookback=2)
    assert out.iloc[1] == "long_breakout"
    assert out.iloc[3] == "mean"
    assert out.iloc[5] == "short_breakout"


def test_filter_is_modular_and_can_be_disabled():
    trades = pd.DataFrame({"bb_position": [0.8, 0.6, 0.9], "bb_bandwidth": [0.02, 0.03, 0.01], "prev_range_atr": [1.0, 1.0, 2.0]})
    cfg = BollingerConfig(min_position=0.75)
    mask = filter_trades(trades, config=cfg, bandwidth_threshold=0.015, prior_range_atr_cap=1.5)
    assert mask.tolist() == [True, False, False]
    off = filter_trades(trades, config=BollingerConfig())
    assert off.tolist() == [True, True, True]
