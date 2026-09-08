from datetime import datetime, timedelta, timezone

import pytest

from daxlab.runtime.contracts import Candle, DataQualityState
from daxlab.runtime.replay import ReplayEngine, assert_decision_parity


def make_candle(index: int, quality=DataQualityState.OK):
    event = datetime(2026, 1, 2, 8, 0, tzinfo=timezone.utc) + timedelta(minutes=5 * index)
    return Candle(
        symbol="DAX",
        timeframe="5m",
        event_time=event,
        close_time=event + timedelta(minutes=5),
        open=100.0 + index,
        high=102.0 + index,
        low=99.0 + index,
        close=101.0 + index,
        volume=None,
        source="fixture",
        received_at=event + timedelta(minutes=5, seconds=1),
        is_closed=True,
        quality_state=quality,
    )


def test_replay_uses_only_closed_safe_candles():
    core = lambda history: history[-1].close
    result = ReplayEngine(core).run([make_candle(0), make_candle(1, DataQualityState.GAP), make_candle(2)])
    assert result.decisions == (101.0, 103.0)
    assert result.blocked_candles == 1


def test_historical_and_replay_parity_gate():
    assert_decision_parity(["NO_TRADE", "TRADE"], ["NO_TRADE", "TRADE"])
    with pytest.raises(AssertionError, match="decision mismatch"):
        assert_decision_parity(["TRADE"], ["NO_TRADE"])
