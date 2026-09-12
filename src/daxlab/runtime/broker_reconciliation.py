"""Broker-neutral reconciliation over plain order-state evidence.

This module compares one local broker-order lifecycle snapshot with one plain
venue observation. It performs no broker query, no state mutation, no repair and
no order submission. Exact normalized agreement is the only consistent result;
all missing, unknown or contradictory evidence fails closed.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from hashlib import sha256
import json
from typing import Any

from daxlab.runtime.broker_order_lifecycle import (
    BrokerOrderLifecycle,
    BrokerOrderState,
)


VENUE_ORDER_OBSERVATION_SCHEMA = "DAXLAB_VENUE_ORDER_OBSERVATION_V1"
BROKER_RECONCILIATION_SCHEMA = "DAXLAB_BROKER_RECONCILIATION_V1"


class BrokerReconciliationStatus(StrEnum):
    CONSISTENT = "CONSISTENT"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True, slots=True)
class VenueOrderObservation:
    """Credential-free normalized venue truth supplied by a future adapter."""

    schema_version: str
    observed_at: datetime
    client_order_id: str
    venue_order_id: str | None
    venue_state: str
    requested_quantity: float
    cumulative_filled_quantity: float
    average_fill_price: float | None
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != VENUE_ORDER_OBSERVATION_SCHEMA:
            raise ValueError("venue order observation schema mismatch")
        if self.observed_at.tzinfo is None:
            raise ValueError("observed_at must be timezone-aware")
        if not self.client_order_id:
            raise ValueError("client_order_id must be non-empty")
        if not isinstance(self.venue_state, str) or not self.venue_state.strip():
            raise ValueError("venue_state must be non-empty")
        if self.requested_quantity <= 0:
            raise ValueError("requested_quantity must be positive")
        if self.cumulative_filled_quantity < 0:
            raise ValueError("cumulative_filled_quantity must be non-negative")
        if self.cumulative_filled_quantity > self.requested_quantity:
            raise ValueError("venue cumulative fill cannot exceed requested quantity")
        if self.average_fill_price is not None and self.average_fill_price <= 0:
            raise ValueError("average_fill_price must be positive when supplied")
        if self.cumulative_filled_quantity > 0 and self.average_fill_price is None:
            raise ValueError("positive venue fill requires average_fill_price")
        if self.cumulative_filled_quantity == 0 and self.average_fill_price is not None:
            raise ValueError("zero venue fill cannot carry average_fill_price")
        if self.execution_capability != "NONE" or self.order_execution_enabled:
            raise ValueError("venue observation cannot authorize execution")

    @property
    def fingerprint(self) -> str:
        """Fingerprint venue truth, intentionally excluding transport observed_at."""
        return _fingerprint(
            {
                "schema_version": self.schema_version,
                "client_order_id": self.client_order_id,
                "venue_order_id": self.venue_order_id,
                "venue_state": self.venue_state,
                "requested_quantity": float(self.requested_quantity),
                "cumulative_filled_quantity": float(self.cumulative_filled_quantity),
                "average_fill_price": (
                    None
                    if self.average_fill_price is None
                    else float(self.average_fill_price)
                ),
                "execution_capability": self.execution_capability,
                "order_execution_enabled": self.order_execution_enabled,
            }
        )


@dataclass(frozen=True, slots=True)
class BrokerReconciliationVerdict:
    schema_version: str
    status: BrokerReconciliationStatus
    blockers: tuple[str, ...]
    local_lifecycle_fingerprint: str | None
    venue_observation_fingerprint: str | None
    reconciled_client_order_id: str | None
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != BROKER_RECONCILIATION_SCHEMA:
            raise ValueError("broker reconciliation schema mismatch")
        if self.execution_capability != "NONE" or self.order_execution_enabled:
            raise ValueError("broker reconciliation cannot authorize execution")
        if self.status is BrokerReconciliationStatus.CONSISTENT and self.blockers:
            raise ValueError("consistent reconciliation cannot carry blockers")
        if self.status is BrokerReconciliationStatus.BLOCKED and not self.blockers:
            raise ValueError("blocked reconciliation requires blockers")

    @property
    def consistent(self) -> bool:
        return self.status is BrokerReconciliationStatus.CONSISTENT

    @property
    def fingerprint(self) -> str:
        return _fingerprint(
            {
                "schema_version": self.schema_version,
                "status": self.status.value,
                "blockers": list(self.blockers),
                "local_lifecycle_fingerprint": self.local_lifecycle_fingerprint,
                "venue_observation_fingerprint": self.venue_observation_fingerprint,
                "reconciled_client_order_id": self.reconciled_client_order_id,
                "execution_capability": self.execution_capability,
                "order_execution_enabled": self.order_execution_enabled,
            }
        )


def reconcile_broker_order(
    *,
    local: BrokerOrderLifecycle | None,
    venue: VenueOrderObservation | None,
) -> BrokerReconciliationVerdict:
    """Compare local and venue truth without mutating either side."""
    blockers: list[str] = []
    if local is None:
        blockers.append("LOCAL_ORDER_EVIDENCE_MISSING")
    if venue is None:
        blockers.append("VENUE_ORDER_EVIDENCE_MISSING")
    if local is None or venue is None:
        return _verdict(local=local, venue=venue, blockers=blockers)

    if venue.client_order_id != local.client_order_id:
        blockers.append("CLIENT_ORDER_ID_MISMATCH")

    try:
        venue_state = BrokerOrderState(venue.venue_state)
    except ValueError:
        venue_state = None
        blockers.append("UNKNOWN_VENUE_STATE")

    if venue_state is not None and venue_state is not local.state:
        blockers.append("ORDER_STATE_MISMATCH")

    if venue.requested_quantity != local.requested_quantity:
        blockers.append("REQUESTED_QUANTITY_MISMATCH")
    if venue.cumulative_filled_quantity != local.cumulative_filled_quantity:
        blockers.append("CUMULATIVE_FILL_MISMATCH")
    if venue.average_fill_price != local.average_fill_price:
        blockers.append("AVERAGE_FILL_PRICE_MISMATCH")

    if local.venue_order_id is None:
        if venue.venue_order_id is not None:
            blockers.append("VENUE_ORDER_ID_UNEXPECTED")
    elif venue.venue_order_id != local.venue_order_id:
        blockers.append("VENUE_ORDER_ID_MISMATCH")

    if venue.observed_at < local.last_event_time:
        blockers.append("VENUE_OBSERVATION_PRECEDES_LOCAL_EVENT")

    return _verdict(local=local, venue=venue, blockers=blockers)


def _verdict(
    *,
    local: BrokerOrderLifecycle | None,
    venue: VenueOrderObservation | None,
    blockers: list[str],
) -> BrokerReconciliationVerdict:
    unique = tuple(dict.fromkeys(blockers))
    status = (
        BrokerReconciliationStatus.CONSISTENT
        if not unique
        else BrokerReconciliationStatus.BLOCKED
    )
    client_order_id = None
    if local is not None and venue is not None and local.client_order_id == venue.client_order_id:
        client_order_id = local.client_order_id
    elif local is not None and venue is None:
        client_order_id = local.client_order_id
    elif venue is not None and local is None:
        client_order_id = venue.client_order_id

    return BrokerReconciliationVerdict(
        schema_version=BROKER_RECONCILIATION_SCHEMA,
        status=status,
        blockers=unique,
        local_lifecycle_fingerprint=None if local is None else local.fingerprint,
        venue_observation_fingerprint=None if venue is None else venue.fingerprint,
        reconciled_client_order_id=client_order_id,
    )


def _fingerprint(value: dict[str, Any]) -> str:
    canonical = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()
