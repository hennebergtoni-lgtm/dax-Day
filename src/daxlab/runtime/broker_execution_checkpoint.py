"""One tamper-evident checkpoint for broker-neutral execution evidence state.

Nested semantics remain owned by ``broker_order_lifecycle`` and
``broker_execution_telemetry_journal``. This module only binds the optional current
order lifecycle and telemetry idempotency journal so callers can persist both with
one existing ``atomic_write_json`` call. No broker API, submission capability,
PAPER authorization or LIVE authorization exists here.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Mapping

from daxlab.runtime.broker_execution_telemetry_journal import (
    BrokerExecutionTelemetryJournal,
    broker_execution_telemetry_journal_payload,
    parse_broker_execution_telemetry_journal_payload,
)
from daxlab.runtime.broker_order_lifecycle import (
    BrokerOrderLifecycle,
    broker_order_lifecycle_state_payload,
    parse_broker_order_lifecycle_state_payload,
)


BROKER_EXECUTION_CHECKPOINT_SCHEMA = "DAXLAB_BROKER_EXECUTION_CHECKPOINT_V1"
_ALLOWED_FIELDS = {
    "schema_version",
    "lifecycle_state",
    "telemetry_journal",
    "execution_capability",
    "order_execution_enabled",
    "payload_fingerprint",
}


@dataclass(frozen=True, slots=True)
class BrokerExecutionCheckpointState:
    lifecycle: BrokerOrderLifecycle | None
    telemetry_journal: BrokerExecutionTelemetryJournal
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.lifecycle is not None and (
            self.lifecycle.execution_capability != "NONE"
            or self.lifecycle.order_execution_enabled
        ):
            raise ValueError("checkpoint lifecycle cannot authorize execution")
        if (
            self.telemetry_journal.execution_capability != "NONE"
            or self.telemetry_journal.order_execution_enabled
        ):
            raise ValueError("checkpoint telemetry journal cannot authorize execution")
        if self.execution_capability != "NONE" or self.order_execution_enabled:
            raise ValueError("broker execution checkpoint cannot authorize execution")


def broker_execution_checkpoint_payload(
    state: BrokerExecutionCheckpointState,
) -> dict[str, Any]:
    """Return one JSON-safe envelope for a single atomic persistence boundary."""
    payload: dict[str, Any] = {
        "schema_version": BROKER_EXECUTION_CHECKPOINT_SCHEMA,
        "lifecycle_state": (
            None
            if state.lifecycle is None
            else broker_order_lifecycle_state_payload(state.lifecycle)
        ),
        "telemetry_journal": broker_execution_telemetry_journal_payload(
            state.telemetry_journal
        ),
        "execution_capability": state.execution_capability,
        "order_execution_enabled": state.order_execution_enabled,
    }
    payload["payload_fingerprint"] = _fingerprint(payload)
    return payload


def parse_broker_execution_checkpoint_payload(
    payload: Mapping[str, Any],
) -> BrokerExecutionCheckpointState:
    """Restore both nested owners and fail closed on any envelope drift."""
    unknown = payload.keys() - _ALLOWED_FIELDS
    missing = _ALLOWED_FIELDS - payload.keys()
    if unknown:
        raise ValueError(f"unknown broker execution checkpoint fields: {sorted(unknown)}")
    if missing:
        raise ValueError(f"missing broker execution checkpoint fields: {sorted(missing)}")
    if payload.get("schema_version") != BROKER_EXECUTION_CHECKPOINT_SCHEMA:
        raise ValueError("broker execution checkpoint schema mismatch")
    if payload.get("execution_capability") != "NONE":
        raise ValueError("broker execution checkpoint execution capability invalid")
    if payload.get("order_execution_enabled") is not False:
        raise ValueError("broker execution checkpoint cannot enable order execution")

    observed = _sha(payload.get("payload_fingerprint"), "payload_fingerprint")
    unhashed = dict(payload)
    unhashed.pop("payload_fingerprint", None)
    if _fingerprint(unhashed) != observed:
        raise ValueError("broker execution checkpoint payload fingerprint mismatch")

    raw_lifecycle = payload.get("lifecycle_state")
    raw_journal = payload.get("telemetry_journal")
    if raw_lifecycle is not None and not isinstance(raw_lifecycle, Mapping):
        raise ValueError("broker execution checkpoint lifecycle_state invalid")
    if not isinstance(raw_journal, Mapping):
        raise ValueError("broker execution checkpoint telemetry_journal invalid")

    return BrokerExecutionCheckpointState(
        lifecycle=(
            None
            if raw_lifecycle is None
            else parse_broker_order_lifecycle_state_payload(raw_lifecycle)
        ),
        telemetry_journal=parse_broker_execution_telemetry_journal_payload(raw_journal),
    )


def _sha(value: Any, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{field} must be sha256 hex")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field} must be sha256 hex") from exc
    return value


def _fingerprint(value: Mapping[str, Any]) -> str:
    canonical = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()
