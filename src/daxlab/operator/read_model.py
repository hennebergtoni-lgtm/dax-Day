"""Generic read-only operator view for the DAX-BOT NextGen product core.

Operator views consume already-owned product state. They never define strategy,
risk, broker or execution semantics and cannot authorize external execution.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json


OPERATOR_VIEW_SCHEMA = "DAXLAB_PRODUCT_OPERATOR_VIEW_V1"


@dataclass(frozen=True, slots=True)
class ProductOperatorViewV1:
    schema_version: str
    queried_at: datetime
    snapshot_generated_at: datetime
    source: str
    product_version: str
    strategy_id: str
    config_fingerprint: str
    source_snapshot_fingerprint: str
    decision_id: str
    decision_action: str
    decision_blockers: tuple[str, ...]
    risk_state: str
    last_market_event_id: str | None
    last_market_event_time: datetime | None
    current_market_event_age_seconds: float | None
    health_state: str | None
    health_source: str | None
    runtime_events: tuple[str, ...]
    recovery_state: str | None
    reconciliation_state: str | None
    view_fingerprint: str
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != OPERATOR_VIEW_SCHEMA:
            raise ValueError("unsupported product operator view schema")
        for field_name, value in (
            ("source", self.source),
            ("product_version", self.product_version),
            ("strategy_id", self.strategy_id),
            ("decision_action", self.decision_action),
            ("risk_state", self.risk_state),
        ):
            _require_text(value, field_name)
        for field_name, value in (
            ("config_fingerprint", self.config_fingerprint),
            ("source_snapshot_fingerprint", self.source_snapshot_fingerprint),
            ("decision_id", self.decision_id),
            ("view_fingerprint", self.view_fingerprint),
        ):
            _require_sha256(value, field_name)

        _require_aware(self.queried_at, "queried_at")
        _require_aware(self.snapshot_generated_at, "snapshot_generated_at")
        if self.queried_at < self.snapshot_generated_at:
            raise ValueError("operator query cannot precede source snapshot")

        event_context = (
            self.last_market_event_id,
            self.last_market_event_time,
            self.current_market_event_age_seconds,
        )
        if any(value is not None for value in event_context) and any(
            value is None for value in event_context
        ):
            raise ValueError("operator market-event context must be complete")
        if self.last_market_event_id is not None:
            _require_sha256(self.last_market_event_id, "last_market_event_id")
            assert self.last_market_event_time is not None
            assert self.current_market_event_age_seconds is not None
            _require_aware(self.last_market_event_time, "last_market_event_time")
            expected_age = (
                self.queried_at.astimezone(timezone.utc)
                - self.last_market_event_time.astimezone(timezone.utc)
            ).total_seconds()
            if expected_age < 0:
                raise ValueError("last market event is in the future")
            if self.current_market_event_age_seconds < 0:
                raise ValueError("current_market_event_age_seconds must be non-negative")
            if abs(float(expected_age) - self.current_market_event_age_seconds) > 1e-9:
                raise ValueError("current market-event age mismatch")

        if (self.health_state is None) != (self.health_source is None):
            raise ValueError("health_state and health_source must be paired")
        if self.health_state is not None:
            _require_text(self.health_state, "health_state")
            assert self.health_source is not None
            _require_text(self.health_source, "health_source")
        _require_unique_text(self.decision_blockers, "decision_blockers")
        _require_unique_text(self.runtime_events, "runtime_events")
        for field_name, value in (
            ("recovery_state", self.recovery_state),
            ("reconciliation_state", self.reconciliation_state),
        ):
            if value is not None:
                _require_text(value, field_name)

        if self.execution_capability != "NONE" or self.order_execution_enabled:
            raise ValueError("product operator view cannot authorize execution")
        if self.view_fingerprint != _fingerprint(_identity_payload(self)):
            raise ValueError("product operator view fingerprint mismatch")

    def to_dict(self) -> dict[str, object]:
        return _identity_payload(self) | {"view_fingerprint": self.view_fingerprint}


def build_product_operator_view(
    *,
    queried_at: datetime,
    snapshot_generated_at: datetime,
    source: str,
    product_version: str,
    strategy_id: str,
    config_fingerprint: str,
    source_snapshot_fingerprint: str,
    decision_id: str,
    decision_action: str,
    decision_blockers: tuple[str, ...],
    risk_state: str,
    last_market_event_id: str | None,
    last_market_event_time: datetime | None,
    health_state: str | None,
    health_source: str | None,
    runtime_events: tuple[str, ...],
    recovery_state: str | None,
    reconciliation_state: str | None,
) -> ProductOperatorViewV1:
    """Build a deterministic read model and derive query-time market freshness."""

    _require_aware(queried_at, "queried_at")
    _require_aware(snapshot_generated_at, "snapshot_generated_at")
    current_age: float | None = None
    if last_market_event_time is not None:
        _require_aware(last_market_event_time, "last_market_event_time")
        current_age = float(
            (
                queried_at.astimezone(timezone.utc)
                - last_market_event_time.astimezone(timezone.utc)
            ).total_seconds()
        )

    values = dict(
        schema_version=OPERATOR_VIEW_SCHEMA,
        queried_at=queried_at.astimezone(timezone.utc),
        snapshot_generated_at=snapshot_generated_at.astimezone(timezone.utc),
        source=source,
        product_version=product_version,
        strategy_id=strategy_id,
        config_fingerprint=config_fingerprint,
        source_snapshot_fingerprint=source_snapshot_fingerprint,
        decision_id=decision_id,
        decision_action=decision_action,
        decision_blockers=decision_blockers,
        risk_state=risk_state,
        last_market_event_id=last_market_event_id,
        last_market_event_time=(
            last_market_event_time.astimezone(timezone.utc)
            if last_market_event_time is not None
            else None
        ),
        current_market_event_age_seconds=current_age,
        health_state=health_state,
        health_source=health_source,
        runtime_events=runtime_events,
        recovery_state=recovery_state,
        reconciliation_state=reconciliation_state,
    )
    provisional_payload = _values_payload(**values)
    return ProductOperatorViewV1(
        **values,
        view_fingerprint=_fingerprint(provisional_payload),
    )


def canonical_operator_view_json(view: ProductOperatorViewV1) -> str:
    return json.dumps(view.to_dict(), sort_keys=True, indent=2, ensure_ascii=True) + "\n"


def _identity_payload(view: ProductOperatorViewV1) -> dict[str, object]:
    return _values_payload(
        schema_version=view.schema_version,
        queried_at=view.queried_at,
        snapshot_generated_at=view.snapshot_generated_at,
        source=view.source,
        product_version=view.product_version,
        strategy_id=view.strategy_id,
        config_fingerprint=view.config_fingerprint,
        source_snapshot_fingerprint=view.source_snapshot_fingerprint,
        decision_id=view.decision_id,
        decision_action=view.decision_action,
        decision_blockers=view.decision_blockers,
        risk_state=view.risk_state,
        last_market_event_id=view.last_market_event_id,
        last_market_event_time=view.last_market_event_time,
        current_market_event_age_seconds=view.current_market_event_age_seconds,
        health_state=view.health_state,
        health_source=view.health_source,
        runtime_events=view.runtime_events,
        recovery_state=view.recovery_state,
        reconciliation_state=view.reconciliation_state,
    )


def _values_payload(
    *,
    schema_version: str,
    queried_at: datetime,
    snapshot_generated_at: datetime,
    source: str,
    product_version: str,
    strategy_id: str,
    config_fingerprint: str,
    source_snapshot_fingerprint: str,
    decision_id: str,
    decision_action: str,
    decision_blockers: tuple[str, ...],
    risk_state: str,
    last_market_event_id: str | None,
    last_market_event_time: datetime | None,
    current_market_event_age_seconds: float | None,
    health_state: str | None,
    health_source: str | None,
    runtime_events: tuple[str, ...],
    recovery_state: str | None,
    reconciliation_state: str | None,
) -> dict[str, object]:
    return {
        "schema_version": schema_version,
        "queried_at_utc": queried_at.astimezone(timezone.utc).isoformat(),
        "snapshot_generated_at_utc": snapshot_generated_at.astimezone(timezone.utc).isoformat(),
        "source": source,
        "product_version": product_version,
        "strategy_id": strategy_id,
        "config_fingerprint": config_fingerprint,
        "source_snapshot_fingerprint": source_snapshot_fingerprint,
        "decision": {
            "decision_id": decision_id,
            "action": decision_action,
            "blockers": list(decision_blockers),
            "risk_state": risk_state,
        },
        "market": {
            "last_event_id": last_market_event_id,
            "last_event_time_utc": (
                last_market_event_time.astimezone(timezone.utc).isoformat()
                if last_market_event_time is not None
                else None
            ),
            "current_event_age_seconds": current_market_event_age_seconds,
        },
        "runtime": {
            "health_state": health_state,
            "health_source": health_source,
            "events": list(runtime_events),
            "recovery_state": recovery_state,
            "reconciliation_state": reconciliation_state,
        },
        "safety": {
            "execution_capability": "NONE",
            "order_execution_enabled": False,
        },
    }


def _fingerprint(value: object) -> str:
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256(canonical.encode("utf-8")).hexdigest()


def _require_aware(value: datetime, field_name: str) -> None:
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")


def _require_text(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"{field_name} must be normalized non-empty text")


def _require_unique_text(values: tuple[str, ...], field_name: str) -> None:
    if any(not isinstance(value, str) or not value.strip() or value != value.strip() for value in values):
        raise ValueError(f"{field_name} must contain normalized non-empty text")
    if len(set(values)) != len(values):
        raise ValueError(f"{field_name} must be unique")


def _require_sha256(value: str, field_name: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{field_name} must be sha256 hex")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be sha256 hex") from exc
