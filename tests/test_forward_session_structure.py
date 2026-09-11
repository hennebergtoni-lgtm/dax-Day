import pandas as pd
import pytest

from daxlab.research.forward_session_structure import analyze_forward_session_structure


def _bars() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "open_time": pd.to_datetime(
                [
                    "2026-09-11T07:00:00Z",
                    "2026-09-11T07:05:00Z",
                    "2026-09-11T07:10:00Z",
                    "2026-09-11T07:15:00Z",
                    "2026-09-11T07:30:00Z",
                ]
            ),
            "open": [25461.1, 25470.0, 25455.0, 25452.6, 25440.0],
            "high": [25497.6, 25480.0, 25470.0, 25459.6, 25445.0],
            "low": [25451.1, 25445.0, 25437.1, 25440.6, 25430.0],
            "close": [25470.0, 25455.0, 25453.1, 25452.6, 25435.0],
        }
    )


def test_known_or5_or15_and_breaks_match_forward_evidence() -> None:
    result = analyze_forward_session_structure(_bars())

    assert result.or5.complete is True
    assert result.or5.high == 25497.6
    assert result.or5.low == 25451.1
    assert result.or5.first_high_break_time is None
    assert result.or5.first_low_break_time == "2026-09-11T09:05:00+02:00"

    assert result.or15.complete is True
    assert result.or15.high == 25497.6
    assert result.or15.low == 25437.1
    assert result.or15.first_high_break_time is None
    assert result.or15.first_low_break_time == "2026-09-11T09:30:00+02:00"
    assert result.execution_capability == "NONE"
    assert result.order_execution_enabled is False


def test_equal_or_boundary_is_not_a_break() -> None:
    bars = _bars().iloc[:4].copy()
    bars.loc[bars.index[-1], ["open", "high", "low", "close"]] = [
        25452.6,
        25497.6,
        25437.1,
        25452.6,
    ]

    result = analyze_forward_session_structure(bars)

    assert result.or15.first_high_break_time is None
    assert result.or15.first_low_break_time is None
    assert result.or15.latest_close_inside is True


def test_or15_remains_incomplete_until_all_three_required_bars_exist() -> None:
    result = analyze_forward_session_structure(_bars().iloc[:2])

    assert result.or5.complete is True
    assert result.or15.complete is False
    assert result.or15.required_bars == 3
    assert result.or15.observed_bars == 2
    assert result.or15.high is None
    assert result.or15.low is None


def test_missing_required_opening_bar_keeps_or15_incomplete() -> None:
    bars = _bars().iloc[[0, 2, 3]].copy()

    result = analyze_forward_session_structure(bars)

    assert result.or15.complete is False
    assert result.or15.observed_bars == 2


def test_duplicate_open_time_is_rejected() -> None:
    bars = pd.concat([_bars().iloc[:2], _bars().iloc[[1]]], ignore_index=True)

    with pytest.raises(ValueError, match="open_time values must be unique"):
        analyze_forward_session_structure(bars)


def test_later_extremes_do_not_change_frozen_opening_range() -> None:
    bars = _bars()
    bars.loc[bars.index[-1], ["open", "high", "low", "close"]] = [
        25440.0,
        26000.0,
        25000.0,
        25460.0,
    ]

    result = analyze_forward_session_structure(bars)

    assert result.or5.high == 25497.6
    assert result.or5.low == 25451.1
    assert result.or15.high == 25497.6
    assert result.or15.low == 25437.1
    assert result.session_high == 26000.0
    assert result.session_low == 25000.0
