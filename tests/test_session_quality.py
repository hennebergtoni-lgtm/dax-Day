from datetime import UTC, datetime, timedelta

from daxlab.runtime.contracts import Candle, DataQualityState
from daxlab.runtime.quality import classify_session_sequence


def candle(event_time: datetime) -> Candle:
    return Candle(
        symbol="DAX",
        timeframe="M5",
        event_time=event_time,
        close_time=event_time + timedelta(minutes=5),
        open=100.0,
        high=101.0,
        low=99.0,
        close=100.5,
        volume=None,
        source="fixture",
        received_at=event_time + timedelta(minutes=5, seconds=30),
        is_closed=True,
    )


def test_new_berlin_session_does_not_create_false_gap() -> None:
    previous = candle(datetime(2026, 1, 2, 16, 30, tzinfo=UTC))  # 17:30 Berlin
    current = candle(datetime(2026, 1, 5, 8, 0, tzinfo=UTC))  # 09:00 Berlin
    assert (
        classify_session_sequence(previous, current, timedelta(minutes=5))
        is DataQualityState.OK
    )


def test_intraday_missing_bar_is_still_gap() -> None:
    previous = candle(datetime(2026, 1, 5, 8, 0, tzinfo=UTC))
    current = candle(datetime(2026, 1, 5, 8, 10, tzinfo=UTC))
    assert (
        classify_session_sequence(previous, current, timedelta(minutes=5))
        is DataQualityState.GAP
    )


def test_dst_week_session_boundary_uses_berlin_date() -> None:
    previous = candle(datetime(2026, 3, 27, 16, 30, tzinfo=UTC))  # CET session close
    current = candle(datetime(2026, 3, 30, 7, 0, tzinfo=UTC))  # CEST session open
    assert (
        classify_session_sequence(previous, current, timedelta(minutes=5))
        is DataQualityState.OK
    )
