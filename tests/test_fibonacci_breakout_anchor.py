from datetime import datetime, timezone

import pandas as pd
import pytest

from daxlab.research.fibonacci_anchor import build_confirmed_breakout_anchor


def _long_bars() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "datetime": pd.date_range("2026-01-05 08:15", periods=6, freq="5min", tz="UTC"),
            "high": [111, 114, 116, 115, 999, 999],
            "low": [108, 110, 112, 111, -999, -999],
            "close": [110.5, 113, 115, 113, 500, 500],
        }
    )


def test_long_breakout_anchor_freezes_on_first_non_extension_bar():
    anchor = build_confirmed_breakout_anchor(
        _long_bars(),
        boundary_price=110.0,
        breakout_time=datetime(2026, 1, 5, 8, 15, tzinfo=timezone.utc),
        available_until=datetime(2026, 1, 5, 8, 35, tzinfo=timezone.utc),
        direction="long",
    )
    assert anchor.start_price == 110.0
    assert anchor.end_price == 116.0
    assert anchor.end_time == datetime(2026, 1, 5, 8, 25, tzinfo=timezone.utc)
    assert anchor.confirmation_time == datetime(2026, 1, 5, 8, 30, tzinfo=timezone.utc)


def test_future_pollution_after_freeze_cannot_change_anchor():
    bars = _long_bars()
    clean = build_confirmed_breakout_anchor(
        bars,
        boundary_price=110.0,
        breakout_time=datetime(2026, 1, 5, 8, 15, tzinfo=timezone.utc),
        available_until=datetime(2026, 1, 5, 8, 35, tzinfo=timezone.utc),
        direction="long",
    )
    polluted = bars.copy()
    polluted.loc[polluted["datetime"] >= pd.Timestamp("2026-01-05 08:35", tz="UTC"), "high"] = 999999
    observed = build_confirmed_breakout_anchor(
        polluted,
        boundary_price=110.0,
        breakout_time=datetime(2026, 1, 5, 8, 15, tzinfo=timezone.utc),
        available_until=datetime(2026, 1, 5, 8, 35, tzinfo=timezone.utc),
        direction="long",
    )
    assert observed == clean


def test_non_breakout_close_is_rejected():
    bars = _long_bars().copy()
    bars.loc[0, "close"] = 109.0
    with pytest.raises(ValueError, match="must close above boundary"):
        build_confirmed_breakout_anchor(
            bars,
            boundary_price=110.0,
            breakout_time=datetime(2026, 1, 5, 8, 15, tzinfo=timezone.utc),
            available_until=datetime(2026, 1, 5, 8, 35, tzinfo=timezone.utc),
            direction="long",
        )


def test_unfrozen_impulse_is_rejected_without_future_bars():
    bars = _long_bars().iloc[:3].copy()
    with pytest.raises(ValueError, match="not frozen before observation"):
        build_confirmed_breakout_anchor(
            bars,
            boundary_price=110.0,
            breakout_time=datetime(2026, 1, 5, 8, 15, tzinfo=timezone.utc),
            available_until=datetime(2026, 1, 5, 8, 30, tzinfo=timezone.utc),
            direction="long",
        )


def test_short_breakout_anchor_is_symmetric():
    bars = pd.DataFrame(
        {
            "datetime": pd.date_range("2026-01-05 08:15", periods=4, freq="5min", tz="UTC"),
            "high": [101, 99, 97, 98],
            "low": [98, 95, 92, 93],
            "close": [99, 96, 93, 95],
        }
    )
    anchor = build_confirmed_breakout_anchor(
        bars,
        boundary_price=100.0,
        breakout_time=datetime(2026, 1, 5, 8, 15, tzinfo=timezone.utc),
        available_until=datetime(2026, 1, 5, 8, 35, tzinfo=timezone.utc),
        direction="short",
    )
    assert anchor.start_price == 100.0
    assert anchor.end_price == 92.0
    assert anchor.confirmation_time == datetime(2026, 1, 5, 8, 30, tzinfo=timezone.utc)
