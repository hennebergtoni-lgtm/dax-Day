import pandas as pd
import pytest

from daxlab.research.fibonacci_bundle import build_fib001_trade_bundle


def _bars() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "datetime": pd.date_range("2026-01-05 08:00", periods=8, freq="5min", tz="UTC"),
            "open": [100, 101, 102, 103, 104, 105, 106, 107],
            "high": [102, 104, 106, 107, 108, 109, 110, 111],
            "low": [99, 100, 101, 102, 103, 104, 105, 106],
            "close": [101, 103, 105, 104, 105, 106, 107, 108],
        }
    )


def test_breakout_bundle_uses_signal_confirmation_before_entry():
    trades = pd.DataFrame(
        {
            "entry_time": [pd.Timestamp("2026-01-05 08:25", tz="UTC")],
            "signal_time": [pd.Timestamp("2026-01-05 08:20", tz="UTC")],
            "retest_time": [pd.NaT],
            "entry_mode": ["breakout"],
            "side": ["long"],
            "orb_min": [15],
        }
    )
    bundle = build_fib001_trade_bundle(_bars(), trades)

    assert len(bundle) == 1
    assert bundle.loc[0, "fib_anchor_start_price"] == 100.0
    assert bundle.loc[0, "fib_anchor_end_price"] == 106.0
    assert bundle.loc[0, "fib_observation_price"] == 105.0
    assert bundle.loc[0, "fib_observation_time"] < bundle.loc[0, "entry_time"]
    assert bundle.loc[0, "fib_retracement_depth"] == pytest.approx(1.0 / 6.0)
    assert bundle.loc[0, "fib_fixed_zone"] == "OUTSIDE_FIXED_ZONES"


def test_retest_bundle_requires_retest_time():
    trades = pd.DataFrame(
        {
            "entry_time": [pd.Timestamp("2026-01-05 08:25", tz="UTC")],
            "signal_time": [pd.Timestamp("2026-01-05 08:20", tz="UTC")],
            "retest_time": [pd.NaT],
            "entry_mode": ["retest"],
            "side": ["long"],
            "orb_min": [15],
        }
    )
    with pytest.raises(ValueError, match="observation time is missing"):
        build_fib001_trade_bundle(_bars(), trades)


def test_bundle_does_not_change_trade_count_or_trade_columns():
    trades = pd.DataFrame(
        {
            "trade_id": ["A"],
            "entry_time": [pd.Timestamp("2026-01-05 08:25", tz="UTC")],
            "signal_time": [pd.Timestamp("2026-01-05 08:20", tz="UTC")],
            "retest_time": [pd.NaT],
            "entry_mode": ["breakout"],
            "side": ["long"],
            "orb_min": [15],
        }
    )
    original = trades.copy(deep=True)
    bundle = build_fib001_trade_bundle(_bars(), trades)

    assert len(bundle) == len(trades)
    pd.testing.assert_frame_equal(trades, original)
    assert bundle.loc[0, "trade_id"] == "A"
