from dataclasses import replace
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

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


def test_trade_decision_uses_closed_bar_time_and_shared_contract():
    value = signal(SignalDirection.LONG)
    plan = build_cand001_trade_plan(value)
    assert plan is not None

    decision = build_cand001_decision(value, plan)

    assert decision.event_time == value.close_time
    assert decision.final_action is FinalAction.TRADE
    assert decision.regime == "OBSERVE_ONLY"
    assert decision.structure == "OPENING_RANGE/OR15"
    assert decision.setup == "LONG_BREAKOUT"
    assert decision.risk_result == "GEOMETRY_VALID"
    assert decision.blockers == ()
    assert decision.filter_results["entry_confirmed"] is True
    assert len(decision.decision_id) == 64


def test_no_breakout_is_logged_as_first_class_no_trade():
    value = signal(SignalDirection.NONE)
    decision = build_cand001_decision(value, None)

    assert decision.final_action is FinalAction.NO_TRADE
    assert decision.setup == "NO_BREAKOUT"
    assert decision.risk_result == "NOT_APPLICABLE"
    assert decision.filter_results["entry_confirmed"] is False


def test_directional_signal_without_trade_plan_fails_closed():
    with pytest.raises(ValueError, match="requires a trade plan"):
        build_cand001_decision(signal(SignalDirection.LONG), None)


def test_non_directional_signal_cannot_carry_trade_plan():
    long_signal = signal(SignalDirection.LONG)
    plan = build_cand001_trade_plan(long_signal)
    assert plan is not None

    with pytest.raises(ValueError, match="cannot carry a trade plan"):
        build_cand001_decision(signal(SignalDirection.NONE), plan)


def test_trade_plan_provenance_must_match_signal():
    value = signal(SignalDirection.LONG)
    plan = build_cand001_trade_plan(value)
    assert plan is not None
    wrong = replace(plan, signal_data_fingerprint="b" * 64)

    with pytest.raises(ValueError, match="provenance"):
        build_cand001_decision(value, wrong)


def test_unsafe_data_is_explicitly_blocked_and_no_trade():
    value = signal(
        SignalDirection.NONE,
        reason=SignalReason.DATA_UNSAFE,
    )
    decision = build_cand001_decision(value, None)

    assert decision.final_action is FinalAction.NO_TRADE
    assert decision.blockers == ("DATA_UNSAFE",)
    assert decision.filter_results["data_safe"] is False


def test_decision_identity_is_deterministic():
    value = signal(SignalDirection.SHORT)
    plan = build_cand001_trade_plan(value)
    assert plan is not None

    left = build_cand001_decision(value, plan)
    right = build_cand001_decision(value, plan)
    assert left == right
