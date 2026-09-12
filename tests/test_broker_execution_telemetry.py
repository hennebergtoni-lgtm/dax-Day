from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

import pytest

from daxlab.runtime.broker_execution_protection import evaluate_execution_protection
from daxlab.runtime.broker_execution_telemetry import (
    BrokerExecutionTelemetryKind,
    telemetry_from_order_event,
    telemetry_from_protection,
    telemetry_from_reconciliation,
)
from daxlab.runtime.broker_order_lifecycle import (
    BrokerOrderState,
    apply_order_event,
    begin_order_lifecycle,
)
from daxlab.runtime.broker_reconciliation import (
    VENUE_ORDER_OBSERVATION_SCHEMA,
    VenueOrderObservation,
    reconcile_broker_order,
)
from daxlab.runtime.paper_contracts import ExecutionIntent, Side


UTC = timezone.utc
DECISION_ID = "1" * 64
RUN_FP = "2" * 64
SIZING_FP = "3" * 64
RISK_FP = "4" * 64


def _intent() -> ExecutionIntent:
    return ExecutionIntent.build(
        decision_id=DECISION_ID,
        run_manifest_fingerprint=RUN_FP,
        created_at=datetime(2026, 9, 11, 9, 5, tzinfo=UTC),
        symbol="DE40",
        side=Side.BUY,
        quantity=1.0,
        requested_price=23000.0,
        stop_price=22990.0,
        target_price=23015.0,
    )


def _requested():
    return begin_order_lifecycle(
        intent=_intent(),
        requested_at=datetime(2026, 9, 11, 9, 6, tzinfo=UTC),
    )


def _consistent_reconciliation():
    lifecycle, _ = _requested()
    venue = VenueOrderObservation(
        schema_version=VENUE_ORDER_OBSERVATION_SCHEMA,
        observed_at=datetime(2026, 9, 11, 9, 6, 1, tzinfo=UTC),
        client_order_id=lifecycle.client_order_id,
        venue_order_id=None,
        venue_state="REQUESTED",
        requested_quantity=1.0,
        cumulative_filled_quantity=0.0,
        average_fill_price=None,
    )
    return reconcile_broker_order(local=lifecycle, venue=venue), venue.observed_at


def _protection(**changes):
    values = {
        "client_order_id": _intent().client_order_id,
        "host_health_green": True,
        "broker_account_trade_allowed": True,
        "feed_age_seconds": 1.0,
        "max_feed_age_seconds": 10.0,
        "observed_spread_points": 0.2,
        "max_spread_points": 0.5,
        "reconciliation_inventory_complete": True,
        "reconciliations": (),
        "duplicate_client_order_id": False,
        "sizing_allowed": True,
        "sizing_evidence_fingerprint": SIZING_FP,
        "loss_cap_allowed": True,
        "risk_policy_fingerprint": RISK_FP,
        "session_admission_allowed": True,
    }
    values.update(changes)
    return evaluate_execution_protection(**values)


def test_requested_event_becomes_deterministic_non_executable_telemetry() -> None:
    _, event = _requested()
    record = telemetry_from_order_event(event)
    replay = telemetry_from_order_event(event)

    assert record.kind is BrokerExecutionTelemetryKind.ORDER_EVENT
    assert record.client_order_id == event.client_order_id
    assert record.source_fingerprint == event.event_fingerprint
    assert record.intent_fingerprint == event.intent_fingerprint
    assert record.lifecycle_state == "REQUESTED"
    assert record.source_sequence == 0
    assert record.reason_code is None
    assert record.telemetry_fingerprint == replay.telemetry_fingerprint
    assert record.execution_capability == "NONE"
    assert record.order_execution_enabled is False
    json.dumps(record.as_dict(), sort_keys=True)


def test_partial_and_fill_events_preserve_fill_evidence() -> None:
    lifecycle, _ = _requested()
    lifecycle, _ = apply_order_event(
        lifecycle=lifecycle,
        state=BrokerOrderState.ACK,
        venue_event_time=lifecycle.last_event_time + timedelta(seconds=1),
        venue_order_id="venue-123",
    )
    lifecycle, partial = apply_order_event(
        lifecycle=lifecycle,
        state=BrokerOrderState.PARTIAL,
        venue_event_time=lifecycle.last_event_time + timedelta(seconds=1),
        cumulative_filled_quantity=0.4,
        last_fill_price=23000.5,
    )
    lifecycle, filled = apply_order_event(
        lifecycle=lifecycle,
        state=BrokerOrderState.FILLED,
        venue_event_time=lifecycle.last_event_time + timedelta(seconds=1),
        cumulative_filled_quantity=1.0,
        last_fill_price=23001.0,
    )

    partial_record = telemetry_from_order_event(partial)
    filled_record = telemetry_from_order_event(filled)
    assert partial_record.lifecycle_state == "PARTIAL"
    assert partial_record.cumulative_filled_quantity == 0.4
    assert partial_record.last_fill_quantity == 0.4
    assert partial_record.last_fill_price == 23000.5
    assert partial_record.venue_order_id == "venue-123"
    assert filled_record.lifecycle_state == "FILLED"
    assert filled_record.cumulative_filled_quantity == 1.0
    assert filled_record.last_fill_quantity == pytest.approx(0.6)
    assert filled_record.venue_order_id == "venue-123"


def test_normalized_reject_reason_is_retained_but_free_text_is_rejected() -> None:
    lifecycle, _ = _requested()
    _, rejected = apply_order_event(
        lifecycle=lifecycle,
        state=BrokerOrderState.REJECT,
        venue_event_time=lifecycle.last_event_time + timedelta(seconds=1),
        reason="VENUE_REJECTED",
    )
    record = telemetry_from_order_event(rejected)
    assert record.reason_code == "VENUE_REJECTED"
    assert record.blockers == ()

    lifecycle, _ = _requested()
    _, unsafe = apply_order_event(
        lifecycle=lifecycle,
        state=BrokerOrderState.REJECT,
        venue_event_time=lifecycle.last_event_time + timedelta(seconds=1),
        reason="password=do-not-export",
    )
    with pytest.raises(ValueError, match="credential-free code"):
        telemetry_from_order_event(unsafe)


def test_reconciliation_telemetry_records_consistent_and_blocked_truth() -> None:
    consistent, observed_at = _consistent_reconciliation()
    record = telemetry_from_reconciliation(consistent, observed_at=observed_at)
    assert record.kind is BrokerExecutionTelemetryKind.RECONCILIATION
    assert record.reconciliation_status == "CONSISTENT"
    assert record.blockers == ()
    assert record.source_fingerprint == consistent.fingerprint
    assert record.execution_capability == "NONE"

    blocked = reconcile_broker_order(local=None, venue=None)
    blocked_record = telemetry_from_reconciliation(
        blocked,
        observed_at=datetime(2026, 9, 11, 9, 7, tzinfo=UTC),
    )
    assert blocked_record.reconciliation_status == "BLOCKED"
    assert blocked_record.client_order_id is None
    assert blocked_record.blockers == (
        "LOCAL_ORDER_EVIDENCE_MISSING",
        "VENUE_ORDER_EVIDENCE_MISSING",
    )


def test_protection_telemetry_preserves_allow_and_block_evidence_only() -> None:
    allowed = _protection()
    allowed_record = telemetry_from_protection(
        allowed,
        evaluated_at=datetime(2026, 9, 11, 9, 8, tzinfo=UTC),
    )
    assert allowed_record.kind is BrokerExecutionTelemetryKind.PROTECTION
    assert allowed_record.protection_status == "ALLOW_EVIDENCE"
    assert allowed_record.feed_age_seconds == 1.0
    assert allowed_record.observed_spread_points == 0.2
    assert allowed_record.sizing_evidence_fingerprint == SIZING_FP
    assert allowed_record.risk_policy_fingerprint == RISK_FP
    assert allowed_record.execution_capability == "NONE"
    assert allowed_record.order_execution_enabled is False

    blocked = _protection(feed_age_seconds=11.0)
    blocked_record = telemetry_from_protection(
        blocked,
        evaluated_at=datetime(2026, 9, 11, 9, 8, 1, tzinfo=UTC),
    )
    assert blocked_record.protection_status == "BLOCKED"
    assert "STALE_FEED" in blocked_record.blockers


def test_naive_telemetry_event_times_fail_closed() -> None:
    verdict, _ = _consistent_reconciliation()
    with pytest.raises(ValueError, match="timezone-aware"):
        telemetry_from_reconciliation(verdict, observed_at=datetime(2026, 9, 11, 9, 9))
    with pytest.raises(ValueError, match="timezone-aware"):
        telemetry_from_protection(_protection(), evaluated_at=datetime(2026, 9, 11, 9, 9))


def test_telemetry_fingerprint_tampering_fails_closed() -> None:
    _, event = _requested()
    record = telemetry_from_order_event(event)
    with pytest.raises(ValueError, match="fingerprint mismatch"):
        replace(record, telemetry_fingerprint="0" * 64)


def test_telemetry_owner_contains_no_broker_submission_api() -> None:
    root = Path(__file__).resolve().parents[1]
    source = (
        root / "src/daxlab/runtime/broker_execution_telemetry.py"
    ).read_text(encoding="utf-8")
    assert "order_send(" not in source
    assert "import MetaTrader5" not in source
