from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from daxlab.runtime.candidate_config import Cand001Config
from daxlab.runtime.candidate_signal import (
    Cand001SignalState,
    SignalDirection,
    SignalReason,
    transition_cand001,
)
from daxlab.runtime.contracts import Candle, DataQualityState


BERLIN = ZoneInfo("Europe/Berlin")


def bar(
    hour,
    minute,
    *,
    open_price=100.0,
    high_price=101.0,
    low_price=99.0,
    close_price=100.0,
    closed=True,
    quality=DataQualityState.OK,
):
    event = datetime(2026, 9, 11, hour, minute, tzinfo=BERLIN)
    return Candle(
        symbol="DE40",
        timeframe="5m",
        event_time=event,
        close_time=event + timedelta(minutes=5),
        open=open_price,
        high=high_price,
        low=low_price,
        close=close_price,
        volume=None,
        source="TEST",
        received_at=event + timedelta(minutes=5, seconds=1),
        is_closed=closed,
        quality_state=quality,
    )


def build_or():
    state = Cand001SignalState()
    state = transition_cand001(state, bar(9, 0, high_price=102, low_price=99)).state
    state = transition_cand001(state, bar(9, 5, high_price=103, low_price=98)).state
    final = transition_cand001(state, bar(9, 10, high_price=102.5, low_price=98.5))
    return final.state, final


def test_or15_is_built_from_exact_three_closed_slots():
    state, transition = build_or()

    assert state.or_slots == ("09:00", "09:05", "09:10")
    assert state.or_high == 103
    assert state.or_low == 98
    assert state.or_complete
    assert transition.signal.reason is SignalReason.OR_READY
    assert transition.signal.direction is SignalDirection.NONE


def test_long_breakout_requires_close_above_completed_or_high():
    state, _ = build_or()
    transition = transition_cand001(
        state,
        bar(9, 15, open_price=102, high_price=105, low_price=101, close_price=104),
    )

    assert transition.signal.direction is SignalDirection.LONG
    assert transition.signal.reason is SignalReason.LONG_BREAKOUT
    assert transition.signal.trigger_price == 104
    assert transition.signal.or_high == 103
    assert transition.signal.or_low == 98


def test_wick_only_breakout_does_not_signal():
    state, _ = build_or()
    transition = transition_cand001(
        state,
        bar(9, 15, open_price=102, high_price=105, low_price=101, close_price=102.5),
    )

    assert transition.signal.direction is SignalDirection.NONE
    assert transition.signal.reason is SignalReason.NO_BREAKOUT
    assert transition.signal.trigger_price is None


def test_short_breakout_is_symmetric():
    state, _ = build_or()
    transition = transition_cand001(
        state,
        bar(9, 15, open_price=99, high_price=100, low_price=95, close_price=97),
    )

    assert transition.signal.direction is SignalDirection.SHORT
    assert transition.signal.reason is SignalReason.SHORT_BREAKOUT
    assert transition.signal.trigger_price == 97


def test_missing_or_slot_fails_closed_after_0915():
    state = Cand001SignalState()
    state = transition_cand001(state, bar(9, 0, high_price=102, low_price=99)).state
    state = transition_cand001(state, bar(9, 10, high_price=104, low_price=98)).state
    transition = transition_cand001(
        state,
        bar(9, 15, high_price=110, low_price=100, close_price=109),
    )

    assert not state.or_complete
    assert transition.signal.direction is SignalDirection.NONE
    assert transition.signal.reason is SignalReason.OR_INCOMPLETE


def test_unsafe_candle_does_not_mutate_strategy_state():
    state, _ = build_or()
    unsafe = bar(
        9,
        15,
        high_price=110,
        low_price=100,
        close_price=109,
        quality=DataQualityState.GAP,
    )
    transition = transition_cand001(state, unsafe)

    assert transition.state == state
    assert transition.signal.reason is SignalReason.DATA_UNSAFE
    assert transition.signal.direction is SignalDirection.NONE


def test_duplicate_and_out_of_order_bars_are_side_effect_free():
    state, _ = build_or()
    first_bar = bar(
        9,
        15,
        open_price=102,
        close_price=102,
        high_price=103,
        low_price=101,
    )
    first = transition_cand001(state, first_bar)
    duplicate = transition_cand001(first.state, first_bar)
    older = transition_cand001(
        first.state,
        bar(
            9,
            10,
            open_price=102,
            close_price=102,
            high_price=103,
            low_price=101,
        ),
    )

    assert duplicate.state == first.state
    assert duplicate.signal.reason is SignalReason.DUPLICATE_BAR
    assert older.state == first.state
    assert older.signal.reason is SignalReason.OUT_OF_ORDER_BAR


def test_new_berlin_session_resets_opening_range_state():
    state, _ = build_or()
    next_day_event = datetime(2026, 9, 12, 9, 0, tzinfo=BERLIN)
    next_day = Candle(
        symbol="DE40",
        timeframe="5m",
        event_time=next_day_event,
        close_time=next_day_event + timedelta(minutes=5),
        open=200,
        high=202,
        low=199,
        close=201,
        volume=None,
        source="TEST",
        received_at=next_day_event + timedelta(minutes=5, seconds=1),
        is_closed=True,
    )
    transition = transition_cand001(state, next_day)

    assert transition.state.session_date == "2026-09-12"
    assert transition.state.or_slots == ("09:00",)
    assert transition.state.or_high == 202
    assert transition.state.or_low == 199


def test_transition_is_deterministic_from_same_state_and_same_bar():
    state, _ = build_or()
    candle = bar(
        9,
        15,
        open_price=102,
        high_price=105,
        low_price=101,
        close_price=104,
    )

    left = transition_cand001(state, candle)
    right = transition_cand001(state, candle)

    assert left == right
    assert len(left.signal.data_fingerprint) == 64


def test_wrong_symbol_or_timeframe_fail_closed():
    event = datetime(2026, 9, 11, 9, 0, tzinfo=BERLIN)
    wrong_symbol = Candle(
        symbol="GER40",
        timeframe="5m",
        event_time=event,
        close_time=event + timedelta(minutes=5),
        open=100,
        high=101,
        low=99,
        close=100,
        volume=None,
        source="TEST",
        received_at=event + timedelta(minutes=5, seconds=1),
        is_closed=True,
    )
    with pytest.raises(ValueError, match="symbol"):
        transition_cand001(Cand001SignalState(), wrong_symbol)

    wrong_timeframe = Candle(
        symbol="DE40",
        timeframe="M5",
        event_time=event,
        close_time=event + timedelta(minutes=5),
        open=100,
        high=101,
        low=99,
        close=100,
        volume=None,
        source="TEST",
        received_at=event + timedelta(minutes=5, seconds=1),
        is_closed=True,
    )
    with pytest.raises(ValueError, match="timeframe"):
        transition_cand001(Cand001SignalState(), wrong_timeframe)


def test_outside_session_cannot_signal():
    transition = transition_cand001(
        Cand001SignalState(),
        bar(8, 55, high_price=110, low_price=90, close_price=109),
    )
    assert transition.signal.direction is SignalDirection.NONE
    assert transition.signal.reason is SignalReason.OUTSIDE_SESSION


def test_no_paper_or_execution_authority_is_required_by_signal_transition():
    config = Cand001Config()
    state, _ = build_or()
    transition = transition_cand001(
        state,
        bar(
            9,
            15,
            open_price=102,
            high_price=105,
            low_price=101,
            close_price=104,
        ),
        config=config,
    )

    assert transition.signal.direction is SignalDirection.LONG
    assert not hasattr(transition.signal, "quantity")
    assert not hasattr(transition.signal, "client_order_id")
    assert not hasattr(transition.signal, "execution_capability")
