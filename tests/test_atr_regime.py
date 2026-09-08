from datetime import datetime, timedelta, timezone

import pandas as pd
import pytest

from daxlab.research.atr_regime import (
    AtrObservation,
    atr_before_entry,
    build_or_atr_feature,
    true_range,
    wilder_atr,
)


def _bars(count: int = 24) -> pd.DataFrame:
    start = datetime(2026, 9, 8, 7, 0, tzinfo=timezone.utc)
    rows = []
    close = 100.0
    for i in range(count):
        open_ = close
        close = open_ + (0.5 if i % 2 == 0 else -0.2)
        rows.append(
            {
                "datetime": start + timedelta(minutes=5 * i),
                "open": open_,
                "high": max(open_, close) + 1.0,
                "low": min(open_, close) - 1.0,
                "close": close,
            }
        )
    return pd.DataFrame(rows)


def test_true_range_uses_previous_close_gap():
    bars = pd.DataFrame(
        [
            {"high": 101.0, "low": 99.0, "close": 100.0},
            {"high": 106.0, "low": 104.0, "close": 105.0},
        ]
    )
    tr = true_range(bars)
    assert tr.iloc[0] == pytest.approx(2.0)
    assert tr.iloc[1] == pytest.approx(6.0)


def test_wilder_atr_requires_full_period():
    bars = _bars(14)
    atr = wilder_atr(bars, 14)
    assert atr.iloc[:13].isna().all()
    assert atr.iloc[13] > 0


def test_atr_observation_is_strictly_before_entry():
    bars = _bars()
    entry = bars.iloc[20]["datetime"]
    obs = atr_before_entry(bars, entry_time=entry, period=14)
    assert obs.observation_time < entry
    assert obs.observation_time == bars.iloc[19]["datetime"]


def test_future_pollution_does_not_change_pre_entry_atr():
    bars = _bars()
    entry = bars.iloc[20]["datetime"]
    before = atr_before_entry(bars, entry_time=entry, period=14)
    polluted = bars.copy()
    polluted.loc[polluted.index >= 20, ["high", "low", "close"]] = [9999.0, 1.0, 5000.0]
    after = atr_before_entry(polluted, entry_time=entry, period=14)
    assert after.atr_points == pytest.approx(before.atr_points)
    assert after.observation_time == before.observation_time


def test_duplicate_or_out_of_order_bars_fail_closed():
    bars = _bars()
    entry = bars.iloc[20]["datetime"]
    duplicate = pd.concat([bars.iloc[:5], bars.iloc[[4]], bars.iloc[5:]], ignore_index=True)
    with pytest.raises(ValueError, match="unique and ordered"):
        atr_before_entry(duplicate, entry_time=entry)
    reversed_bars = bars.iloc[::-1].reset_index(drop=True)
    with pytest.raises(ValueError, match="unique and ordered"):
        atr_before_entry(reversed_bars, entry_time=entry)


def test_insufficient_history_fails_closed():
    bars = _bars(10)
    entry = bars.iloc[-1]["datetime"] + timedelta(minutes=5)
    with pytest.raises(ValueError, match="insufficient"):
        atr_before_entry(bars, entry_time=entry, period=14)


def test_or_atr_feature_requires_completed_or_and_positive_ranges():
    entry = datetime(2026, 9, 8, 9, 30, tzinfo=timezone.utc)
    atr = AtrObservation(atr_points=10.0, observation_time=entry - timedelta(minutes=5), period=14)
    feature = build_or_atr_feature(
        or_high=110.0,
        or_low=105.0,
        or_confirmation_time=entry - timedelta(minutes=10),
        atr=atr,
        entry_time=entry,
    )
    assert feature.ratio == pytest.approx(0.5)
    with pytest.raises(ValueError, match="complete before entry"):
        build_or_atr_feature(
            or_high=110.0,
            or_low=105.0,
            or_confirmation_time=entry,
            atr=atr,
            entry_time=entry,
        )
    with pytest.raises(ValueError, match="opening range"):
        build_or_atr_feature(
            or_high=105.0,
            or_low=105.0,
            or_confirmation_time=entry - timedelta(minutes=10),
            atr=atr,
            entry_time=entry,
        )
