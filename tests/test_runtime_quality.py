from datetime import UTC, datetime, timedelta

from daxlab.runtime.contracts import Candle, DataQualityState
from daxlab.runtime.quality import classify_sequence, source_agrees


def make_candle(minute=0, *, received_delay=1, **overrides):
    event = datetime(2026, 1, 2, 8, minute, tzinfo=UTC)
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
        "received_at": event + timedelta(minutes=5, seconds=received_delay),
        "is_closed": True,
    }
    values.update(overrides)
    return Candle(**values)


def test_sequence_quality_states():
    interval = timedelta(minutes=5)
    first = make_candle(0)
    assert classify_sequence(None, first, interval) is DataQualityState.OK
    assert classify_sequence(first, make_candle(0), interval) is DataQualityState.DUPLICATE
    assert classify_sequence(make_candle(5), first, interval) is DataQualityState.OUT_OF_ORDER
    assert classify_sequence(first, make_candle(10), interval) is DataQualityState.GAP
    assert (
        classify_sequence(first, make_candle(5, received_delay=180), interval)
        is DataQualityState.STALE
    )


def test_source_disagreement_is_explicit():
    left = make_candle(0)
    right = make_candle(0, source="second", close=101.5)
    assert source_agrees(left, right) is DataQualityState.SOURCE_DISAGREEMENT
