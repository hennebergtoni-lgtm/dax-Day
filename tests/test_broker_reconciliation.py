from __future__ import annotations

from datetime import datetime, timedelta, timezone

from daxlab.runtime.broker_order_lifecycle import (
    BrokerOrderState,
    apply_order_event,
    begin_order_lifecycle,
)
from daxlab.runtime.broker_reconciliation import (
    BrokerReconciliationStatus,
    VENUE_ORDER_OBSERVATION_SCHEMA,
    VenueOrderObservation,
    reconcile_broker_order,
)
from daxlab.runtime.paper_contracts import ExecutionIntent, Side


UTC = timezone.utc
T0 = datetime(2026, 9, 11, 9, 15, tzinfo=UTC)


def _intent(*, quantity: float = 2.0) -> ExecutionIntent:
    return ExecutionIntent.build(
        decision_id="3" * 64,
        run_manifest_fingerprint="4" * 64,
        created_at=T0,
        symbol="DE40",
        side=Side.BUY,
        quantity=quantity,
        requested_price=24000.0,
        stop_price=23980.0,
        target_price=24030.0,
    )


def _acked_local():
    lifecycle, _ = begin_order_lifecycle(intent=_intent(), requested_at=T0)
    lifecycle, _ = apply_order_event(
        lifecycle=lifecycle,
        state=BrokerOrderState.ACK,
        venue_event_time=T0 + timedelta(seconds=1),
        venue_order_id="venue-42",
    )
    return lifecycle


def _venue_for(local, *, observed_at: datetime | None = None, **changes):
    values = {
        "schema_version": VENUE_ORDER_OBSERVATION_SCHEMA,
        "observed_at": observed_at or T0 + timedelta(seconds=2),
        "client_order_id": local.client_order_id,
        "venue_order_id": local.venue_order_id,
        "venue_state": local.state.value,
        "requested_quantity": local.requested_quantity,
        "cumulative_filled_quantity": local.cumulative_filled_quantity,
        "average_fill_price": local.average_fill_price,
    }
    values.update(changes)
    return VenueOrderObservation(**values)


def test_exact_normalized_venue_truth_is_consistent_and_execution_disabled() -> None:
    local = _acked_local()
    venue = _venue_for(local)
    verdict = reconcile_broker_order(local=local, venue=venue)

    assert verdict.status is BrokerReconciliationStatus.CONSISTENT
    assert verdict.consistent is True
    assert verdict.blockers == ()
    assert verdict.reconciled_client_order_id == local.client_order_id
    assert verdict.local_lifecycle_fingerprint == local.fingerprint
    assert verdict.venue_observation_fingerprint == venue.fingerprint
    assert verdict.execution_capability == "NONE"
    assert verdict.order_execution_enabled is False


def test_missing_local_or_venue_evidence_fails_closed() -> None:
    local = _acked_local()
    venue = _venue_for(local)

    missing_venue = reconcile_broker_order(local=local, venue=None)
    assert missing_venue.consistent is False
    assert missing_venue.blockers == ("VENUE_ORDER_EVIDENCE_MISSING",)

    missing_local = reconcile_broker_order(local=None, venue=venue)
    assert missing_local.consistent is False
    assert missing_local.blockers == ("LOCAL_ORDER_EVIDENCE_MISSING",)

    both_missing = reconcile_broker_order(local=None, venue=None)
    assert both_missing.blockers == (
        "LOCAL_ORDER_EVIDENCE_MISSING",
        "VENUE_ORDER_EVIDENCE_MISSING",
    )


def test_unknown_venue_state_fails_closed() -> None:
    local = _acked_local()
    venue = _venue_for(local, venue_state="BROKER_MAGIC_STATE")
    verdict = reconcile_broker_order(local=local, venue=venue)
    assert verdict.status is BrokerReconciliationStatus.BLOCKED
    assert "UNKNOWN_VENUE_STATE" in verdict.blockers


def test_identity_state_and_quantity_drift_are_all_visible() -> None:
    local = _acked_local()
    venue = _venue_for(
        local,
        client_order_id="different-client-id",
        venue_order_id="different-venue-id",
        venue_state=BrokerOrderState.REQUESTED.value,
        requested_quantity=3.0,
    )
    verdict = reconcile_broker_order(local=local, venue=venue)
    assert set(verdict.blockers) == {
        "CLIENT_ORDER_ID_MISMATCH",
        "ORDER_STATE_MISMATCH",
        "REQUESTED_QUANTITY_MISMATCH",
        "VENUE_ORDER_ID_MISMATCH",
    }
    assert verdict.reconciled_client_order_id is None


def test_fill_drift_is_blocked() -> None:
    local, _ = begin_order_lifecycle(intent=_intent(), requested_at=T0)
    local, _ = apply_order_event(
        lifecycle=local,
        state=BrokerOrderState.PARTIAL,
        venue_event_time=T0 + timedelta(seconds=1),
        cumulative_filled_quantity=0.5,
        last_fill_price=24001.0,
        venue_order_id="venue-42",
    )
    venue = _venue_for(
        local,
        cumulative_filled_quantity=0.75,
        average_fill_price=24002.0,
    )
    verdict = reconcile_broker_order(local=local, venue=venue)
    assert "CUMULATIVE_FILL_MISMATCH" in verdict.blockers
    assert "AVERAGE_FILL_PRICE_MISMATCH" in verdict.blockers


def test_observation_that_predates_local_event_is_blocked() -> None:
    local = _acked_local()
    venue = _venue_for(local, observed_at=T0)
    verdict = reconcile_broker_order(local=local, venue=venue)
    assert verdict.blockers == ("VENUE_OBSERVATION_PRECEDES_LOCAL_EVENT",)


def test_venue_truth_fingerprint_excludes_transport_observation_time() -> None:
    local = _acked_local()
    early = _venue_for(local, observed_at=T0 + timedelta(seconds=2))
    later = _venue_for(local, observed_at=T0 + timedelta(minutes=5))

    assert early != later
    assert early.fingerprint == later.fingerprint
    assert reconcile_broker_order(local=local, venue=early).fingerprint == (
        reconcile_broker_order(local=local, venue=later).fingerprint
    )


def test_reconciliation_does_not_mutate_local_lifecycle() -> None:
    local = _acked_local()
    before = local.fingerprint
    reconcile_broker_order(local=local, venue=_venue_for(local))
    assert local.fingerprint == before
