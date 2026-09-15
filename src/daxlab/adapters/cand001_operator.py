"""Compatibility adapter from the existing CAND-001 operator current view.

The legacy/current Candidate operator payload remains its own evidence surface.
This adapter validates it again, then exposes only the generic read-only fields
owned by ``ProductOperatorViewV1``.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

from daxlab.operator.read_model import ProductOperatorViewV1, build_product_operator_view
from daxlab.runtime.candidate_operator_query import CandidateOperatorCurrent
from daxlab.runtime.candidate_operator_telemetry import validate_candidate_operator_snapshot


def candidate_current_to_product_operator_view(
    current: CandidateOperatorCurrent,
) -> ProductOperatorViewV1:
    """Map one validated Candidate current view into the generic operator boundary."""

    if current.execution_capability != "NONE" or current.order_execution_enabled:
        raise ValueError("Candidate current view cannot authorize execution")
    validate_candidate_operator_snapshot(current.payload)
    if str(current.payload["snapshot_fingerprint"]) != current.snapshot_fingerprint:
        raise ValueError("Candidate current-view snapshot fingerprint drift")
    if str(current.payload["generated_at"]) != current.snapshot_generated_at:
        raise ValueError("Candidate current-view generated_at drift")

    payload = current.payload
    decision = _section(payload, "decision")
    runtime = _section(payload, "runtime")

    blockers = _string_tuple(decision.get("blockers"), "decision.blockers")
    runtime_events = _string_tuple(runtime.get("events"), "runtime.events")
    queried_at = _parse_aware(current.queried_at_utc, "queried_at_utc")
    generated_at = _parse_aware(current.snapshot_generated_at, "snapshot_generated_at")

    last_event_time_raw = runtime.get("last_bar_close_time")
    last_event_time = (
        _parse_aware(str(last_event_time_raw), "runtime.last_bar_close_time")
        if last_event_time_raw is not None
        else None
    )

    view = build_product_operator_view(
        queried_at=queried_at,
        snapshot_generated_at=generated_at,
        source=current.source,
        product_version=_required_text(payload.get("core_version"), "core_version"),
        strategy_id=_required_text(payload.get("candidate_id"), "candidate_id"),
        config_fingerprint=_required_text(payload.get("config_fingerprint"), "config_fingerprint"),
        source_snapshot_fingerprint=current.snapshot_fingerprint,
        decision_id=_required_text(decision.get("decision_id"), "decision.decision_id"),
        decision_action=_required_text(decision.get("action"), "decision.action"),
        decision_blockers=blockers,
        risk_state=_required_text(decision.get("risk_result"), "decision.risk_result"),
        last_market_event_id=(
            _required_text(runtime.get("last_bar_id"), "runtime.last_bar_id")
            if runtime.get("last_bar_id") is not None
            else None
        ),
        last_market_event_time=last_event_time,
        health_state=(
            _required_text(runtime.get("health_state"), "runtime.health_state")
            if runtime.get("health_state") is not None
            else None
        ),
        health_source=(
            _required_text(runtime.get("health_source"), "runtime.health_source")
            if runtime.get("health_source") is not None
            else None
        ),
        runtime_events=runtime_events,
        recovery_state=(
            _required_text(runtime.get("recovery_state"), "runtime.recovery_state")
            if runtime.get("recovery_state") is not None
            else None
        ),
        reconciliation_state=(
            _required_text(runtime.get("reconciliation_state"), "runtime.reconciliation_state")
            if runtime.get("reconciliation_state") is not None
            else None
        ),
    )
    if view.current_market_event_age_seconds != current.current_bar_age_seconds:
        raise ValueError("Candidate current-view query-time freshness drift")
    return view


def _section(payload: Mapping[str, Any], name: str) -> Mapping[str, Any]:
    value = payload.get(name)
    if not isinstance(value, Mapping):
        raise ValueError(f"Candidate operator {name} section must be an object")
    return value


def _string_tuple(value: Any, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} must be a list")
    result = tuple(_required_text(item, field_name) for item in value)
    if len(set(result)) != len(result):
        raise ValueError(f"{field_name} must be unique")
    return result


def _parse_aware(value: str, field_name: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be ISO datetime") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return parsed


def _required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"{field_name} must be normalized non-empty text")
    return value
