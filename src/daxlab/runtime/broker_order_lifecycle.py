"""Broker-neutral order-lifecycle evidence with no venue API or submission capability.

The owner in this module starts from an existing :class:`ExecutionIntent` and
validates deterministic lifecycle transitions over plain venue observations.
It deliberately has no MetaTrader5 import, no broker adapter and no order-send
function. Its outputs are evidence objects only and keep execution disabled.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from hashlib import sha256
import json
from typing import Any, Mapping

from daxlab.runtime.paper_contracts import ExecutionIntent, PaperLifecycleState


BROKER_ORDER_LIFECYCLE_SCHEMA = "DAXLAB_BROKER_ORDER_LIFECYCLE_V1"
BROKER_ORDER_EVENT_SCHEMA = "DAXLAB_BROKER_ORDER_EVENT_V1"
BROKER_ORDER_LIFECYCLE_STATE_SCHEMA = "DAXLAB_BROKER_ORDER_LIFECYCLE_STATE_V1"
_LIFECYCLE_STATE_FIELDS = {
    "state_schema_version",
    "lifecycle_schema_version",
    "client_order_id",
    "intent_fingerprint",
    "requested_quantity",
    "state",
    "cumulative_filled_quantity",
    "average_fill_price",
    "venue_order_id",
    "last_event_time",
    "last_event_fingerprint",
    "event_count",
    "execution_capability",
    "order_execution_enabled",
    "lifecycle_fingerprint",
    "payload_fingerprint",
}


class BrokerOrderState(StrEnum):
    """Order states; existing paper vocabulary is reused where it matches."""

    REQUESTED = "REQUESTED"
    ACK = PaperLifecycleState.ACK.value
    REJECT = PaperLifecycleState.REJECT.value
    PARTIAL = PaperLifecycleState.PARTIAL.value
    FILLED = PaperLifecycleState.FILLED.value
    CANCELLED = PaperLifecycleState.CANCELLED.value
    EXPIRED = "EXPIRED"


_TERMINAL = {
    BrokerOrderState.REJECT,
    BrokerOrderState.FILLED,
    BrokerOrderState.CANCELLED,
    BrokerOrderState.EXPIRED,
}
_ALLOWED_NEXT = {
    BrokerOrderState.REQUESTED: {
        BrokerOrderState.ACK,
        BrokerOrderState.REJECT,
        BrokerOrderState.PARTIAL,
        BrokerOrderState.FILLED,
        BrokerOrderState.CANCELLED,
        BrokerOrderState.EXPIRED,
    },
    BrokerOrderState.ACK: {
        BrokerOrderState.PARTIAL,
        BrokerOrderState.FILLED,
        BrokerOrderState.CANCELLED,
        BrokerOrderState.EXPIRED,
    },
    BrokerOrderState.PARTIAL: {
        BrokerOrderState.PARTIAL,
        BrokerOrderState.FILLED,
        BrokerOrderState.CANCELLED,
        BrokerOrderState.EXPIRED,
    },
}


def _canonical(value: Mapping[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _fingerprint(value: Mapping[str, Any]) -> str:
    return sha256(_canonical(value).encode("utf-8")).hexdigest()


def _sha(value: Any, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{field} must be sha256 hex")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field} must be sha256 hex") from exc
    return value


def _intent_fingerprint(intent: ExecutionIntent) -> str:
    return _fingerprint(
        {
            "schema_version": intent.schema_version,
            "decision_id": intent.decision_id,
            "run_manifest_fingerprint": intent.run_manifest_fingerprint,
            "created_at": intent.created_at.isoformat(),
            "symbol": intent.symbol,
            "side": intent.side.value,
            "quantity": float(intent.quantity),
            "requested_price": float(intent.requested_price),
            "stop_price": float(intent.stop_price),
            "target_price": float(intent.target_price),
            "client_order_id": intent.client_order_id,
        }
    )


@dataclass(frozen=True, slots=True)
class BrokerOrderEvent:
    schema_version: str
    client_order_id: str
    intent_fingerprint: str
    sequence: int
    previous_state: BrokerOrderState | None
    state: BrokerOrderState
    venue_event_time: datetime
    cumulative_filled_quantity: float
    last_fill_quantity: float
    last_fill_price: float | None
    venue_order_id: str | None
    reason: str | None
    event_fingerprint: str
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != BROKER_ORDER_EVENT_SCHEMA:
            raise ValueError("broker order event schema mismatch")
        _sha(self.client_order_id, "client_order_id")
        _sha(self.intent_fingerprint, "intent_fingerprint")
        _sha(self.event_fingerprint, "event_fingerprint")
        if self.venue_event_time.tzinfo is None:
            raise ValueError("venue_event_time must be timezone-aware")
        if self.sequence < 0:
            raise ValueError("sequence must be non-negative")
        if self.cumulative_filled_quantity < 0 or self.last_fill_quantity < 0:
            raise ValueError("fill quantities must be non-negative")
        if self.last_fill_price is not None and self.last_fill_price <= 0:
            raise ValueError("last_fill_price must be positive when supplied")
        if self.execution_capability != "NONE" or self.order_execution_enabled:
            raise ValueError("broker order evidence cannot authorize execution")
        if self.event_fingerprint != self.expected_fingerprint:
            raise ValueError("broker order event fingerprint mismatch")

    @property
    def expected_fingerprint(self) -> str:
        return _fingerprint(
            {
                "schema_version": self.schema_version,
                "client_order_id": self.client_order_id,
                "intent_fingerprint": self.intent_fingerprint,
                "sequence": self.sequence,
                "previous_state": (
                    None if self.previous_state is None else self.previous_state.value
                ),
                "state": self.state.value,
                "venue_event_time": self.venue_event_time.isoformat(),
                "cumulative_filled_quantity": float(self.cumulative_filled_quantity),
                "last_fill_quantity": float(self.last_fill_quantity),
                "last_fill_price": (
                    None if self.last_fill_price is None else float(self.last_fill_price)
                ),
                "venue_order_id": self.venue_order_id,
                "reason": self.reason,
            }
        )


@dataclass(frozen=True, slots=True)
class BrokerOrderLifecycle:
    schema_version: str
    client_order_id: str
    intent_fingerprint: str
    requested_quantity: float
    state: BrokerOrderState
    cumulative_filled_quantity: float
    average_fill_price: float | None
    venue_order_id: str | None
    last_event_time: datetime
    last_event_fingerprint: str
    event_count: int
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != BROKER_ORDER_LIFECYCLE_SCHEMA:
            raise ValueError("broker order lifecycle schema mismatch")
        _sha(self.client_order_id, "client_order_id")
        _sha(self.intent_fingerprint, "intent_fingerprint")
        _sha(self.last_event_fingerprint, "last_event_fingerprint")
        if not isinstance(self.state, BrokerOrderState):
            raise TypeError("state must be BrokerOrderState")
        if self.requested_quantity <= 0:
            raise ValueError("requested_quantity must be positive")
        if self.cumulative_filled_quantity < 0:
            raise ValueError("cumulative_filled_quantity must be non-negative")
        if self.cumulative_filled_quantity > self.requested_quantity:
            raise ValueError("cumulative fill cannot exceed requested quantity")
        if self.average_fill_price is not None and self.average_fill_price <= 0:
            raise ValueError("average_fill_price must be positive when supplied")
        if self.last_event_time.tzinfo is None:
            raise ValueError("last_event_time must be timezone-aware")
        if self.event_count < 1:
            raise ValueError("event_count must be positive")
        if self.execution_capability != "NONE" or self.order_execution_enabled:
            raise ValueError("broker order lifecycle cannot authorize execution")
        if (
            self.state is BrokerOrderState.FILLED
            and self.cumulative_filled_quantity != self.requested_quantity
        ):
            raise ValueError("FILLED requires cumulative quantity to equal requested quantity")
        if self.state is BrokerOrderState.PARTIAL and not (
            0 < self.cumulative_filled_quantity < self.requested_quantity
        ):
            raise ValueError("PARTIAL requires fill quantity strictly between zero and requested")
        if self.cumulative_filled_quantity > 0 and self.average_fill_price is None:
            raise ValueError("filled quantity requires average_fill_price")

    @property
    def terminal(self) -> bool:
        return self.state in _TERMINAL

    @property
    def fingerprint(self) -> str:
        return _fingerprint(
            {
                "schema_version": self.schema_version,
                "client_order_id": self.client_order_id,
                "intent_fingerprint": self.intent_fingerprint,
                "requested_quantity": float(self.requested_quantity),
                "state": self.state.value,
                "cumulative_filled_quantity": float(self.cumulative_filled_quantity),
                "average_fill_price": (
                    None if self.average_fill_price is None else float(self.average_fill_price)
                ),
                "venue_order_id": self.venue_order_id,
                "last_event_time": self.last_event_time.isoformat(),
                "last_event_fingerprint": self.last_event_fingerprint,
                "event_count": self.event_count,
                "execution_capability": self.execution_capability,
                "order_execution_enabled": self.order_execution_enabled,
            }
        )


def broker_order_lifecycle_state_payload(
    lifecycle: BrokerOrderLifecycle,
) -> dict[str, Any]:
    """Serialize one lifecycle into a strict tamper-evident restart envelope."""
    payload: dict[str, Any] = {
        "state_schema_version": BROKER_ORDER_LIFECYCLE_STATE_SCHEMA,
        "lifecycle_schema_version": lifecycle.schema_version,
        "client_order_id": lifecycle.client_order_id,
        "intent_fingerprint": lifecycle.intent_fingerprint,
        "requested_quantity": float(lifecycle.requested_quantity),
        "state": lifecycle.state.value,
        "cumulative_filled_quantity": float(lifecycle.cumulative_filled_quantity),
        "average_fill_price": (
            None
            if lifecycle.average_fill_price is None
            else float(lifecycle.average_fill_price)
        ),
        "venue_order_id": lifecycle.venue_order_id,
        "last_event_time": lifecycle.last_event_time.isoformat(),
        "last_event_fingerprint": lifecycle.last_event_fingerprint,
        "event_count": lifecycle.event_count,
        "execution_capability": lifecycle.execution_capability,
        "order_execution_enabled": lifecycle.order_execution_enabled,
        "lifecycle_fingerprint": lifecycle.fingerprint,
    }
    payload["payload_fingerprint"] = _fingerprint(payload)
    return payload


def parse_broker_order_lifecycle_state_payload(
    payload: Mapping[str, Any],
) -> BrokerOrderLifecycle:
    """Restore lifecycle evidence and fail closed on any persisted drift."""
    unknown = payload.keys() - _LIFECYCLE_STATE_FIELDS
    missing = _LIFECYCLE_STATE_FIELDS - payload.keys()
    if unknown:
        raise ValueError(f"unknown broker lifecycle state fields: {sorted(unknown)}")
    if missing:
        raise ValueError(f"missing broker lifecycle state fields: {sorted(missing)}")
    if payload.get("state_schema_version") != BROKER_ORDER_LIFECYCLE_STATE_SCHEMA:
        raise ValueError("broker order lifecycle state schema mismatch")
    if payload.get("lifecycle_schema_version") != BROKER_ORDER_LIFECYCLE_SCHEMA:
        raise ValueError("broker order lifecycle schema mismatch")
    if payload.get("execution_capability") != "NONE":
        raise ValueError("broker order lifecycle state execution capability invalid")
    if payload.get("order_execution_enabled") is not False:
        raise ValueError("broker order lifecycle state cannot enable order execution")

    observed_payload_fingerprint = _sha(
        payload.get("payload_fingerprint"),
        "payload_fingerprint",
    )
    unhashed = dict(payload)
    unhashed.pop("payload_fingerprint", None)
    if _fingerprint(unhashed) != observed_payload_fingerprint:
        raise ValueError("broker order lifecycle state payload fingerprint mismatch")

    client_order_id = _sha(payload.get("client_order_id"), "client_order_id")
    intent_fingerprint = _sha(payload.get("intent_fingerprint"), "intent_fingerprint")
    last_event_fingerprint = _sha(
        payload.get("last_event_fingerprint"),
        "last_event_fingerprint",
    )
    observed_lifecycle_fingerprint = _sha(
        payload.get("lifecycle_fingerprint"),
        "lifecycle_fingerprint",
    )

    raw_time = payload.get("last_event_time")
    if not isinstance(raw_time, str):
        raise ValueError("last_event_time must be ISO-8601 string")
    try:
        last_event_time = datetime.fromisoformat(raw_time.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("last_event_time must be valid ISO-8601") from exc

    raw_state = payload.get("state")
    if not isinstance(raw_state, str):
        raise ValueError("state must be a string")
    try:
        state = BrokerOrderState(raw_state)
    except ValueError as exc:
        raise ValueError("broker order lifecycle state value invalid") from exc

    requested_quantity = _number(payload.get("requested_quantity"), "requested_quantity")
    cumulative_filled_quantity = _number(
        payload.get("cumulative_filled_quantity"),
        "cumulative_filled_quantity",
    )
    raw_average = payload.get("average_fill_price")
    average_fill_price = (
        None
        if raw_average is None
        else _number(raw_average, "average_fill_price")
    )
    venue_order_id = payload.get("venue_order_id")
    if venue_order_id is not None and (
        not isinstance(venue_order_id, str) or not venue_order_id.strip()
    ):
        raise ValueError("venue_order_id must be non-empty string or null")
    event_count = payload.get("event_count")
    if type(event_count) is not int:
        raise ValueError("event_count must be integer")

    lifecycle = BrokerOrderLifecycle(
        schema_version=BROKER_ORDER_LIFECYCLE_SCHEMA,
        client_order_id=client_order_id,
        intent_fingerprint=intent_fingerprint,
        requested_quantity=requested_quantity,
        state=state,
        cumulative_filled_quantity=cumulative_filled_quantity,
        average_fill_price=average_fill_price,
        venue_order_id=venue_order_id,
        last_event_time=last_event_time,
        last_event_fingerprint=last_event_fingerprint,
        event_count=event_count,
    )
    if lifecycle.fingerprint != observed_lifecycle_fingerprint:
        raise ValueError("broker order lifecycle fingerprint mismatch")
    return lifecycle


def begin_order_lifecycle(
    *,
    intent: ExecutionIntent,
    requested_at: datetime,
) -> tuple[BrokerOrderLifecycle, BrokerOrderEvent]:
    """Create REQUESTED evidence for an existing intent; submit nothing."""
    if requested_at.tzinfo is None:
        raise ValueError("requested_at must be timezone-aware")
    if requested_at < intent.created_at:
        raise ValueError("requested_at cannot precede intent.created_at")

    intent_fp = _intent_fingerprint(intent)
    event = _build_event(
        client_order_id=intent.client_order_id,
        intent_fingerprint=intent_fp,
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
        client_order_id=intent.client_order_id,
        intent_fingerprint=intent_fp,
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


def apply_order_event(
    *,
    lifecycle: BrokerOrderLifecycle,
    state: BrokerOrderState,
    venue_event_time: datetime,
    cumulative_filled_quantity: float | None = None,
    last_fill_price: float | None = None,
    venue_order_id: str | None = None,
    reason: str | None = None,
) -> tuple[BrokerOrderLifecycle, BrokerOrderEvent]:
    """Validate one broker-neutral venue observation and return new evidence."""
    if not isinstance(state, BrokerOrderState):
        raise TypeError("state must be BrokerOrderState")
    if venue_event_time.tzinfo is None:
        raise ValueError("venue_event_time must be timezone-aware")
    if venue_event_time < lifecycle.last_event_time:
        raise ValueError("venue event time cannot move backwards")
    if lifecycle.terminal:
        raise ValueError("terminal broker order lifecycle cannot transition")
    allowed = _ALLOWED_NEXT.get(lifecycle.state, set())
    if state not in allowed:
        raise ValueError(f"invalid broker order transition: {lifecycle.state.value}->{state.value}")

    next_cumulative = (
        lifecycle.cumulative_filled_quantity
        if cumulative_filled_quantity is None
        else float(cumulative_filled_quantity)
    )
    if next_cumulative < lifecycle.cumulative_filled_quantity:
        raise ValueError("cumulative filled quantity cannot decrease")
    if next_cumulative > lifecycle.requested_quantity:
        raise ValueError("cumulative filled quantity cannot exceed requested quantity")

    delta = next_cumulative - lifecycle.cumulative_filled_quantity
    if delta > 0 and (last_fill_price is None or last_fill_price <= 0):
        raise ValueError("positive fill delta requires positive last_fill_price")
    if delta == 0 and last_fill_price is not None:
        raise ValueError("last_fill_price is only valid when fill quantity increases")

    if state is BrokerOrderState.PARTIAL and not (
        0 < next_cumulative < lifecycle.requested_quantity
    ):
        raise ValueError("PARTIAL requires cumulative quantity between zero and requested")
    if state is BrokerOrderState.FILLED and next_cumulative != lifecycle.requested_quantity:
        raise ValueError("FILLED requires cumulative quantity equal requested quantity")
    if state in {BrokerOrderState.ACK, BrokerOrderState.REJECT, BrokerOrderState.EXPIRED} and delta:
        raise ValueError(f"{state.value} cannot add fill quantity")
    if state is BrokerOrderState.REJECT and not reason:
        raise ValueError("REJECT requires a reason")

    next_venue_order_id = venue_order_id or lifecycle.venue_order_id
    if lifecycle.venue_order_id and venue_order_id and venue_order_id != lifecycle.venue_order_id:
        raise ValueError("venue_order_id cannot change")
    if state in {BrokerOrderState.ACK, BrokerOrderState.PARTIAL, BrokerOrderState.FILLED} and not next_venue_order_id:
        raise ValueError(f"{state.value} requires venue_order_id")

    next_average = lifecycle.average_fill_price
    if delta > 0:
        previous_value = lifecycle.cumulative_filled_quantity * (lifecycle.average_fill_price or 0.0)
        next_average = (previous_value + delta * float(last_fill_price)) / next_cumulative

    event = _build_event(
        client_order_id=lifecycle.client_order_id,
        intent_fingerprint=lifecycle.intent_fingerprint,
        sequence=lifecycle.event_count,
        previous_state=lifecycle.state,
        state=state,
        venue_event_time=venue_event_time,
        cumulative_filled_quantity=next_cumulative,
        last_fill_quantity=delta,
        last_fill_price=last_fill_price,
        venue_order_id=next_venue_order_id,
        reason=reason,
    )
    updated = BrokerOrderLifecycle(
        schema_version=BROKER_ORDER_LIFECYCLE_SCHEMA,
        client_order_id=lifecycle.client_order_id,
        intent_fingerprint=lifecycle.intent_fingerprint,
        requested_quantity=lifecycle.requested_quantity,
        state=state,
        cumulative_filled_quantity=next_cumulative,
        average_fill_price=next_average,
        venue_order_id=next_venue_order_id,
        last_event_time=venue_event_time,
        last_event_fingerprint=event.event_fingerprint,
        event_count=lifecycle.event_count + 1,
    )
    return updated, event


def _build_event(
    *,
    client_order_id: str,
    intent_fingerprint: str,
    sequence: int,
    previous_state: BrokerOrderState | None,
    state: BrokerOrderState,
    venue_event_time: datetime,
    cumulative_filled_quantity: float,
    last_fill_quantity: float,
    last_fill_price: float | None,
    venue_order_id: str | None,
    reason: str | None,
) -> BrokerOrderEvent:
    payload = {
        "schema_version": BROKER_ORDER_EVENT_SCHEMA,
        "client_order_id": client_order_id,
        "intent_fingerprint": intent_fingerprint,
        "sequence": sequence,
        "previous_state": None if previous_state is None else previous_state.value,
        "state": state.value,
        "venue_event_time": venue_event_time.isoformat(),
        "cumulative_filled_quantity": float(cumulative_filled_quantity),
        "last_fill_quantity": float(last_fill_quantity),
        "last_fill_price": None if last_fill_price is None else float(last_fill_price),
        "venue_order_id": venue_order_id,
        "reason": reason,
    }
    return BrokerOrderEvent(
        schema_version=BROKER_ORDER_EVENT_SCHEMA,
        client_order_id=client_order_id,
        intent_fingerprint=intent_fingerprint,
        sequence=sequence,
        previous_state=previous_state,
        state=state,
        venue_event_time=venue_event_time,
        cumulative_filled_quantity=float(cumulative_filled_quantity),
        last_fill_quantity=float(last_fill_quantity),
        last_fill_price=None if last_fill_price is None else float(last_fill_price),
        venue_order_id=venue_order_id,
        reason=reason,
        event_fingerprint=_fingerprint(payload),
    )


def _number(value: Any, field: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{field} must be numeric")
    return float(value)
