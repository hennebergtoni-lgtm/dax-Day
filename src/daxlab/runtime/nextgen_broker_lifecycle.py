"""Compatibility entry from canonical NextGen intent into the existing broker lifecycle.

This module adds no lifecycle vocabulary and no venue capability. It binds a
canonical domain ExecutionIntent to the already-owned broker-neutral lifecycle
state machine while preserving the canonical intent_id as client_order_id.
"""

from __future__ import annotations

from datetime import datetime
from hashlib import sha256
import json

from daxlab.domain.execution import ExecutionIntent
from daxlab.runtime.broker_order_lifecycle import (
    BROKER_ORDER_LIFECYCLE_SCHEMA,
    BrokerOrderEvent,
    BrokerOrderLifecycle,
    BrokerOrderState,
    _build_event,
)


def begin_nextgen_order_lifecycle(
    *,
    intent: ExecutionIntent,
    requested_at: datetime,
) -> tuple[BrokerOrderLifecycle, BrokerOrderEvent]:
    """Create REQUESTED lifecycle evidence for canonical intent; submit nothing."""

    if requested_at.tzinfo is None:
        raise ValueError("requested_at must be timezone-aware")
    if requested_at < intent.created_at:
        raise ValueError("requested_at cannot precede intent.created_at")

    intent_fingerprint = _canonical_intent_fingerprint(intent)
    event = _build_event(
        client_order_id=intent.intent_id,
        intent_fingerprint=intent_fingerprint,
        sequence=0,
        previous_state=None,
        state=BrokerOrderState.REQUESTED,
        venue_event_time=requested_at,
        cumulative_filled_quantity=0.0,
        last_fill_quantity=0.0,
        last_fill_price=None,
        venue_order_id=None,
        reason=None,
    )
    lifecycle = BrokerOrderLifecycle(
        schema_version=BROKER_ORDER_LIFECYCLE_SCHEMA,
        client_order_id=intent.intent_id,
        intent_fingerprint=intent_fingerprint,
        requested_quantity=float(intent.quantity),
        state=BrokerOrderState.REQUESTED,
        cumulative_filled_quantity=0.0,
        average_fill_price=None,
        venue_order_id=None,
        last_event_time=requested_at,
        last_event_fingerprint=event.event_fingerprint,
        event_count=1,
    )
    return lifecycle, event


def _canonical_intent_fingerprint(intent: ExecutionIntent) -> str:
    return _fingerprint(
        {
            "schema_version": intent.schema_version,
            "decision_id": intent.decision_id,
            "provenance_fingerprint": intent.provenance_fingerprint,
            "created_at": intent.created_at.isoformat(),
            "instrument_id": intent.instrument_id.value,
            "side": intent.side.value,
            "quantity": float(intent.quantity),
            "requested_price": float(intent.requested_price),
            "stop_price": float(intent.stop_price),
            "target_price": float(intent.target_price),
            "intent_id": intent.intent_id,
        }
    )


def _fingerprint(payload: object) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256(canonical.encode("utf-8")).hexdigest()
