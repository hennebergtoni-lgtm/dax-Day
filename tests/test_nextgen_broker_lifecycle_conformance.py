from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from daxlab.domain.loss_admission import (
    LossExposureObservation,
    LossExposurePolicy,
    evaluate_loss_exposure_admission,
)
from daxlab.domain.market import InstrumentId
from daxlab.domain.risk import InstrumentRiskInputs, RiskRequest, evaluate_fixed_cash_risk
from daxlab.domain.risk_policy import FixedCashRiskPolicy
from daxlab.domain.risk_execution import build_execution_intent_from_risk
from daxlab.domain.strategy import TradeDirection, TradePlan
from daxlab.runtime.broker_execution_protection import (
    ExecutionProtectionStatus,
    evaluate_nextgen_execution_protection,
)
from daxlab.runtime.broker_order_lifecycle import BrokerOrderState, apply_order_event
from daxlab.runtime.broker_reconciliation import (
    BrokerReconciliationStatus,
    VenueOrderObservation,
    reconcile_broker_order,
)
from daxlab.runtime.nextgen_broker_lifecycle import begin_nextgen_order_lifecycle


UTC = timezone.utc
T0 = datetime(2026, 9, 11, 8, 5, tzinfo=UTC)


def _loss_evidence():
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
        open_positions=0,
    )
    decision = evaluate_loss_exposure_admission(
        policy=policy,
        observation=observation,
    )
    return policy, observation, decision


def _canonical_chain():
    plan = TradePlan(
        instrument_id=InstrumentId("DAX40.CFD"),
        direction=TradeDirection.LONG,
        entry_price=25000.0,
        stop_price=24900.0,
        target_price=25200.0,
    )
    request = RiskRequest.build(
        strategy_decision_id="a" * 64,
        trade_plan=plan,
        max_loss_cash=257.0,
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
    decision = evaluate_fixed_cash_risk(request)
    admission_policy, admission_observation, admission_decision = _loss_evidence()
    intent = build_execution_intent_from_risk(
        request=request,
        decision=decision,
        admission_policy=admission_policy,
        admission_observation=admission_observation,
        admission_decision=admission_decision,
        created_at=T0,
    )
    return request, decision, intent


def test_canonical_intent_enters_existing_lifecycle_deterministically() -> None:
    _, _, intent = _canonical_chain()

    first, first_event = begin_nextgen_order_lifecycle(
        intent=intent,
        requested_at=T0 + timedelta(seconds=1),
    )
    second, second_event = begin_nextgen_order_lifecycle(
        intent=intent,
        requested_at=T0 + timedelta(seconds=1),
    )

    assert first == second
    assert first_event == second_event
    assert first.client_order_id == intent.intent_id
    assert first.requested_quantity == intent.quantity
    assert first.state is BrokerOrderState.REQUESTED
    assert first.execution_capability == "NONE"
    assert first.order_execution_enabled is False
    assert first_event.execution_capability == "NONE"
    assert first_event.order_execution_enabled is False


def test_existing_lifecycle_vocabulary_handles_ack_partial_filled() -> None:
    _, _, intent = _canonical_chain()
    lifecycle, _ = begin_nextgen_order_lifecycle(intent=intent, requested_at=T0)

    lifecycle, _ = apply_order_event(
        lifecycle=lifecycle,
        state=BrokerOrderState.ACK,
        venue_event_time=T0 + timedelta(seconds=1),
        venue_order_id="venue-nextgen-1",
    )
    lifecycle, _ = apply_order_event(
        lifecycle=lifecycle,
        state=BrokerOrderState.PARTIAL,
        venue_event_time=T0 + timedelta(seconds=2),
        cumulative_filled_quantity=1.0,
        last_fill_price=25000.5,
        venue_order_id="venue-nextgen-1",
    )
    lifecycle, _ = apply_order_event(
        lifecycle=lifecycle,
        state=BrokerOrderState.FILLED,
        venue_event_time=T0 + timedelta(seconds=3),
        cumulative_filled_quantity=intent.quantity,
        last_fill_price=25001.0,
        venue_order_id="venue-nextgen-1",
    )

    assert lifecycle.state is BrokerOrderState.FILLED
    assert lifecycle.terminal is True
    assert lifecycle.cumulative_filled_quantity == intent.quantity


def test_matching_synthetic_venue_truth_reconciles_consistently() -> None:
    _, _, intent = _canonical_chain()
    lifecycle, _ = begin_nextgen_order_lifecycle(intent=intent, requested_at=T0)
    lifecycle, _ = apply_order_event(
        lifecycle=lifecycle,
        state=BrokerOrderState.FILLED,
        venue_event_time=T0 + timedelta(seconds=1),
        cumulative_filled_quantity=intent.quantity,
        last_fill_price=25000.5,
        venue_order_id="venue-nextgen-2",
    )
    venue = VenueOrderObservation(
        schema_version="DAXLAB_VENUE_ORDER_OBSERVATION_V1",
        observed_at=T0 + timedelta(seconds=2),
        client_order_id=lifecycle.client_order_id,
        venue_order_id=lifecycle.venue_order_id,
        venue_state=lifecycle.state.value,
        requested_quantity=lifecycle.requested_quantity,
        cumulative_filled_quantity=lifecycle.cumulative_filled_quantity,
        average_fill_price=lifecycle.average_fill_price,
    )

    verdict = reconcile_broker_order(local=lifecycle, venue=venue)

    assert verdict.status is BrokerReconciliationStatus.CONSISTENT
    assert verdict.consistent is True
    assert verdict.blockers == ()
    assert verdict.execution_capability == "NONE"
    assert verdict.order_execution_enabled is False


def test_contradictory_synthetic_venue_truth_fails_closed() -> None:
    _, _, intent = _canonical_chain()
    lifecycle, _ = begin_nextgen_order_lifecycle(intent=intent, requested_at=T0)
    lifecycle, _ = apply_order_event(
        lifecycle=lifecycle,
        state=BrokerOrderState.ACK,
        venue_event_time=T0 + timedelta(seconds=1),
        venue_order_id="venue-nextgen-3",
    )
    venue = VenueOrderObservation(
        schema_version="DAXLAB_VENUE_ORDER_OBSERVATION_V1",
        observed_at=T0 + timedelta(seconds=2),
        client_order_id=lifecycle.client_order_id,
        venue_order_id=lifecycle.venue_order_id,
        venue_state=BrokerOrderState.FILLED.value,
        requested_quantity=lifecycle.requested_quantity,
        cumulative_filled_quantity=lifecycle.requested_quantity,
        average_fill_price=25000.5,
    )

    verdict = reconcile_broker_order(local=lifecycle, venue=venue)

    assert verdict.status is BrokerReconciliationStatus.BLOCKED
    assert verdict.consistent is False
    assert "ORDER_STATE_MISMATCH" in verdict.blockers
    assert "CUMULATIVE_FILL_MISMATCH" in verdict.blockers


def test_existing_protection_owner_accepts_only_complete_synthetic_evidence() -> None:
    request, decision, intent = _canonical_chain()
    lifecycle, _ = begin_nextgen_order_lifecycle(intent=intent, requested_at=T0)
    lifecycle, _ = apply_order_event(
        lifecycle=lifecycle,
        state=BrokerOrderState.FILLED,
        venue_event_time=T0 + timedelta(seconds=1),
        cumulative_filled_quantity=intent.quantity,
        last_fill_price=25000.5,
        venue_order_id="venue-nextgen-4",
    )
    venue = VenueOrderObservation(
        schema_version="DAXLAB_VENUE_ORDER_OBSERVATION_V1",
        observed_at=T0 + timedelta(seconds=2),
        client_order_id=lifecycle.client_order_id,
        venue_order_id=lifecycle.venue_order_id,
        venue_state=lifecycle.state.value,
        requested_quantity=lifecycle.requested_quantity,
        cumulative_filled_quantity=lifecycle.cumulative_filled_quantity,
        average_fill_price=lifecycle.average_fill_price,
    )
    reconciliation = reconcile_broker_order(local=lifecycle, venue=venue)
    risk_policy = FixedCashRiskPolicy.build(
        currency=request.loss_currency,
        max_loss_cash=request.max_loss_cash,
    )
    loss_policy, loss_observation, loss_decision = _loss_evidence()

    protection = evaluate_nextgen_execution_protection(
        client_order_id=lifecycle.client_order_id,
        host_health_green=True,
        broker_account_trade_allowed=True,
        feed_age_seconds=0.2,
        max_feed_age_seconds=5.0,
        observed_spread_points=1.0,
        max_spread_points=2.0,
        reconciliation_inventory_complete=True,
        reconciliations=(reconciliation,),
        duplicate_client_order_id=False,
        risk_policy=risk_policy,
        risk_request=request,
        risk_decision=decision,
        loss_policy=loss_policy,
        loss_observation=loss_observation,
        loss_admission_decision=loss_decision,
        session_admission_allowed=True,
    )

    assert protection.status is ExecutionProtectionStatus.ALLOW_EVIDENCE
    assert protection.allow_evidence is True
    assert protection.blockers == ()
    assert protection.sizing_evidence_fingerprint == decision.decision_id
    assert protection.risk_policy_fingerprint == risk_policy.policy_fingerprint
    assert (
        protection.loss_admission_evidence_fingerprint
        == loss_decision.decision_fingerprint
    )
    assert protection.execution_capability == "NONE"
    assert protection.order_execution_enabled is False


def test_nextgen_lifecycle_bridge_has_no_venue_submission_dependency() -> None:
    path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "daxlab"
        / "runtime"
        / "nextgen_broker_lifecycle.py"
    )
    source = path.read_text(encoding="utf-8").lower()
    assert "metatrader5" not in source
    assert "order_send" not in source
