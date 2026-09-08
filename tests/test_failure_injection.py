from datetime import UTC, datetime, timedelta

import pytest

from daxlab.runtime.contracts import Candle, DataQualityState
from daxlab.runtime.decision import FinalAction
from daxlab.runtime.gates import RuntimeSafetySnapshot, evaluate_runtime_safety
from daxlab.runtime.quality import classify_sequence


def candle(index: int, *, received_delay: int = 1) -> Candle:
    event = datetime(2026, 1, 5, 8, 0, tzinfo=UTC) + timedelta(minutes=5 * index)
    return Candle(
        symbol="DAX",
        timeframe="5m",
        event_time=event,
        close_time=event + timedelta(minutes=5),
        open=100.0,
        high=101.0,
        low=99.0,
        close=100.5,
        volume=None,
        source="fixture",
        received_at=event + timedelta(minutes=5, seconds=received_delay),
        is_closed=True,
    )


def gate_for_quality(quality: DataQualityState):
    return evaluate_runtime_safety(
        RuntimeSafetySnapshot(
            data_quality=quality,
            feed_connected=True,
            spread=0.2,
            max_spread=1.0,
        )
    )


@pytest.mark.parametrize(
    "quality",
    [
        DataQualityState.GAP,
        DataQualityState.DUPLICATE,
        DataQualityState.OUT_OF_ORDER,
        DataQualityState.STALE,
    ],
)
def test_injected_market_data_faults_end_in_no_trade(quality):
    gate = gate_for_quality(quality)
    assert gate.guard_action(FinalAction.TRADE) is FinalAction.NO_TRADE


def test_missing_duplicate_out_of_order_and_late_are_detected_then_blocked():
    interval = timedelta(minutes=5)
    first = candle(0)
    injected = {
        "missing": classify_sequence(first, candle(2), interval),
        "duplicate": classify_sequence(first, candle(0), interval),
        "out_of_order": classify_sequence(candle(1), first, interval),
        "late": classify_sequence(first, candle(1, received_delay=180), interval),
    }
    assert injected == {
        "missing": DataQualityState.GAP,
        "duplicate": DataQualityState.DUPLICATE,
        "out_of_order": DataQualityState.OUT_OF_ORDER,
        "late": DataQualityState.STALE,
    }
    for quality in injected.values():
        gate = gate_for_quality(quality)
        assert gate.allowed is False
        assert gate.guard_action(FinalAction.TRADE) is FinalAction.NO_TRADE


def test_feed_spread_and_contradictory_state_injection_are_fail_safe():
    cases = [
        {"feed_connected": False, "spread": 0.2, "contradictory_state": False},
        {"feed_connected": True, "spread": 1.5, "contradictory_state": False},
        {"feed_connected": True, "spread": 0.2, "contradictory_state": True},
    ]
    for case in cases:
        gate = evaluate_runtime_safety(
            RuntimeSafetySnapshot(
                data_quality=DataQualityState.OK,
                max_spread=1.0,
                **case,
            )
        )
        assert gate.allowed is False
        assert gate.guard_action(FinalAction.TRADE) is FinalAction.NO_TRADE
