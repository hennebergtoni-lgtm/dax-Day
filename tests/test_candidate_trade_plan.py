from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from daxlab.runtime.candidate_signal import Cand001Signal, SignalDirection, SignalReason
from daxlab.runtime.candidate_trade_plan import build_cand001_trade_plan


BERLIN = ZoneInfo("Europe/Berlin")


def signal(direction: SignalDirection) -> Cand001Signal:
    event = datetime(2026, 9, 11, 9, 15, tzinfo=BERLIN)
    if direction is SignalDirection.LONG:
        trigger = 104.0
    elif direction is SignalDirection.SHORT:
        trigger = 97.0
    else:
        trigger = None
    return Cand001Signal(
        event_time=event,
        close_time=event + timedelta(minutes=5),
        direction=direction,
        reason=(
            SignalReason.LONG_BREAKOUT
            if direction is SignalDirection.LONG
            else SignalReason.SHORT_BREAKOUT
            if direction is SignalDirection.SHORT
            else SignalReason.NO_BREAKOUT
        ),
        or_high=103.0,
        or_low=98.0,
        trigger_price=trigger,
        data_fingerprint="a" * 64,
    )


def test_long_trade_plan_uses_or_opposite_stop_and_fixed_1_5r_target():
    plan = build_cand001_trade_plan(signal(SignalDirection.LONG))

    assert plan is not None
    assert plan.direction is SignalDirection.LONG
    assert plan.entry_price == 104.0
    assert plan.stop_price == 98.0
    assert plan.risk_points == 6.0
    assert plan.reward_risk == 1.5
    assert plan.target_price == 113.0
    assert len(plan.plan_fingerprint) == 64


def test_short_trade_plan_is_symmetric():
    plan = build_cand001_trade_plan(signal(SignalDirection.SHORT))

    assert plan is not None
    assert plan.direction is SignalDirection.SHORT
    assert plan.entry_price == 97.0
    assert plan.stop_price == 103.0
    assert plan.risk_points == 6.0
    assert plan.reward_risk == 1.5
    assert plan.target_price == 88.0


def test_no_signal_produces_no_trade_plan():
    assert build_cand001_trade_plan(signal(SignalDirection.NONE)) is None


def test_directional_signal_requires_complete_price_geometry():
    value = signal(SignalDirection.LONG)
    incomplete = Cand001Signal(
        event_time=value.event_time,
        close_time=value.close_time,
        direction=value.direction,
        reason=value.reason,
        or_high=value.or_high,
        or_low=None,
        trigger_price=value.trigger_price,
        data_fingerprint=value.data_fingerprint,
    )
    with pytest.raises(ValueError, match="completed opening range"):
        build_cand001_trade_plan(incomplete)


def test_trade_plan_is_deterministic_for_same_signal():
    value = signal(SignalDirection.LONG)
    assert build_cand001_trade_plan(value) == build_cand001_trade_plan(value)


def test_trade_plan_contains_no_quantity_or_order_identity():
    plan = build_cand001_trade_plan(signal(SignalDirection.LONG))
    assert plan is not None
    assert not hasattr(plan, "quantity")
    assert not hasattr(plan, "client_order_id")
    assert not hasattr(plan, "execution_capability")
