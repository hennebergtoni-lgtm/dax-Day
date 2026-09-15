from __future__ import annotations

from datetime import datetime, timedelta, timezone

from daxlab.data.recovery import RecoveryIdentity
from daxlab.domain.execution import ExecutionIntent, OrderSide
from daxlab.domain.market import InstrumentId
from daxlab.runtime.broker_execution_protection import evaluate_execution_protection
from daxlab.runtime.broker_reconciliation import (
    VENUE_ORDER_OBSERVATION_SCHEMA,
    VenueOrderObservation,
    reconcile_broker_order,
)
from daxlab.runtime.nextgen_broker_lifecycle import begin_nextgen_order_lifecycle
from daxlab.runtime.readiness import ReadinessSnapshot, RunKind, evaluate_run_readiness


UTC = timezone.utc
T0 = datetime(2026, 9, 11, 8, 5, tzinfo=UTC)


def _intent() -> ExecutionIntent:
    return ExecutionIntent.build(
        decision_id="a" * 64,
        provenance_fingerprint="b" * 64,
        created_at=T0,
        instrument_id=InstrumentId("DAX40.CFD"),
        side=OrderSide.BUY,
        quantity=1.0,
        requested_price=25000.0,
        stop_price=24950.0,
        target_price=25100.0,
    )


def _ready_snapshot(*, paper_user_authorized: bool) -> ReadinessSnapshot:
    return ReadinessSnapshot(
        ci_green=True,
        dataset_verified=True,
        engine_verified=True,
        database_verified=True,
        technical_replay_verified=True,
        audited_bundle_available=True,
        full_reference_replay_verified=True,
        execution_boundary_verified=True,
        mt5_readonly_health_verified=True,
        dataset_identity=RecoveryIdentity.HASH_VERIFIED,
        broker_economics_verified=True,
        broker_risk_sizing_verified=True,
        risk_profile_policy_verified=True,
        loss_cap_policy_verified=True,
        broker_order_lifecycle_verified=True,
        broker_execution_checkpoint_verified=True,
        broker_reconciliation_verified=True,
        execution_protection_gates_verified=True,
        broker_order_telemetry_verified=True,
        paper_user_authorized=paper_user_authorized,
    )


def _protection(*, duplicate: bool = False):
    intent = _intent()
    lifecycle, _ = begin_nextgen_order_lifecycle(intent=intent, requested_at=T0)
    venue = VenueOrderObservation(
        schema_version=VENUE_ORDER_OBSERVATION_SCHEMA,
        observed_at=T0 + timedelta(seconds=1),
        client_order_id=lifecycle.client_order_id,
        venue_order_id=None,
        venue_state=lifecycle.state.value,
        requested_quantity=lifecycle.requested_quantity,
        cumulative_filled_quantity=0.0,
        average_fill_price=None,
    )
    reconciliation = reconcile_broker_order(local=lifecycle, venue=venue)
    protection = evaluate_execution_protection(
        client_order_id=lifecycle.client_order_id,
        host_health_green=True,
        broker_account_trade_allowed=True,
        feed_age_seconds=0.2,
        max_feed_age_seconds=5.0,
        observed_spread_points=1.0,
        max_spread_points=2.0,
        reconciliation_inventory_complete=True,
        reconciliations=(reconciliation,),
        duplicate_client_order_id=duplicate,
        sizing_allowed=True,
        sizing_evidence_fingerprint="c" * 64,
        loss_cap_allowed=True,
        risk_policy_fingerprint="d" * 64,
        session_admission_allowed=True,
    )
    return lifecycle, protection


def test_technical_protection_cannot_infer_paper_user_authorization() -> None:
    lifecycle, protection = _protection()
    readiness = evaluate_run_readiness(
        RunKind.PAPER,
        _ready_snapshot(paper_user_authorized=False),
    )

    assert protection.client_order_id == lifecycle.client_order_id == _intent().intent_id
    assert protection.allow_evidence is True
    assert readiness.allowed is False
    assert readiness.blockers == ("PAPER_USER_AUTHORIZATION_REQUIRED",)
    assert not (protection.allow_evidence and readiness.allowed)


def test_user_authorization_alone_cannot_override_blocked_protection() -> None:
    _, protection = _protection(duplicate=True)
    readiness = evaluate_run_readiness(
        RunKind.PAPER,
        _ready_snapshot(paper_user_authorized=True),
    )

    assert readiness.allowed is True
    assert protection.allow_evidence is False
    assert "DUPLICATE_CLIENT_ORDER_ID" in protection.blockers
    assert not (protection.allow_evidence and readiness.allowed)


def test_only_both_independent_evidence_surfaces_can_be_true_in_fixture() -> None:
    _, protection = _protection()
    readiness = evaluate_run_readiness(
        RunKind.PAPER,
        _ready_snapshot(paper_user_authorized=True),
    )

    assert protection.allow_evidence is True
    assert readiness.allowed is True
    assert protection.execution_capability == "NONE"
    assert protection.order_execution_enabled is False
