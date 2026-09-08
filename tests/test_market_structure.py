import pandas as pd

from daxlab.research.liquidity_sweep import ConfirmedLevel, LevelKind
from daxlab.research.market_structure import StructureLabel, close_breaks, label_structure


def _level(*, pivot, confirmed, price, kind):
    base = pd.Timestamp("2026-01-01T09:00:00Z")
    return ConfirmedLevel(
        pivot_index=pivot,
        pivot_time=base + pd.Timedelta(minutes=5 * pivot),
        confirmed_index=confirmed,
        confirmed_time=base + pd.Timedelta(minutes=5 * confirmed),
        price=price,
        kind=kind,
    )


def test_structure_labels_use_only_confirmed_sequence():
    levels = [
        _level(pivot=1, confirmed=3, price=100.0, kind=LevelKind.HIGH),
        _level(pivot=2, confirmed=4, price=90.0, kind=LevelKind.LOW),
        _level(pivot=5, confirmed=7, price=105.0, kind=LevelKind.HIGH),
        _level(pivot=6, confirmed=8, price=92.0, kind=LevelKind.LOW),
    ]
    labeled = label_structure(levels)
    assert labeled[0].label is None
    assert labeled[1].label is None
    assert labeled[2].label is StructureLabel.HH
    assert labeled[3].label is StructureLabel.HL


def test_close_break_requires_reference_confirmed_strictly_before_bar():
    frame = pd.DataFrame(
        {
            "datetime": pd.date_range("2026-01-01T09:00:00Z", periods=6, freq="5min"),
            "close": [95.0, 97.0, 99.0, 101.0, 102.0, 103.0],
        }
    )
    high = _level(pivot=1, confirmed=3, price=100.0, kind=LevelKind.HIGH)
    events = close_breaks(frame, [high])
    assert len(events) == 1
    assert events[0].bar_index == 4
    assert events[0].direction == "UP"


def test_close_break_is_emitted_once_per_level():
    frame = pd.DataFrame(
        {
            "datetime": pd.date_range("2026-01-01T09:00:00Z", periods=7, freq="5min"),
            "close": [95.0, 97.0, 99.0, 100.0, 101.0, 102.0, 103.0],
        }
    )
    high = _level(pivot=1, confirmed=3, price=100.0, kind=LevelKind.HIGH)
    events = close_breaks(frame, [high])
    assert len(events) == 1
    assert events[0].bar_index == 4


def test_future_bars_do_not_change_earlier_bos_event():
    prefix = pd.DataFrame(
        {
            "datetime": pd.date_range("2026-01-01T09:00:00Z", periods=5, freq="5min"),
            "close": [95.0, 97.0, 99.0, 100.0, 101.0],
        }
    )
    full = pd.concat(
        [
            prefix,
            pd.DataFrame(
                {
                    "datetime": pd.date_range("2026-01-01T09:25:00Z", periods=2, freq="5min"),
                    "close": [-999.0, 999.0],
                }
            ),
        ],
        ignore_index=True,
    )
    high = _level(pivot=1, confirmed=3, price=100.0, kind=LevelKind.HIGH)
    assert close_breaks(prefix, [high]) == close_breaks(full, [high])[:1]
