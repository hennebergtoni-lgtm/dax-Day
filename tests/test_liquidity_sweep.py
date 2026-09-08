import pandas as pd

from daxlab.research.liquidity_sweep import LevelKind, confirmed_levels, wick_rejection_sweeps


def _frame(values):
    rows = []
    for i, (high, low, close) in enumerate(values):
        rows.append(
            {
                "datetime": pd.Timestamp("2026-01-01T09:00:00Z") + pd.Timedelta(minutes=5 * i),
                "high": high,
                "low": low,
                "close": close,
            }
        )
    return pd.DataFrame(rows)


def test_level_is_not_known_before_confirmation_bar():
    frame = _frame(
        [
            (10, 7, 9),
            (11, 8, 10),
            (15, 9, 12),
            (12, 8, 10),
            (11, 7, 9),
        ]
    )
    levels = confirmed_levels(frame, half_window=2)
    high = next(level for level in levels if level.kind is LevelKind.HIGH)
    assert high.pivot_index == 2
    assert high.confirmed_index == 4
    assert high.confirmed_time == frame.iloc[4]["datetime"]


def test_prefix_property_for_confirmed_levels():
    full = _frame(
        [
            (10, 7, 9),
            (11, 8, 10),
            (15, 9, 12),
            (12, 8, 10),
            (11, 7, 9),
            (14, 8, 13),
            (16, 10, 15),
        ]
    )
    prefix = full.iloc[:5].copy()
    prefix_levels = confirmed_levels(prefix, half_window=2)
    full_levels = [level for level in confirmed_levels(full, half_window=2) if level.confirmed_index < 5]
    assert prefix_levels == full_levels


def test_future_pollution_does_not_mutate_already_confirmed_level():
    full = _frame(
        [
            (10, 7, 9),
            (11, 8, 10),
            (15, 9, 12),
            (12, 8, 10),
            (11, 7, 9),
            (14, 8, 13),
            (16, 10, 15),
        ]
    )
    before = [level for level in confirmed_levels(full, half_window=2) if level.confirmed_index <= 4]
    polluted = full.copy()
    polluted.loc[5:, "high"] = [1000, 2000]
    polluted.loc[5:, "low"] = [-1000, -2000]
    after = [level for level in confirmed_levels(polluted, half_window=2) if level.confirmed_index <= 4]
    assert before == after


def test_wick_rejection_requires_level_confirmed_strictly_before_sweep():
    frame = _frame(
        [
            (10, 7, 9),
            (11, 8, 10),
            (15, 9, 12),
            (12, 8, 10),
            (11, 7, 9),
            (16, 10, 14),
        ]
    )
    levels = confirmed_levels(frame, half_window=2)
    sweeps = wick_rejection_sweeps(frame, levels)
    high_sweeps = [event for event in sweeps if event.side == "HIGH_SIDE"]
    assert len(high_sweeps) == 1
    event = high_sweeps[0]
    assert event.level.confirmed_index == 4
    assert event.bar_index == 5
    assert event.overshoot_points == 1.0


def test_no_same_confirmation_bar_sweep():
    frame = _frame(
        [
            (10, 7, 9),
            (11, 8, 10),
            (15, 9, 12),
            (12, 8, 10),
            (16, 7, 14),
        ]
    )
    levels = confirmed_levels(frame, half_window=2)
    sweeps = wick_rejection_sweeps(frame, levels)
    assert not [event for event in sweeps if event.level.kind is LevelKind.HIGH]
