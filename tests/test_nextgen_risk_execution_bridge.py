from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

import pytest

from daxlab.domain.execution import OrderSide
from daxlab.domain.loss_admission import (
    LossExposureObservation,
    LossExposurePolicy,
    evaluate_loss_exposure_admission,
)
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


def _admission(*, open_positions: int = 0):
    policy = LossExposurePolicy.build(
        currency="EUR",
        daily_drawdown_cap_cash=100.0,
        weekly_drawdown_cap_cash=250.0,
        max_consecutive_losses=3,
        max_open_positions=1,
    )
    observation = LossExposureObservation.build(
        currency="EUR",
        daily_drawdown_cash=10.0,
        weekly_drawdown_cash=20.0,
        consecutive_losses=0,
        open_positions=open_positions,
    )
    decision = evaluate_loss_exposure_admission(
        policy=policy,
        observation=observation,
    )
    return policy, observation, decision


def _intent(request: RiskRequest, decision, *, open_positions: int = 0):
    policy, observation, admission = _admission(open_positions=open_positions)
    return build_execution_intent_from_risk(
        request=request,
        decision=decision,
        admission_policy=policy,
        admission_observation=observation,
        admission_decision=admission,
        created_at=_created_at(),
    )


def _created_at() -> datetime:
    return datetime(2026, 9, 11, 8, 5, tzinfo=UTC)


def test_allow_risk_and_admission_build_deterministic_execution_intent() -> None:
    request = _request()
    decision = evaluate_fixed_cash_risk(request)

    first = _intent(request, decision)
    second = _intent(request, decision)

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

    intent = _intent(request, decision)

    assert intent.side is OrderSide.SELL
    assert intent.quantity == 2.5
    assert intent.stop_price == 25100.0
    assert intent.target_price == 24800.0


def test_deny_risk_cannot_create_execution_intent() -> None:
    request = _request(max_loss_cash=5.0)
    decision = evaluate_fixed_cash_risk(request)
    assert decision.action is RiskDecisionAction.DENY

    with pytest.raises(ValueError, match="ALLOW risk"):
        _intent(request, decision)


def test_blocked_admission_cannot_create_execution_intent() -> None:
    request = _request()
    decision = evaluate_fixed_cash_risk(request)
    policy, observation, admission = _admission(open_positions=1)
    assert admission.allowed is False

    with pytest.raises(ValueError, match="ALLOW loss/exposure"):
        build_execution_intent_from_risk(
            request=request,
            decision=decision,
            admission_policy=policy,
            admission_observation=observation,
            admission_decision=admission,
            created_at=_created_at(),
        )


def test_request_identity_tampering_fails_closed() -> None:
    request = _request()
    decision = evaluate_fixed_cash_risk(request)
    tampered = replace(request, request_id="b" * 64)

    with pytest.raises(ValueError, match="request identity"):
        _intent(tampered, decision)


def test_risk_decision_quantity_tampering_fails_closed() -> None:
    request = _request()
    decision = evaluate_fixed_cash_risk(request)
    forged = replace(decision, quantity=9.9, decision_id="c" * 64)

    with pytest.raises(ValueError, match="canonical risk evaluation"):
        _intent(request, forged)


def test_risk_decision_from_other_request_fails_closed() -> None:
    request = _request(max_loss_cash=257.0)
    other_request = _request(max_loss_cash=300.0)
    other_decision = evaluate_fixed_cash_risk(other_request)

    with pytest.raises(ValueError, match="canonical risk evaluation"):
        _intent(request, other_decision)


def test_admission_decision_tampering_fails_closed() -> None:
    request = _request()
    decision = evaluate_fixed_cash_risk(request)
    policy, observation, admission = _admission()
    forged = replace(admission, decision_fingerprint="d" * 64)

    with pytest.raises(ValueError, match="canonical admission evaluation"):
        build_execution_intent_from_risk(
            request=request,
            decision=decision,
            admission_policy=policy,
            admission_observation=observation,
            admission_decision=forged,
            created_at=_created_at(),
        )


def test_admission_evidence_changes_intent_provenance() -> None:
    request = _request()
    decision = evaluate_fixed_cash_risk(request)
    first = _intent(request, decision)

    policy = LossExposurePolicy.build(
        currency="EUR",
        daily_drawdown_cap_cash=100.0,
        weekly_drawdown_cap_cash=250.0,
        max_consecutive_losses=3,
        max_open_positions=2,
    )
    observation = LossExposureObservation.build(
        currency="EUR",
        daily_drawdown_cash=11.0,
        weekly_drawdown_cash=20.0,
        consecutive_losses=0,
        open_positions=0,
    )
    admission = evaluate_loss_exposure_admission(
        policy=policy,
        observation=observation,
    )
    second = build_execution_intent_from_risk(
        request=request,
        decision=decision,
        admission_policy=policy,
        admission_observation=observation,
        admission_decision=admission,
        created_at=_created_at(),
    )

    assert first.provenance_fingerprint != second.provenance_fingerprint


def test_bridge_adds_no_broker_or_authorization_capability() -> None:
    request = _request()
    decision = evaluate_fixed_cash_risk(request)
    intent = _intent(request, decision)

    assert not hasattr(intent, "broker")
    assert not hasattr(intent, "order_execution_enabled")
    assert not hasattr(intent, "paper_authorized")
    assert not hasattr(intent, "live_authorized")
