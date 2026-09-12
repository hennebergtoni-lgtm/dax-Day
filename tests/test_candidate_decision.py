from dataclasses import replace
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from daxlab.runtime.candidate_admission import (
    AdmissionStatus,
    Cand001AdmissionResult,
    Cand001AdmissionState,
    admit_cand001_trade,
)
from daxlab.runtime.candidate_decision import build_cand001_decision
from daxlab.runtime.candidate_signal import Cand001Signal, SignalDirection, SignalReason
from daxlab.runtime.candidate_trade_plan import build_cand001_trade_plan
from daxlab.runtime.decision import FinalAction


BERLIN = ZoneInfo("Europe/Berlin")


def signal(
    direction: SignalDirection,
    *,
    reason: SignalReason | None = None,
) -> Cand001Signal:
    event = datetime(2026, 9, 11, 9, 15, tzinfo=BERLIN)
    if direction is SignalDirection.LONG:
        trigger = 104.0
        default_reason = SignalReason.LONG_BREAKOUT
    elif direction is SignalDirection.SHORT:
        trigger = 97.0
        default_reason = SignalReason.SHORT_BREAKOUT
    else:
        trigger = None
        default_reason = SignalReason.NO_BREAKOUT
    return Cand001Signal(
        event_time=event,
        close_time=event + timedelta(minutes=5),
        direction=direction,
        reason=reason or default_reason,
        or_high=103.0,
        or_low=98.0,
        trigger_price=trigger,
        data_fingerprint="a" * 64,
    )


def admission(value: Cand001Signal):
    plan = build_cand001_trade_plan(value)
    return admit_cand001_trade(Cand001AdmissionState(), value, plan)


def test_trade_decision_uses_closed_bar_time_and_shared_contract():
    value = signal(SignalDirection.LONG)
    admitted = admission(value)

    decision = build_cand001_decision(value, admitted)

    assert decision.event_time == value.close_time
    assert decision.final_action is FinalAction.TRADE
    assert decision.regime == "OBSERVE_ONLY"
    assert decision.structure == "OPENING_RANGE/OR15"
    assert decision.setup == "LONG_BREAKOUT"
    assert decision.risk_result == "ADMITTED"
    assert decision.blockers == ()
    assert decision.filter_results["entry_confirmed"] is True
    assert decision.filter_results["session_trade_slot_available"] is True
    assert len(decision.decision_id) == 64


def test_no_breakout_is_logged_as_first_class_no_trade():
    value = signal(SignalDirection.NONE)
    result = admission(value)
    decision = build_cand001_decision(value, result)

    assert decision.final_action is FinalAction.NO_TRADE
    assert decision.setup == "NO_BREAKOUT"
    assert decision.risk_result == "NOT_APPLICABLE"
    assert decision.filter_results["entry_confirmed"] is False


def test_session_limit_turns_visible_signal_into_blocked_no_trade():
    value = signal(SignalDirection.LONG)
    plan = build_cand001_trade_plan(value)
    assert plan is not None
    limited = admit_cand001_trade(
        Cand001AdmissionState(session_date="2026-09-11", trades_admitted=1),
        value,
        plan,
    )

    decision = build_cand001_decision(value, limited)

    assert limited.status is AdmissionStatus.SESSION_LIMIT
    assert decision.final_action is FinalAction.NO_TRADE
    assert decision.blockers == ("SESSION_TRADE_LIMIT",)
    assert decision.risk_result == "SESSION_LIMIT"
    assert decision.filter_results["entry_confirmed"] is True
    assert decision.filter_results["session_trade_slot_available"] is False


def test_allowed_admission_requires_directional_signal_and_plan():
    value = signal(SignalDirection.NONE)
    invalid = Cand001AdmissionResult(
        state=Cand001AdmissionState(session_date="2026-09-11", trades_admitted=1),
        status=AdmissionStatus.ALLOWED,
        admitted_plan=None,
    )
    with pytest.raises(ValueError, match="requires directional signal and trade plan"):
        build_cand001_decision(value, invalid)


def test_trade_plan_provenance_must_match_signal():
    value = signal(SignalDirection.LONG)
    admitted = admission(value)
    assert admitted.admitted_plan is not None
    wrong_plan = replace(admitted.admitted_plan, signal_data_fingerprint="b" * 64)
    wrong = replace(admitted, admitted_plan=wrong_plan)

    with pytest.raises(ValueError, match="provenance"):
        build_cand001_decision(value, wrong)


def test_unsafe_data_is_explicitly_blocked_and_no_trade():
    value = signal(
        SignalDirection.NONE,
        reason=SignalReason.DATA_UNSAFE,
    )
    result = admission(value)
    decision = build_cand001_decision(value, result)

    assert decision.final_action is FinalAction.NO_TRADE
    assert decision.blockers == ("DATA_UNSAFE",)
    assert decision.filter_results["data_safe"] is False


def test_decision_identity_is_deterministic():
    value = signal(SignalDirection.SHORT)
    admitted = admission(value)

    left = build_cand001_decision(value, admitted)
    right = build_cand001_decision(value, admitted)
    assert left == right
