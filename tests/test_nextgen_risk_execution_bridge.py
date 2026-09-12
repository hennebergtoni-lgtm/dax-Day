from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

import pytest

from daxlab.domain.execution import OrderSide
from daxlab.domain.market import InstrumentId
from daxlab.domain.risk import (
    InstrumentRiskInputs,
    RiskDecisionAction,
    RiskRequest,
    evaluate_fixed_cash_risk,
)
from daxlab.domain.risk_execution import build_execution_intent_from_risk
from daxlab.domain.strategy import TradeDirection, TradePlan


UTC = timezone.utc


def _plan(direction: TradeDirection = TradeDirection.LONG) -> TradePlan:
    if direction is TradeDirection.LONG:
        return TradePlan(
            instrument_id=InstrumentId("DAX40.CFD"),
            direction=direction,
            entry_price=25000.0,
            stop_price=24900.0,
            target_price=25200.0,
        )
    return TradePlan(
        instrument_id=InstrumentId("DAX40.CFD"),
        direction=direction,
        entry_price=25000.0,
        stop_price=25100.0,
        target_price=24800.0,
    )


def _request(
    *,
    direction: TradeDirection = TradeDirection.LONG,
    max_loss_cash: float = 257.0,
) -> RiskRequest:
    return RiskRequest.build(
        strategy_decision_id="a" * 64,
        trade_plan=_plan(direction),
        max_loss_cash=max_loss_cash,
        loss_currency="EUR",
        instrument=InstrumentRiskInputs(
            instrument_id=InstrumentId("DAX40.CFD"),
            quantity_min=0.1,
            quantity_step=0.1,
            quantity_max=10.0,
            cash_loss_per_price_unit_per_quantity=1.0,
            currency="EUR",
        ),
    )


def _created_at() -> datetime:
    return datetime(2026, 9, 11, 8, 5, tzinfo=UTC)


def test_allow_risk_builds_deterministic_execution_intent() -> None:
    request = _request()
    decision = evaluate_fixed_cash_risk(request)

    first = build_execution_intent_from_risk(
        request=request,
        decision=decision,
        created_at=_created_at(),
    )
    second = build_execution_intent_from_risk(
        request=request,
        decision=decision,
        created_at=_created_at(),
    )

    assert first == second
    assert first.decision_id == request.strategy_decision_id
    assert len(first.provenance_fingerprint) == 64
    assert first.instrument_id == InstrumentId("DAX40.CFD")
    assert first.side is OrderSide.BUY
    assert first.quantity == 2.5
    assert first.requested_price == 25000.0
    assert first.stop_price == 24900.0
    assert first.target_price == 25200.0


def test_short_plan_maps_deterministically_to_sell() -> None:
    request = _request(direction=TradeDirection.SHORT)
    decision = evaluate_fixed_cash_risk(request)

    intent = build_execution_intent_from_risk(
        request=request,
        decision=decision,
        created_at=_created_at(),
    )

    assert intent.side is OrderSide.SELL
    assert intent.quantity == 2.5
    assert intent.stop_price == 25100.0
    assert intent.target_price == 24800.0


def test_deny_risk_cannot_create_execution_intent() -> None:
    request = _request(max_loss_cash=5.0)
    decision = evaluate_fixed_cash_risk(request)
    assert decision.action is RiskDecisionAction.DENY

    with pytest.raises(ValueError, match="ALLOW"):
        build_execution_intent_from_risk(
            request=request,
            decision=decision,
            created_at=_created_at(),
        )


def test_request_identity_tampering_fails_closed() -> None:
    request = _request()
    decision = evaluate_fixed_cash_risk(request)
    tampered = replace(request, request_id="b" * 64)

    with pytest.raises(ValueError, match="request identity"):
        build_execution_intent_from_risk(
            request=tampered,
            decision=decision,
            created_at=_created_at(),
        )


def test_risk_decision_quantity_tampering_fails_closed() -> None:
    request = _request()
    decision = evaluate_fixed_cash_risk(request)
    forged = replace(decision, quantity=9.9, decision_id="c" * 64)

    with pytest.raises(ValueError, match="canonical risk evaluation"):
        build_execution_intent_from_risk(
            request=request,
            decision=forged,
            created_at=_created_at(),
        )


def test_risk_decision_from_other_request_fails_closed() -> None:
    request = _request(max_loss_cash=257.0)
    other_request = _request(max_loss_cash=300.0)
    other_decision = evaluate_fixed_cash_risk(other_request)

    with pytest.raises(ValueError, match="canonical risk evaluation"):
        build_execution_intent_from_risk(
            request=request,
            decision=other_decision,
            created_at=_created_at(),
        )


def test_bridge_adds_no_broker_or_authorization_capability() -> None:
    request = _request()
    decision = evaluate_fixed_cash_risk(request)
    intent = build_execution_intent_from_risk(
        request=request,
        decision=decision,
        created_at=_created_at(),
    )

    assert not hasattr(intent, "broker")
    assert not hasattr(intent, "order_execution_enabled")
    assert not hasattr(intent, "paper_authorized")
    assert not hasattr(intent, "live_authorized")
