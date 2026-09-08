from datetime import UTC, datetime, timedelta

import pytest

from daxlab.runtime.contracts import Candle, DataQualityState, RuntimeMode


def candle(**overrides):
    event = datetime(2026, 1, 2, 8, 0, tzinfo=UTC)
    values = {
        "symbol": "DAX",
        "timeframe": "5m",
        "event_time": event,
        "close_time": event + timedelta(minutes=5),
        "open": 100.0,
        "high": 102.0,
        "low": 99.0,
        "close": 101.0,
        "volume": None,
        "source": "fixture",
        "received_at": event + timedelta(minutes=5, seconds=1),
        "is_closed": True,
        "quality_state": DataQualityState.OK,
    }
    values.update(overrides)
    return Candle(**values)


def test_runtime_modes_are_explicit():
    assert [mode.value for mode in RuntimeMode] == [
        "HISTORICAL",
        "REPLAY",
        "SHADOW",
        "PAPER",
        "LIVE",
    ]


def test_only_closed_ok_candle_is_safe_for_decision():
    assert candle().safe_for_decision is True
    assert candle(is_closed=False).safe_for_decision is False
    assert candle(quality_state=DataQualityState.GAP).safe_for_decision is False


def test_timestamps_must_be_timezone_aware():
    naive_event = datetime(2026, 1, 2, 8, 0, tzinfo=UTC).replace(tzinfo=None)
    with pytest.raises(ValueError, match="timezone-aware"):
        candle(event_time=naive_event)
