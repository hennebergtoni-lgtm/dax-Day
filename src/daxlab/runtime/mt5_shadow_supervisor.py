"""Deterministic state transition for the Windows MT5 SHADOW supervisor.

This module has no MetaTrader5 dependency and no process-management capability.
It consumes credential-free Windows MT5 bundle payloads, evaluates the existing
validated SHADOW path, and returns heartbeat/resume state plus newly produced
NO_ORDER decisions for durable observation. It cannot place orders.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from daxlab.runtime.mt5_cross_cycle_integrity import evaluate_cross_cycle_integrity
from daxlab.runtime.mt5_shadow_integration import (
    Mt5ShadowResumeState,
    build_mt5_shadow_resume_state,
    evaluate_shadow_soak_from_bundle,
    mt5_shadow_resume_payload,
    parse_mt5_shadow_resume_payload,
)
from daxlab.runtime.mt5_windows_bundle import parse_windows_mt5_bundle
from daxlab.runtime.prospective_gate import ProspectiveAuthorization
from daxlab.runtime.shadow_observation import ShadowDecision

_HEARTBEAT_SCHEMA = "DAXLAB_MT5_SHADOW_HEARTBEAT_V1"
_FORBIDDEN_KEYS = frozenset(
    {"login", "password", "token", "secret", "email", "phone", "account_id"}
)


@dataclass(frozen=True, slots=True)
class SupervisorCycleResult:
    heartbeat: dict[str, Any]
    resume_state: Mt5ShadowResumeState | None
    decisions: tuple[ShadowDecision, ...] = ()


def with_history_archive_status(
    heartbeat: Mapping[str, Any], *, archived: bool
) -> dict[str, Any]:
    """Annotate evidence archival status without changing NO_ORDER safety fields."""
    _assert_credential_free(heartbeat)
    if heartbeat.get("execution_capability") != "NONE":
        raise ValueError("heartbeat execution_capability must be NONE")
    if heartbeat.get("order_execution_enabled") is not False:
        raise ValueError("heartbeat order_execution_enabled must be false")
    annotated = dict(heartbeat)
    annotated["history_archive_status"] = "OK" if archived else "FAILED"
    if annotated.get("execution_capability") != "NONE":
        raise RuntimeError("history status changed execution capability")
    if annotated.get("order_execution_enabled") is not False:
        raise RuntimeError("history status enabled order execution")
    _assert_credential_free(annotated)
    return annotated


def shadow_authorization() -> ProspectiveAuthorization:
    """Return the fixed research authorization scope for read-only SHADOW only."""
    return ProspectiveAuthorization(
        gate_id="STEP_91_USER_AUTHORIZATION",
        shadow_authorized=True,
        paper_authorized=False,
        live_authorized=False,
    )


def process_mt5_shadow_cycle(
    bundle_payload: Mapping[str, Any],
    *,
    resume_state: Mt5ShadowResumeState | None = None,
    single_instance_lock_held: bool,
    observed_at: datetime | None = None,
    previous_bundle_payload: Mapping[str, Any] | None = None,
) -> SupervisorCycleResult:
    """Validate one broker bundle and produce credential-free NO_ORDER evidence."""
    now = observed_at or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("supervisor observed_at must be timezone-aware")

    bundle = parse_windows_mt5_bundle(bundle_payload)
    cross_cycle_status = "NOT_AVAILABLE"
    cross_cycle_overlapping_bars = 0
    cross_cycle_identical_overlaps = 0
    cross_cycle_mutated_overlaps = 0

    if previous_bundle_payload is not None:
        previous_bundle = parse_windows_mt5_bundle(previous_bundle_payload)
        if previous_bundle.feed is not None and bundle.feed is not None:
            integrity = evaluate_cross_cycle_integrity(previous_bundle.feed, bundle.feed)
            cross_cycle_status = integrity.status
            cross_cycle_overlapping_bars = integrity.overlapping_bars
            cross_cycle_identical_overlaps = integrity.identical_overlaps
            cross_cycle_mutated_overlaps = integrity.mutated_overlaps
            if integrity.blockers:
                symbol = bundle.host.symbols[0].name if bundle.host.symbols else None
                blockers = list(dict.fromkeys([*bundle.blockers, *integrity.blockers]))
                heartbeat = {
                    "schema_version": _HEARTBEAT_SCHEMA,
                    "observed_at_utc": now.astimezone(timezone.utc).isoformat(),
                    "status": "BLOCKED",
                    "blockers": blockers,
                    "symbol": symbol,
                    "bundle_sha256": bundle.fingerprint,
                    "closed_m5_bars": len(bundle.feed.bars),
                    "latest_closed_bar_age_seconds": bundle.feed.age_seconds,
                    "single_instance_lock_held": single_instance_lock_held,
                    "processed_total": None,
                    "new_decisions": 0,
                    "duplicates_suppressed": 0,
                    "evidence_state": None,
                    "cross_cycle_status": cross_cycle_status,
                    "cross_cycle_overlapping_bars": cross_cycle_overlapping_bars,
                    "cross_cycle_identical_overlaps": cross_cycle_identical_overlaps,
                    "cross_cycle_mutated_overlaps": cross_cycle_mutated_overlaps,
                    "execution_capability": "NONE",
                    "order_execution_enabled": False,
                }
                _assert_credential_free(heartbeat)
                return SupervisorCycleResult(heartbeat=heartbeat, resume_state=None)

    gate, result, status = evaluate_shadow_soak_from_bundle(
        bundle,
        authorization=shadow_authorization(),
        single_instance_lock_held=single_instance_lock_held,
        resume_state=resume_state,
    )

    new_resume: Mt5ShadowResumeState | None = None
    decisions: tuple[ShadowDecision, ...] = ()
    if gate.allowed:
        if result is None or status.symbol is None:
            raise RuntimeError("allowed MT5 SHADOW gate produced no result")
        decisions = result.decisions
        if any(item.action != "NO_ORDER" for item in decisions):
            raise RuntimeError("MT5 SHADOW supervisor received non-NO_ORDER decision")
        new_resume = build_mt5_shadow_resume_state(
            symbol=status.symbol,
            checkpoint=result.checkpoint,
        )

    heartbeat = {
        "schema_version": _HEARTBEAT_SCHEMA,
        "observed_at_utc": now.astimezone(timezone.utc).isoformat(),
        "status": "GREEN" if gate.allowed else "BLOCKED",
        "blockers": list(status.blockers),
        "symbol": status.symbol,
        "bundle_sha256": bundle.fingerprint,
        "closed_m5_bars": status.closed_m5_bars,
        "latest_closed_bar_age_seconds": status.latest_closed_bar_age_seconds,
        "single_instance_lock_held": single_instance_lock_held,
        "processed_total": result.processed if result is not None else None,
        "new_decisions": len(decisions),
        "duplicates_suppressed": result.duplicates_suppressed if result is not None else 0,
        "evidence_state": result.evidence_state if result is not None else None,
        "cross_cycle_status": cross_cycle_status,
        "cross_cycle_overlapping_bars": cross_cycle_overlapping_bars,
        "cross_cycle_identical_overlaps": cross_cycle_identical_overlaps,
        "cross_cycle_mutated_overlaps": cross_cycle_mutated_overlaps,
        "execution_capability": "NONE",
        "order_execution_enabled": False,
    }
    _assert_credential_free(heartbeat)
    if new_resume is not None:
        _assert_credential_free(mt5_shadow_resume_payload(new_resume))
    return SupervisorCycleResult(
        heartbeat=heartbeat,
        resume_state=new_resume,
        decisions=decisions,
    )


def load_mt5_resume_payload(payload: Mapping[str, Any]) -> Mt5ShadowResumeState:
    """Strict loader used by the disk-backed Windows loop."""
    _assert_credential_free(payload)
    return parse_mt5_shadow_resume_payload(payload)


def supervisor_error_heartbeat(
    *,
    observed_at: datetime | None = None,
    error_code: str,
) -> dict[str, Any]:
    """Build a bounded error heartbeat without echoing exception text or secrets."""
    now = observed_at or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("supervisor observed_at must be timezone-aware")
    clean_code = error_code.strip().upper()
    if not clean_code or not clean_code.replace("_", "").isalnum():
        raise ValueError("supervisor error_code must be an identifier")
    heartbeat = {
        "schema_version": _HEARTBEAT_SCHEMA,
        "observed_at_utc": now.astimezone(timezone.utc).isoformat(),
        "status": "ERROR",
        "blockers": [clean_code],
        "symbol": None,
        "bundle_sha256": None,
        "closed_m5_bars": 0,
        "latest_closed_bar_age_seconds": None,
        "single_instance_lock_held": True,
        "processed_total": None,
        "new_decisions": 0,
        "duplicates_suppressed": 0,
        "evidence_state": None,
        "cross_cycle_status": "NOT_AVAILABLE",
        "cross_cycle_overlapping_bars": 0,
        "cross_cycle_identical_overlaps": 0,
        "cross_cycle_mutated_overlaps": 0,
        "execution_capability": "NONE",
        "order_execution_enabled": False,
    }
    _assert_credential_free(heartbeat)
    return heartbeat


def supervisor_stopped_heartbeat(*, observed_at: datetime | None = None) -> dict[str, Any]:
    now = observed_at or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("supervisor observed_at must be timezone-aware")
    heartbeat = {
        "schema_version": _HEARTBEAT_SCHEMA,
        "observed_at_utc": now.astimezone(timezone.utc).isoformat(),
        "status": "STOPPED",
        "blockers": [],
        "symbol": None,
        "bundle_sha256": None,
        "closed_m5_bars": 0,
        "latest_closed_bar_age_seconds": None,
        "single_instance_lock_held": False,
        "processed_total": None,
        "new_decisions": 0,
        "duplicates_suppressed": 0,
        "evidence_state": None,
        "cross_cycle_status": "NOT_AVAILABLE",
        "cross_cycle_overlapping_bars": 0,
        "cross_cycle_identical_overlaps": 0,
        "cross_cycle_mutated_overlaps": 0,
        "execution_capability": "NONE",
        "order_execution_enabled": False,
    }
    _assert_credential_free(heartbeat)
    return heartbeat


def _assert_credential_free(payload: Mapping[str, Any]) -> None:
    def walk(value: Any) -> None:
        if isinstance(value, Mapping):
            for key, item in value.items():
                if str(key).lower() in _FORBIDDEN_KEYS:
                    raise RuntimeError(f"forbidden supervisor output key: {key}")
                walk(item)
        elif isinstance(value, (list, tuple)):
            for item in value:
                walk(item)

    walk(payload)
