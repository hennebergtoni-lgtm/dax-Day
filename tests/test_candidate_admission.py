from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from daxlab.runtime.candidate_admission import (
    AdmissionStatus,
    Cand001AdmissionState,
    admit_cand001_trade,
)
from daxlab.runtime.candidate_signal import Cand001Signal, SignalDirection, SignalReason
from daxlab.runtime.candidate_trade_plan import build_cand001_trade_plan


BERLIN = ZoneInfo("Europe/Berlin")


def signal(direction: SignalDirection, *, day: int = 11) -> Cand001Signal:
    event = datetime(2026, 9, day, 9, 15, tzinfo=BERLIN)
    trigger = 104.0 if direction is SignalDirection.LONG else 97.0 if direction is SignalDirection.SHORT else None
    reason = (
        SignalReason.LONG_BREAKOUT
        if direction is SignalDirection.LONG
        else SignalReason.SHORT_BREAKOUT
        if direction is SignalDirection.SHORT
        else SignalReason.NO_BREAKOUT
    )
    return Cand001Signal(
        event_time=event,
        close_time=event + timedelta(minutes=5),
        direction=direction,
        reason=reason,
        or_high=103.0,
        or_low=98.0,
        trigger_price=trigger,
        data_fingerprint=("a" if day == 11 else "b") * 64,
    )


def test_first_trade_is_admitted_and_counted():
    value = signal(SignalDirection.LONG)
    plan = build_cand001_trade_plan(value)
    assert plan is not None

    result = admit_cand001_trade(Cand001AdmissionState(), value, plan)

    assert result.status is AdmissionStatus.ALLOWED
    assert result.admitted_plan == plan
    assert result.state.session_date == "2026-09-11"
    assert result.state.trades_admitted == 1


def test_second_trade_same_session_is_visible_but_blocked():
    first_signal = signal(SignalDirection.LONG)
    first_plan = build_cand001_trade_plan(first_signal)
    assert first_plan is not None
    first = admit_cand001_trade(Cand001AdmissionState(), first_signal, first_plan)

    second_signal = signal(SignalDirection.SHORT)
    second_plan = build_cand001_trade_plan(second_signal)
    assert second_plan is not None
    second = admit_cand001_trade(first.state, second_signal, second_plan)

    assert second.status is AdmissionStatus.SESSION_LIMIT
    assert second.admitted_plan is None
    assert second.state.trades_admitted == 1


def test_new_session_resets_trade_admission_count():
    first_signal = signal(SignalDirection.LONG, day=11)
    first_plan = build_cand001_trade_plan(first_signal)
    assert first_plan is not None
    first = admit_cand001_trade(Cand001AdmissionState(), first_signal, first_plan)

    next_signal = signal(SignalDirection.SHORT, day=12)
    next_plan = build_cand001_trade_plan(next_signal)
    assert next_plan is not None
    next_result = admit_cand001_trade(first.state, next_signal, next_plan)

    assert next_result.status is AdmissionStatus.ALLOWED
    assert next_result.state.session_date == "2026-09-12"
    assert next_result.state.trades_admitted == 1


def test_no_signal_does_not_consume_session_trade_slot():
    value = signal(SignalDirection.NONE)
    result = admit_cand001_trade(Cand001AdmissionState(), value, None)

    assert result.status is AdmissionStatus.NO_SIGNAL
    assert result.state.trades_admitted == 0


def test_directional_signal_requires_plan_before_admission():
    with pytest.raises(ValueError, match="requires a trade plan"):
        admit_cand001_trade(Cand001AdmissionState(), signal(SignalDirection.LONG), None)
