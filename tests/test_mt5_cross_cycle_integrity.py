from __future__ import annotations

from datetime import datetime, timezone

from daxlab.runtime.mt5_cross_cycle_integrity import evaluate_cross_cycle_integrity
from daxlab.runtime.mt5_feed_payload import parse_closed_m5_feed


def _feed(times_and_closes: list[tuple[str, float]]):
    bars = []
    for open_time, close in times_and_closes:
        bars.append(
            {
                "open_time": open_time,
                "open": close - 1.0,
                "high": close + 1.0,
                "low": close - 2.0,
                "close": close,
            }
        )
    return parse_closed_m5_feed(
        {
            "observed_at": "2026-09-10T12:00:00+00:00",
            "requested_start_pos": 1,
            "max_age_seconds": 999999,
            "bars": bars,
        }
    )


def test_identical_overlap_is_green() -> None:
    previous = _feed(
        [
            ("2026-09-10T09:00:00+00:00", 100.0),
            ("2026-09-10T09:05:00+00:00", 101.0),
        ]
    )
    current = _feed(
        [
            ("2026-09-10T09:05:00+00:00", 101.0),
            ("2026-09-10T09:10:00+00:00", 102.0),
        ]
    )

    result = evaluate_cross_cycle_integrity(previous, current)
    assert result.status == "GREEN"
    assert result.blockers == ()
    assert result.overlapping_bars == 1
    assert result.identical_overlaps == 1
    assert result.mutated_overlaps == 0
    assert result.execution_capability == "NONE"
    assert result.order_execution_enabled is False


def test_mutated_historical_bar_blocks() -> None:
    previous = _feed(
        [
            ("2026-09-10T09:00:00+00:00", 100.0),
            ("2026-09-10T09:05:00+00:00", 101.0),
        ]
    )
    current = _feed(
        [
            ("2026-09-10T09:05:00+00:00", 999.0),
            ("2026-09-10T09:10:00+00:00", 102.0),
        ]
    )

    result = evaluate_cross_cycle_integrity(previous, current)
    assert result.status == "BLOCKED"
    assert result.blockers == ("HISTORICAL_BAR_MUTATION",)
    assert result.mutated_overlaps == 1


def test_latest_time_regression_blocks() -> None:
    previous = _feed(
        [
            ("2026-09-10T09:10:00+00:00", 102.0),
            ("2026-09-10T09:15:00+00:00", 103.0),
        ]
    )
    current = _feed(
        [
            ("2026-09-10T09:00:00+00:00", 100.0),
            ("2026-09-10T09:05:00+00:00", 101.0),
        ]
    )

    result = evaluate_cross_cycle_integrity(previous, current)
    assert result.status == "BLOCKED"
    assert "LATEST_BAR_TIME_REGRESSION" in result.blockers


def test_no_overlap_can_still_be_green_without_session_guessing() -> None:
    previous = _feed(
        [
            ("2026-09-10T09:00:00+00:00", 100.0),
            ("2026-09-10T09:05:00+00:00", 101.0),
        ]
    )
    current = _feed(
        [
            ("2026-09-10T10:00:00+00:00", 110.0),
            ("2026-09-10T10:05:00+00:00", 111.0),
        ]
    )

    result = evaluate_cross_cycle_integrity(previous, current)
    assert result.status == "GREEN"
    assert result.overlapping_bars == 0
    assert result.blockers == ()


def test_result_times_are_timezone_aware() -> None:
    previous = _feed([("2026-09-10T09:00:00+00:00", 100.0)])
    current = _feed([("2026-09-10T09:05:00+00:00", 101.0)])
    result = evaluate_cross_cycle_integrity(previous, current)
    assert result.latest_previous_open_time == datetime(2026, 9, 10, 9, 0, tzinfo=timezone.utc)
    assert result.latest_current_open_time == datetime(2026, 9, 10, 9, 5, tzinfo=timezone.utc)
