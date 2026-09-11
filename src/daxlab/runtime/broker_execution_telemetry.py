"""Append-only broker-neutral execution telemetry evidence.

This module does not own order state, reconciliation logic, protection rules or
broker transport. It serializes already-owned evidence into deterministic event
records suitable for a future append-only telemetry store. No broker API, order
submission capability, PAPER authorization or LIVE authorization exists here.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from hashlib import sha256
import json
from typing import Any

from daxlab.runtime.broker_execution_protection import (
    BrokerExecutionProtectionVerdict,
)
from daxlab.runtime.broker_order_lifecycle import BrokerOrderEvent, BrokerOrderState
from daxlab.runtime.broker_reconciliation import BrokerReconciliationVerdict


BROKER_EXECUTION_TELEMETRY_SCHEMA = "DAXLAB_BROKER_EXECUTION_TELEMETRY_V1"


class BrokerExecutionTelemetryKind(StrEnum):
    ORDER_EVENT = "ORDER_EVENT"
    RECONCILIATION = "RECONCILIATION"
    PROTECTION = "PROTECTION"


@dataclass(frozen=True, slots=True)
class BrokerExecutionTelemetryRecord:
    schema_version: str
    kind: BrokerExecutionTelemetryKind
    event_time: datetime
    client_order_id: str | None
    source_fingerprint: str
    intent_fingerprint: str | None
    lifecycle_state: str | None
    source_sequence: int | None
    reconciliation_status: str | None
    protection_status: str | None
    blockers: tuple[str, ...]
    venue_order_id: str | None = None
    cumulative_filled_quantity: float | None = None
    last_fill_quantity: float | None = None
    last_fill_price: float | None = None
    feed_age_seconds: float | None = None
    observed_spread_points: float | None = None
    sizing_evidence_fingerprint: str | None = None
    risk_policy_fingerprint: str | None = None
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False
    telemetry_fingerprint: str = ""

    def __post_init__(self) -> None:
        if self.schema_version != BROKER_EXECUTION_TELEMETRY_SCHEMA:
            raise ValueError("broker execution telemetry schema mismatch")
        if not isinstance(self.kind, BrokerExecutionTelemetryKind):
            raise TypeError("kind must be BrokerExecutionTelemetryKind")
        if self.event_time.tzinfo is None:
            raise ValueError("event_time must be timezone-aware")
        if self.client_order_id is not None:
            _sha(self.client_order_id, "client_order_id")
        _sha(self.source_fingerprint, "source_fingerprint")
        for value, field in (
            (self.intent_fingerprint, "intent_fingerprint"),
            (self.sizing_evidence_fingerprint, "sizing_evidence_fingerprint"),
            (self.risk_policy_fingerprint, "risk_policy_fingerprint"),
        ):
            if value is not None:
                _sha(value, field)
        if self.source_sequence is not None and self.source_sequence < 0:
            raise ValueError("source_sequence must be non-negative")
        for value, field in (
            (self.cumulative_filled_quantity, "cumulative_filled_quantity"),
            (self.last_fill_quantity, "last_fill_quantity"),
            (self.feed_age_seconds, "feed_age_seconds"),
            (self.observed_spread_points, "observed_spread_points"),
        ):
            if value is not None and value < 0:
                raise ValueError(f"{field} must be non-negative")
        if self.last_fill_price is not None and self.last_fill_price <= 0:
            raise ValueError("last_fill_price must be positive when supplied")
        if self.execution_capability != "NONE" or self.order_execution_enabled:
            raise ValueError("broker execution telemetry cannot authorize execution")
        self._validate_kind_shape()
        if self.telemetry_fingerprint != self.expected_fingerprint:
            raise ValueError("broker execution telemetry fingerprint mismatch")

    def _validate_kind_shape(self) -> None:
        if self.kind is BrokerExecutionTelemetryKind.ORDER_EVENT:
            if self.client_order_id is None or self.intent_fingerprint is None:
                raise ValueError("order-event telemetry requires order and intent identity")
            if self.lifecycle_state is None or self.source_sequence is None:
                raise ValueError("order-event telemetry requires lifecycle state and sequence")
            if self.reconciliation_status is not None or self.protection_status is not None:
                raise ValueError("order-event telemetry cannot carry other verdict states")
            return

        if self.kind is BrokerExecutionTelemetryKind.RECONCILIATION:
            if self.reconciliation_status is None:
                raise ValueError("reconciliation telemetry requires reconciliation status")
            if self.lifecycle_state is not None or self.protection_status is not None:
                raise ValueError("reconciliation telemetry cannot carry other verdict states")
            if any(
                value is not None
                for value in (
                    self.intent_fingerprint,
                    self.source_sequence,
                    self.venue_order_id,
                    self.cumulative_filled_quantity,
                    self.last_fill_quantity,
                    self.last_fill_price,
                    self.feed_age_seconds,
                    self.observed_spread_points,
                    self.sizing_evidence_fingerprint,
                    self.risk_policy_fingerprint,
                )
            ):
                raise ValueError("reconciliation telemetry contains unrelated fields")
            return

        if self.protection_status is None or self.client_order_id is None:
            raise ValueError("protection telemetry requires status and client order identity")
        if self.lifecycle_state is not None or self.reconciliation_status is not None:
            raise ValueError("protection telemetry cannot carry other verdict states")
        if any(
            value is not None
            for value in (
                self.intent_fingerprint,
                self.source_sequence,
                self.venue_order_id,
                self.cumulative_filled_quantity,
                self.last_fill_quantity,
                self.last_fill_price,
            )
        ):
            raise ValueError("protection telemetry contains unrelated lifecycle fields")

    @property
    def expected_fingerprint(self) -> str:
        return _fingerprint(self.identity_payload)

    @property
    def identity_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "kind": self.kind.value,
            "event_time": self.event_time.isoformat(),
            "client_order_id": self.client_order_id,
            "source_fingerprint": self.source_fingerprint,
            "intent_fingerprint": self.intent_fingerprint,
            "lifecycle_state": self.lifecycle_state,
            "source_sequence": self.source_sequence,
            "reconciliation_status": self.reconciliation_status,
            "protection_status": self.protection_status,
            "blockers": list(self.blockers),
            "venue_order_id": self.venue_order_id,
            "cumulative_filled_quantity": self.cumulative_filled_quantity,
            "last_fill_quantity": self.last_fill_quantity,
            "last_fill_price": self.last_fill_price,
            "feed_age_seconds": self.feed_age_seconds,
            "observed_spread_points": self.observed_spread_points,
            "sizing_evidence_fingerprint": self.sizing_evidence_fingerprint,
            "risk_policy_fingerprint": self.risk_policy_fingerprint,
            "execution_capability": self.execution_capability,
            "order_execution_enabled": self.order_execution_enabled,
        }

    def as_dict(self) -> dict[str, Any]:
        payload = self.identity_payload
        payload["telemetry_fingerprint"] = self.telemetry_fingerprint
        return payload


def telemetry_from_order_event(event: BrokerOrderEvent) -> BrokerExecutionTelemetryRecord:
    """Project one canonical order event into append-only telemetry evidence."""
    payload = _record_payload(
        kind=BrokerExecutionTelemetryKind.ORDER_EVENT,
        event_time=event.venue_event_time,
        client_order_id=event.client_order_id,
        source_fingerprint=event.event_fingerprint,
        intent_fingerprint=event.intent_fingerprint,
        lifecycle_state=event.state.value,
        source_sequence=event.sequence,
        reconciliation_status=None,
        protection_status=None,
        blockers=(() if event.reason is None else (event.reason,)),
        venue_order_id=event.venue_order_id,
        cumulative_filled_quantity=event.cumulative_filled_quantity,
        last_fill_quantity=event.last_fill_quantity,
        last_fill_price=event.last_fill_price,
        feed_age_seconds=None,
        observed_spread_points=None,
        sizing_evidence_fingerprint=None,
        risk_policy_fingerprint=None,
    )
    return _record(payload)


def telemetry_from_reconciliation(
    verdict: BrokerReconciliationVerdict,
    *,
    observed_at: datetime,
) -> BrokerExecutionTelemetryRecord:
    """Record one reconciliation verdict; observed_at is transport/event metadata."""
    if observed_at.tzinfo is None:
        raise ValueError("observed_at must be timezone-aware")
    payload = _record_payload(
        kind=BrokerExecutionTelemetryKind.RECONCILIATION,
        event_time=observed_at,
        client_order_id=verdict.reconciled_client_order_id,
        source_fingerprint=verdict.fingerprint,
        intent_fingerprint=None,
        lifecycle_state=None,
        source_sequence=None,
        reconciliation_status=verdict.status.value,
        protection_status=None,
        blockers=verdict.blockers,
        venue_order_id=None,
        cumulative_filled_quantity=None,
        last_fill_quantity=None,
        last_fill_price=None,
        feed_age_seconds=None,
        observed_spread_points=None,
        sizing_evidence_fingerprint=None,
        risk_policy_fingerprint=None,
    )
    return _record(payload)


def telemetry_from_protection(
    verdict: BrokerExecutionProtectionVerdict,
    *,
    evaluated_at: datetime,
) -> BrokerExecutionTelemetryRecord:
    """Record one pre-submission safety verdict; submit and authorize nothing."""
    if evaluated_at.tzinfo is None:
        raise ValueError("evaluated_at must be timezone-aware")
    payload = _record_payload(
        kind=BrokerExecutionTelemetryKind.PROTECTION,
        event_time=evaluated_at,
        client_order_id=verdict.client_order_id,
        source_fingerprint=verdict.fingerprint,
        intent_fingerprint=None,
        lifecycle_state=None,
        source_sequence=None,
        reconciliation_status=None,
        protection_status=verdict.status.value,
        blockers=verdict.blockers,
        venue_order_id=None,
        cumulative_filled_quantity=None,
        last_fill_quantity=None,
        last_fill_price=None,
        feed_age_seconds=verdict.feed_age_seconds,
        observed_spread_points=verdict.observed_spread_points,
        sizing_evidence_fingerprint=verdict.sizing_evidence_fingerprint,
        risk_policy_fingerprint=verdict.risk_policy_fingerprint,
    )
    return _record(payload)


def _record_payload(
    *,
    kind: BrokerExecutionTelemetryKind,
    event_time: datetime,
    client_order_id: str | None,
    source_fingerprint: str,
    intent_fingerprint: str | None,
    lifecycle_state: str | None,
    source_sequence: int | None,
    reconciliation_status: str | None,
    protection_status: str | None,
    blockers: tuple[str, ...],
    venue_order_id: str | None,
    cumulative_filled_quantity: float | None,
    last_fill_quantity: float | None,
    last_fill_price: float | None,
    feed_age_seconds: float | None,
    observed_spread_points: float | None,
    sizing_evidence_fingerprint: str | None,
    risk_policy_fingerprint: str | None,
) -> dict[str, Any]:
    return {
        "schema_version": BROKER_EXECUTION_TELEMETRY_SCHEMA,
        "kind": kind.value,
        "event_time": event_time.isoformat(),
        "client_order_id": client_order_id,
        "source_fingerprint": source_fingerprint,
        "intent_fingerprint": intent_fingerprint,
        "lifecycle_state": lifecycle_state,
        "source_sequence": source_sequence,
        "reconciliation_status": reconciliation_status,
        "protection_status": protection_status,
        "blockers": list(blockers),
        "venue_order_id": venue_order_id,
        "cumulative_filled_quantity": cumulative_filled_quantity,
        "last_fill_quantity": last_fill_quantity,
        "last_fill_price": last_fill_price,
        "feed_age_seconds": feed_age_seconds,
        "observed_spread_points": observed_spread_points,
        "sizing_evidence_fingerprint": sizing_evidence_fingerprint,
        "risk_policy_fingerprint": risk_policy_fingerprint,
        "execution_capability": "NONE",
        "order_execution_enabled": False,
    }


def _record(payload: dict[str, Any]) -> BrokerExecutionTelemetryRecord:
    kind = BrokerExecutionTelemetryKind(payload["kind"])
    event_time = datetime.fromisoformat(payload["event_time"])
    return BrokerExecutionTelemetryRecord(
        schema_version=payload["schema_version"],
        kind=kind,
        event_time=event_time,
        client_order_id=payload["client_order_id"],
        source_fingerprint=payload["source_fingerprint"],
        intent_fingerprint=payload["intent_fingerprint"],
        lifecycle_state=payload["lifecycle_state"],
        source_sequence=payload["source_sequence"],
        reconciliation_status=payload["reconciliation_status"],
        protection_status=payload["protection_status"],
        blockers=tuple(payload["blockers"]),
        venue_order_id=payload["venue_order_id"],
        cumulative_filled_quantity=payload["cumulative_filled_quantity"],
        last_fill_quantity=payload["last_fill_quantity"],
        last_fill_price=payload["last_fill_price"],
        feed_age_seconds=payload["feed_age_seconds"],
        observed_spread_points=payload["observed_spread_points"],
        sizing_evidence_fingerprint=payload["sizing_evidence_fingerprint"],
        risk_policy_fingerprint=payload["risk_policy_fingerprint"],
        telemetry_fingerprint=_fingerprint(payload),
    )


def _sha(value: str, field: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{field} must be sha256 hex")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field} must be sha256 hex") from exc


def _fingerprint(value: dict[str, Any]) -> str:
    canonical = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()
