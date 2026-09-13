"""Credential-free read-only operator snapshot for DAX-BOT 1.x.

The snapshot separates the current strategy decision from any still-open or just-
closed virtual position. A position may originate from an earlier TRADE decision
while the current bar legitimately produces a later NO_TRADE decision.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from datetime import datetime, timedelta, timezone
from math import isfinite
from typing import Any, Mapping

from daxlab.runtime.candidate_operator_query import build_candidate_operator_current
from daxlab.runtime.candidate_operator_telemetry import (
    _assert_credential_free,
    operator_timestamp,
    validate_candidate_operator_snapshot,
)
from daxlab.runtime.mt5_windows_bundle import parse_windows_mt5_bundle

from daxlab.runtime.candidate_admission import AdmissionStatus, Cand001AdmissionResult
from daxlab.runtime.candidate_config import Cand001Config
from daxlab.runtime.candidate_signal import Cand001Signal
from daxlab.runtime.candidate_trade_plan import Cand001TradePlan
from daxlab.runtime.candidate_virtual_lifecycle import (
    Cand001VirtualLifecycleState,
    VirtualPositionStatus,
)
from daxlab.runtime.candidate_virtual_outcome import Cand001VirtualOutcomeEvidence
from daxlab.runtime.decision import DecisionRecord, FinalAction, stable_fingerprint


SCHEMA_VERSION = "DAX_BOT_OPERATOR_SNAPSHOT_V3"


@dataclass(frozen=True, slots=True)
class OperatorSnapshot:
    schema_version: str
    generated_at: datetime
    core_version: str
    candidate_id: str
    config_fingerprint: str
    regime: str
    structure: str
    setup: str
    signal_direction: str
    signal_reason: str
    admission_status: str
    decision_action: str
    decision_id: str
    blockers: tuple[str, ...]
    risk_result: str
    proposed_entry: float | None
    proposed_stop: float | None
    proposed_target: float | None
    proposed_reward_risk: float | None
    last_bar_id: str | None
    last_bar_close_time: datetime | None
    freshness_seconds: float | None
    health_state: str | None
    health_source: str | None
    runtime_events: tuple[str, ...]
    recovery_state: str | None
    reconciliation_state: str | None
    virtual_lifecycle_id: str | None
    virtual_decision_id: str | None
    virtual_status: str | None
    virtual_side: str | None
    virtual_filled_at: datetime | None
    virtual_filled_price: float | None
    virtual_closed_at: datetime | None
    virtual_exit_price: float | None
    virtual_exit_reason: str | None
    outcome_id: str | None
    outcome_gross_r: float | None
    outcome_cost_r: float | None
    outcome_net_r: float | None
    execution_capability: str
    order_execution_enabled: bool
    snapshot_fingerprint: str

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError("operator snapshot schema mismatch")
        if self.generated_at.tzinfo is None:
            raise ValueError("generated_at must be timezone-aware")
        for value in (
            self.last_bar_close_time,
            self.virtual_filled_at,
            self.virtual_closed_at,
        ):
            if value is not None and value.tzinfo is None:
                raise ValueError("operator snapshot timestamps must be timezone-aware")

        runtime_values = (
            self.last_bar_id,
            self.last_bar_close_time,
            self.freshness_seconds,
        )
        if any(value is not None for value in runtime_values) and any(
            value is None for value in runtime_values
        ):
            raise ValueError("operator runtime bar context must be complete")
        if self.last_bar_id is not None:
            _sha(self.last_bar_id, "last_bar_id")
            assert self.last_bar_close_time is not None
            assert self.freshness_seconds is not None
            if type(self.freshness_seconds) not in (int, float) or not isfinite(self.freshness_seconds) or self.freshness_seconds < 0:
                raise ValueError("freshness_seconds cannot be negative")
            if self.generated_at < self.last_bar_close_time:
                raise ValueError("operator snapshot cannot precede last closed bar")

        if (self.health_state is None) != (self.health_source is None):
            raise ValueError("health_state and health_source must be supplied together")
        if self.health_state is not None and not self.health_state.strip():
            raise ValueError("health_state must be non-empty")
        if self.health_source is not None and not self.health_source.strip():
            raise ValueError("health_source must be non-empty")
        if any(not event.strip() for event in self.runtime_events):
            raise ValueError("runtime_events must be non-empty strings")
        if len(set(self.runtime_events)) != len(self.runtime_events):
            raise ValueError("runtime_events must be unique")

        if self.execution_capability != "NONE":
            raise ValueError("operator snapshot cannot carry execution capability")
        if self.order_execution_enabled is not False:
            raise ValueError("operator snapshot cannot enable order execution")

        _sha(self.config_fingerprint, "config_fingerprint")
        _sha(self.decision_id, "decision_id")
        if self.virtual_lifecycle_id is not None:
            _sha(self.virtual_lifecycle_id, "virtual_lifecycle_id")
        if self.virtual_decision_id is not None:
            _sha(self.virtual_decision_id, "virtual_decision_id")
        if (self.virtual_lifecycle_id is None) != (self.virtual_decision_id is None):
            raise ValueError("virtual lifecycle and origin decision identity must be paired")
        if self.outcome_id is not None:
            _sha(self.outcome_id, "outcome_id")
        _sha(self.snapshot_fingerprint, "snapshot_fingerprint")

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at.isoformat(),
            "core_version": self.core_version,
            "candidate_id": self.candidate_id,
            "config_fingerprint": self.config_fingerprint,
            "strategy": {
                "regime": self.regime,
                "structure": self.structure,
                "setup": self.setup,
            },
            "signal": {
                "direction": self.signal_direction,
                "reason": self.signal_reason,
            },
            "admission": {"status": self.admission_status},
            "decision": {
                "action": self.decision_action,
                "decision_id": self.decision_id,
                "blockers": list(self.blockers),
                "risk_result": self.risk_result,
            },
            "trade_plan": {
                "entry": self.proposed_entry,
                "stop": self.proposed_stop,
                "target": self.proposed_target,
                "reward_risk": self.proposed_reward_risk,
            },
            "runtime": {
                "last_bar_id": self.last_bar_id,
                "last_bar_close_time": (
                    self.last_bar_close_time.isoformat()
                    if self.last_bar_close_time is not None
                    else None
                ),
                "freshness_seconds": self.freshness_seconds,
                "health_state": self.health_state,
                "health_source": self.health_source,
                "events": list(self.runtime_events),
                "recovery_state": self.recovery_state,
                "reconciliation_state": self.reconciliation_state,
            },
            "virtual_position": {
                "lifecycle_id": self.virtual_lifecycle_id,
                "origin_decision_id": self.virtual_decision_id,
                "status": self.virtual_status,
                "side": self.virtual_side,
                "filled_at": (
                    self.virtual_filled_at.isoformat()
                    if self.virtual_filled_at is not None
                    else None
                ),
                "filled_price": self.virtual_filled_price,
                "closed_at": (
                    self.virtual_closed_at.isoformat()
                    if self.virtual_closed_at is not None
                    else None
                ),
                "exit_price": self.virtual_exit_price,
                "exit_reason": self.virtual_exit_reason,
            },
            "outcome": {
                "outcome_id": self.outcome_id,
                "gross_r": self.outcome_gross_r,
                "cost_r": self.outcome_cost_r,
                "net_r": self.outcome_net_r,
            },
            "safety": {
                "execution_capability": self.execution_capability,
                "order_execution_enabled": self.order_execution_enabled,
            },
            "snapshot_fingerprint": self.snapshot_fingerprint,
        }


def build_operator_snapshot(
    *,
    generated_at: datetime,
    config: Cand001Config,
    signal: Cand001Signal,
    proposed_trade_plan: Cand001TradePlan | None,
    admission: Cand001AdmissionResult,
    decision: DecisionRecord,
    last_bar_id: str | None = None,
    last_bar_close_time: datetime | None = None,
    freshness_seconds: float | None = None,
    health_state: str | None = None,
    health_source: str | None = None,
    runtime_events: tuple[str, ...] = (),
    recovery_state: str | None = None,
    reconciliation_state: str | None = None,
    lifecycle: Cand001VirtualLifecycleState | None = None,
    outcome: Cand001VirtualOutcomeEvidence | None = None,
) -> OperatorSnapshot:
    """Build a read-only current-decision view plus independent position context."""
    if generated_at.tzinfo is None:
        raise ValueError("generated_at must be timezone-aware")
    identity = config.product_identity()

    if decision.event_time != signal.close_time:
        raise ValueError("decision time must match closed signal time")
    if decision.data_fingerprint != signal.data_fingerprint:
        raise ValueError("decision provenance must match signal data fingerprint")

    if admission.status is AdmissionStatus.ALLOWED:
        if admission.admitted_plan is None or decision.final_action is not FinalAction.TRADE:
            raise ValueError("ALLOWED admission must map to TRADE decision")
    elif decision.final_action is FinalAction.TRADE:
        raise ValueError("non-ALLOWED admission cannot map to TRADE decision")

    if proposed_trade_plan is not None:
        if proposed_trade_plan.signal_data_fingerprint != signal.data_fingerprint:
            raise ValueError("proposed trade-plan provenance mismatch")
        entry = proposed_trade_plan.entry_price
        stop = proposed_trade_plan.stop_price
        target = proposed_trade_plan.target_price
        reward_risk = proposed_trade_plan.reward_risk
    else:
        entry = stop = target = reward_risk = None

    runtime_fields = _runtime_fields(
        generated_at=generated_at,
        last_bar_id=last_bar_id,
        last_bar_close_time=last_bar_close_time,
        freshness_seconds=freshness_seconds,
        health_state=health_state,
        health_source=health_source,
        runtime_events=runtime_events,
        recovery_state=recovery_state,
        reconciliation_state=reconciliation_state,
    )
    lifecycle_fields = _lifecycle_fields(
        generated_at=generated_at,
        lifecycle=lifecycle,
    )
    outcome_fields = _outcome_fields(
        generated_at=generated_at,
        lifecycle=lifecycle,
        outcome=outcome,
    )

    payload = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "core_version": identity.core_version,
        "candidate_id": identity.candidate_id,
        "config_fingerprint": identity.config_fingerprint,
        "regime": decision.regime,
        "structure": decision.structure,
        "setup": decision.setup,
        "signal_direction": signal.direction.value,
        "signal_reason": signal.reason.value,
        "admission_status": admission.status.value,
        "decision_action": decision.final_action.value,
        "decision_id": decision.decision_id,
        "blockers": decision.blockers,
        "risk_result": decision.risk_result,
        "proposed_entry": entry,
        "proposed_stop": stop,
        "proposed_target": target,
        "proposed_reward_risk": reward_risk,
        **runtime_fields,
        **lifecycle_fields,
        **outcome_fields,
        "execution_capability": "NONE",
        "order_execution_enabled": False,
    }
    return OperatorSnapshot(
        **payload,
        snapshot_fingerprint=stable_fingerprint(payload),
    )


def _runtime_fields(
    *,
    generated_at: datetime,
    last_bar_id: str | None,
    last_bar_close_time: datetime | None,
    freshness_seconds: float | None,
    health_state: str | None,
    health_source: str | None,
    runtime_events: tuple[str, ...],
    recovery_state: str | None,
    reconciliation_state: str | None,
) -> dict[str, object]:
    values = (last_bar_id, last_bar_close_time, freshness_seconds)
    if all(value is None for value in values):
        bar_fields: dict[str, object] = {
            "last_bar_id": None,
            "last_bar_close_time": None,
            "freshness_seconds": None,
        }
    else:
        if any(value is None for value in values):
            raise ValueError("operator runtime bar context must be complete")
        assert last_bar_id is not None
        assert last_bar_close_time is not None
        assert freshness_seconds is not None
        _sha(last_bar_id, "last_bar_id")
        if last_bar_close_time.tzinfo is None:
            raise ValueError("last_bar_close_time must be timezone-aware")
        if type(freshness_seconds) not in (int, float) or not isfinite(freshness_seconds) or freshness_seconds < 0:
            raise ValueError("freshness_seconds cannot be negative")
        if generated_at < last_bar_close_time:
            raise ValueError("operator snapshot cannot precede last closed bar")
        bar_fields = {
            "last_bar_id": last_bar_id,
            "last_bar_close_time": last_bar_close_time,
            "freshness_seconds": float(freshness_seconds),
        }

    if (health_state is None) != (health_source is None):
        raise ValueError("health_state and health_source must be supplied together")
    if health_state is not None and not health_state.strip():
        raise ValueError("health_state must be non-empty")
    if health_source is not None and not health_source.strip():
        raise ValueError("health_source must be non-empty")

    events = tuple(dict.fromkeys(runtime_events))
    if any(not isinstance(event, str) or not event.strip() for event in events):
        raise ValueError("runtime_events must be non-empty strings")
    for value, field in (
        (recovery_state, "recovery_state"),
        (reconciliation_state, "reconciliation_state"),
    ):
        if value is not None and (not isinstance(value, str) or not value.strip()):
            raise ValueError(f"{field} must be non-empty string or null")

    return {
        **bar_fields,
        "health_state": health_state,
        "health_source": health_source,
        "runtime_events": events,
        "recovery_state": recovery_state,
        "reconciliation_state": reconciliation_state,
    }


def _lifecycle_fields(
    *,
    generated_at: datetime,
    lifecycle: Cand001VirtualLifecycleState | None,
) -> dict[str, object]:
    if lifecycle is None:
        return {
            "virtual_lifecycle_id": None,
            "virtual_decision_id": None,
            "virtual_status": None,
            "virtual_side": None,
            "virtual_filled_at": None,
            "virtual_filled_price": None,
            "virtual_closed_at": None,
            "virtual_exit_price": None,
            "virtual_exit_reason": None,
        }

    if generated_at < lifecycle.requested_at:
        raise ValueError("operator snapshot cannot observe a future virtual request")
    if lifecycle.filled_at is not None and generated_at < lifecycle.filled_at:
        raise ValueError("operator snapshot cannot observe a future virtual fill")
    if lifecycle.closed_at is not None and generated_at < lifecycle.closed_at:
        raise ValueError("operator snapshot cannot observe a future virtual close")

    return {
        "virtual_lifecycle_id": lifecycle.lifecycle_id,
        "virtual_decision_id": lifecycle.decision_id,
        "virtual_status": lifecycle.status.value,
        "virtual_side": lifecycle.side.value,
        "virtual_filled_at": lifecycle.filled_at,
        "virtual_filled_price": lifecycle.filled_price,
        "virtual_closed_at": lifecycle.closed_at,
        "virtual_exit_price": lifecycle.exit_price,
        "virtual_exit_reason": (
            lifecycle.exit_reason.value
            if lifecycle.status is VirtualPositionStatus.CLOSED
            else None
        ),
    }


def _outcome_fields(
    *,
    generated_at: datetime,
    lifecycle: Cand001VirtualLifecycleState | None,
    outcome: Cand001VirtualOutcomeEvidence | None,
) -> dict[str, object]:
    if outcome is None:
        return {
            "outcome_id": None,
            "outcome_gross_r": None,
            "outcome_cost_r": None,
            "outcome_net_r": None,
        }
    if lifecycle is None or lifecycle.status is not VirtualPositionStatus.CLOSED:
        raise ValueError("virtual outcome requires CLOSED lifecycle in operator snapshot")
    if outcome.decision_id != lifecycle.decision_id:
        raise ValueError("virtual outcome origin decision identity drift")
    if outcome.lifecycle_id != lifecycle.lifecycle_id:
        raise ValueError("virtual outcome lifecycle identity drift")
    if generated_at < outcome.closed_at:
        raise ValueError("operator snapshot cannot observe a future virtual outcome")
    return {
        "outcome_id": outcome.outcome_id,
        "outcome_gross_r": outcome.gross_r,
        "outcome_cost_r": outcome.cost_r,
        "outcome_net_r": outcome.net_r,
    }


def _sha(value: str, field: str) -> None:
    if len(value) != 64:
        raise ValueError(f"{field} must be sha256 hex")
    int(value, 16)


CONSOLE_SCHEMA = "DAXLAB_READONLY_OPERATOR_CONSOLE_V1"


def parse_operator_snapshot_payload(payload: Mapping[str, Any]) -> OperatorSnapshot:
    """Reconstruct the existing V3 contract and verify its ORIGINAL flat digest.

    No new strategy/state schema or fingerprint contract. Unknown fields cannot
    become a browser-side passthrough. Legacy telemetry validators remain usable.
    """
    validate_candidate_operator_snapshot(payload)
    root_fields = {
        "schema_version", "generated_at", "core_version", "candidate_id",
        "config_fingerprint", "snapshot_fingerprint",
    }
    sections = {
        "strategy": {"regime": "regime", "structure": "structure", "setup": "setup"},
        "signal": {"direction": "signal_direction", "reason": "signal_reason"},
        "admission": {"status": "admission_status"},
        "decision": {
            "action": "decision_action", "decision_id": "decision_id",
            "blockers": "blockers", "risk_result": "risk_result",
        },
        "trade_plan": {
            "entry": "proposed_entry", "stop": "proposed_stop",
            "target": "proposed_target", "reward_risk": "proposed_reward_risk",
        },
        "runtime": {
            "last_bar_id": "last_bar_id", "last_bar_close_time": "last_bar_close_time",
            "freshness_seconds": "freshness_seconds", "health_state": "health_state",
            "health_source": "health_source", "events": "runtime_events",
            "recovery_state": "recovery_state", "reconciliation_state": "reconciliation_state",
        },
        "virtual_position": {
            "lifecycle_id": "virtual_lifecycle_id", "origin_decision_id": "virtual_decision_id",
            "status": "virtual_status", "side": "virtual_side",
            "filled_at": "virtual_filled_at", "filled_price": "virtual_filled_price",
            "closed_at": "virtual_closed_at", "exit_price": "virtual_exit_price",
            "exit_reason": "virtual_exit_reason",
        },
        "outcome": {
            "outcome_id": "outcome_id", "gross_r": "outcome_gross_r",
            "cost_r": "outcome_cost_r", "net_r": "outcome_net_r",
        },
        "safety": {
            "execution_capability": "execution_capability",
            "order_execution_enabled": "order_execution_enabled",
        },
    }
    if set(payload) != root_fields | set(sections):
        raise ValueError("operator snapshot field set mismatch")
    values = {key: payload[key] for key in root_fields}
    for section, names in sections.items():
        raw = payload[section]
        if not isinstance(raw, Mapping) or set(raw) != set(names):
            raise ValueError("operator snapshot section field set mismatch")
        values.update({target: raw[key] for key, target in names.items()})
    for name in ("generated_at", "last_bar_close_time", "virtual_filled_at", "virtual_closed_at"):
        if values[name] is not None:
            values[name] = operator_timestamp(values[name], name)
    for name in ("blockers", "runtime_events"):
        if not isinstance(values[name], list) or any(
            not isinstance(v, str) or not v.strip() for v in values[name]
        ):
            raise ValueError("operator event/blocker list invalid")
        values[name] = tuple(values[name])
    snapshot = OperatorSnapshot(**values)
    original = {f.name: getattr(snapshot, f.name) for f in fields(snapshot) if f.name != "snapshot_fingerprint"}
    if stable_fingerprint(original) != snapshot.snapshot_fingerprint:
        raise ValueError("operator snapshot original fingerprint mismatch")
    return snapshot


def build_operator_console_projection(
    *, snapshot_payload: Mapping[str, Any] | None,
    bundle_payload: Mapping[str, Any] | None,
    heartbeat_payload: Mapping[str, Any] | None,
    queried_at: datetime,
) -> dict[str, Any]:
    """Project canonical observations; NEVER evaluate readiness or grant execution.

    Feed age uses its source-bound limit. Snapshot/host age has no reviewed maximum
    here, hence UNKNOWN / UNVERIFIED_THRESHOLD. Fetch time is supplied by the UI
    separately and cannot renew any source observation.
    """
    if queried_at.tzinfo is None or queried_at.utcoffset() is None:
        raise ValueError("operator queried_at must be timezone-aware")
    now = queried_at.astimezone(timezone.utc)
    snapshot = parse_operator_snapshot_payload(snapshot_payload) if snapshot_payload is not None else None
    current = build_candidate_operator_current(snapshot.as_dict(), queried_at=now) if snapshot else None
    for value in (bundle_payload, heartbeat_payload):
        if value is not None:
            _assert_credential_free(value)
    bundle = parse_windows_mt5_bundle(bundle_payload) if bundle_payload is not None else None
    heartbeat_at = None
    if heartbeat_payload is not None:
        if (
            heartbeat_payload.get("schema_version") != "DAXLAB_MT5_SHADOW_HEARTBEAT_V1"
            or heartbeat_payload.get("status") not in {"GREEN", "BLOCKED", "ERROR", "STOPPED"}
            or heartbeat_payload.get("execution_capability") != "NONE"
            or heartbeat_payload.get("order_execution_enabled") is not False
        ):
            raise ValueError("operator heartbeat contract invalid")
        heartbeat_at = operator_timestamp(heartbeat_payload.get("observed_at_utc"), "heartbeat observed_at")
        _observation_age(now, heartbeat_at)
        raw_blockers = heartbeat_payload.get("blockers")
        if not isinstance(raw_blockers, list) or any(not isinstance(v, str) for v in raw_blockers):
            raise ValueError("operator heartbeat blockers invalid")
    blockers = list(snapshot.blockers) if snapshot else ["CANDIDATE_SNAPSHOT_MISSING"]
    if heartbeat_payload is None:
        blockers.append("SUPERVISOR_HEARTBEAT_MISSING")
    elif heartbeat_payload["status"] != "GREEN":
        blockers.extend(["SUPERVISOR_NOT_GREEN", *heartbeat_payload["blockers"]])
    if bundle is None:
        blockers.append("HOST_BUNDLE_MISSING")
    else:
        blockers.extend(bundle.blockers)
        if heartbeat_payload is None or heartbeat_payload.get("bundle_sha256") != bundle.fingerprint:
            blockers.append("HEARTBEAT_BUNDLE_CYCLE_MISMATCH")
        if heartbeat_payload is not None and bundle.host.symbols and heartbeat_payload.get("symbol") != bundle.host.symbols[0].name:
            blockers.append("HEARTBEAT_SYMBOL_MISMATCH")
        _observation_age(now, bundle.host.observed_at)
    feed = bundle.feed if bundle else None
    feed_at = feed.observed_at if feed else None
    close_time = feed.bars[-1].open_time + timedelta(minutes=5) if feed else None
    feed_age = _observation_age(now, close_time) if close_time else None
    max_feed_age = bundle_payload["closed_m5_feed"]["max_age_seconds"] if feed else None
    if feed:
        _observation_age(now, feed.observed_at)
        if bundle.host.observed_at != feed.observed_at:
            blockers.append("HOST_FEED_OBSERVATION_CYCLE_MISMATCH")
        if feed_age > max_feed_age:
            blockers.append("MARKET_DATA_STALE_AT_QUERY")
        if snapshot and snapshot.last_bar_close_time != close_time:
            blockers.append("CANDIDATE_BEHIND_OR_DIFFERENT_FEED")
    ctx = bundle.demo_account_context if bundle else None
    if ctx is None:
        blockers.append("DEMO_ACCOUNT_CONTEXT_MISSING")
    elif ctx.account_mode.value != "DEMO":
        blockers.append("ACCOUNT_MODE_NOT_DEMO")
    if feed is None or not feed.broker_timezone or feed.timestamp_interpretation != "EXPLICIT_BROKER_WALL_CLOCK":
        blockers.append("EXPLICIT_BROKER_TIME_CONTEXT_MISSING")
    elif bundle_payload["host_probe"].get("broker_timezone") != feed.broker_timezone:
        blockers.append("HOST_FEED_TIMEZONE_MISMATCH")
    if ctx and bundle.host.symbols and ctx.symbol != bundle.host.symbols[0].name:
        blockers.append("ACCOUNT_SYMBOL_MISMATCH")
    # These are evidence boundaries, independent of observed strategy ALLOWED.
    blockers.extend([
        "SNAPSHOT_FRESHNESS_THRESHOLD_UNVERIFIED", "HOST_FRESHNESS_THRESHOLD_UNVERIFIED",
        "ACCOUNT_WIDE_INVENTORY_NOT_VERIFIED", "BROKER_HISTORY_COMPLETENESS_NOT_VERIFIED",
        "DEMO_PAPER_EXECUTION_NOT_AUTHORIZED",
    ])
    host = bundle.host if bundle else None
    feed_state = "UNKNOWN" if not feed else "GREEN"
    if feed and feed_age > max_feed_age:
        feed_state = "STALE"
    elif feed and (not bundle.green or any(v in blockers for v in (
        "SUPERVISOR_NOT_GREEN", "HEARTBEAT_BUNDLE_CYCLE_MISMATCH",
        "HEARTBEAT_SYMBOL_MISMATCH", "HOST_FEED_OBSERVATION_CYCLE_MISMATCH",
        "HOST_FEED_TIMEZONE_MISMATCH", "ACCOUNT_SYMBOL_MISMATCH",
    ))):
        feed_state = "BLOCKED"
    snapshot_state = "STALE" if "CANDIDATE_BEHIND_OR_DIFFERENT_FEED" in blockers else "UNKNOWN"
    tiles = {
        "BOT MODE": _tile("WARN" if snapshot and heartbeat_payload else "UNKNOWN", "SHADOW observation only"),
        "HOST": _tile("BLOCKED" if host and not host.engine_loop_healthy else "UNKNOWN", "UNVERIFIED_THRESHOLD"),
        "MT5": _tile("BLOCKED" if host and not host.terminal_connected else "UNKNOWN", "connected observed" if host and host.terminal_connected else "connection unknown/down"),
        "FEED": _tile(feed_state, "CLOSED-M5" if feed else "MISSING"),
        "CLOCK": _tile("BLOCKED" if host and not host.clock_ok else "UNKNOWN", feed.broker_timezone if feed else None),
        "ACCOUNT MODE": _tile("BLOCKED" if ctx and ctx.account_mode.value != "DEMO" else "UNKNOWN", ctx.account_mode.value if ctx else None),
        "SYMBOL": _tile("UNKNOWN", host.symbols[0].name if host and host.symbols else None),
        "PROTECTION": _tile("WAITING_EXTERNAL", "no current bound verdict"),
        "RECONCILIATION": _tile("UNKNOWN", "account-wide venue evidence missing"),
        "SNAPSHOT AGE": _tile(snapshot_state, "UNVERIFIED_THRESHOLD"),
        "EXECUTION": _tile("BLOCKED", "NONE / disabled"),
    }
    projection = {
        "schema_version": CONSOLE_SCHEMA,
        "queried_at_utc": now.isoformat(),
        "state": "BLOCKED", "source": "existing_local_supervisor_artifacts",
        "system": tiles, "blockers": list(dict.fromkeys(blockers)),
        "candidate": snapshot.as_dict() if snapshot else None,
        "timestamps": {
            "snapshot_generated_at": snapshot.generated_at.isoformat() if snapshot else None,
            "snapshot_age_seconds": _observation_age(now, snapshot.generated_at) if snapshot else None,
            "snapshot_age_threshold": "UNVERIFIED_THRESHOLD",
            "last_closed_m5_close_time": close_time.isoformat() if close_time else None,
            "current_feed_age_seconds": feed_age, "source_max_feed_age_seconds": max_feed_age,
            "snapshot_measured_bar_age_seconds": snapshot.freshness_seconds if snapshot else None,
            "candidate_current_bar_age_seconds": current.current_bar_age_seconds if current else None,
            "host_observed_at": host.observed_at.isoformat() if host else None,
            "host_age_seconds": _observation_age(now, host.observed_at) if host else None,
            "host_age_threshold": "UNVERIFIED_THRESHOLD",
            "heartbeat_observed_at": heartbeat_at.isoformat() if heartbeat_at else None,
            "feed_observed_at": feed_at.isoformat() if feed_at else None,
            "broker_tick_observed_at": None,
        },
        "host_observation": {
            "terminal_connected": host.terminal_connected if host else None,
            "account_connected": host.account_connected if host else None,
            "engine_loop_healthy": host.engine_loop_healthy if host else None,
            "clock_ok": host.clock_ok if host else None,
            "heartbeat_status": heartbeat_payload["status"] if heartbeat_payload else None,
        },
        "clock": {
            "broker_timezone": feed.broker_timezone if feed else None,
            "timestamp_interpretation": feed.timestamp_interpretation if feed else None,
            "session_review_state": "WAITING_EXTERNAL", "broker_tick_time": None,
        },
        "account_context": ctx.to_payload() if ctx else None,
        "economics": {
            "state": "UNKNOWN", "verification": "OBSERVATION_IS_NOT_REVIEWED_RISK_BINDING",
            "observed_symbol_metadata": asdict(host.symbols[0]) if host and host.symbols else None,
        },
        "risk_loss_exposure": {"state": "WAITING_EXTERNAL", "values": None},
        "session_guard": {"state": "UNKNOWN"},
        "reserved_attempt": None,
        "broker_lifecycle": {"state": "UNKNOWN", "venue_state": "UNKNOWN"},
        "reconciliation": {
            "state": "UNKNOWN", "account_inventory_complete": False,
            "history_completeness": "UNKNOWN", "targeted_lookup_is_account_inventory": False,
            "resubmit_allowed": False, "session_slot_release_allowed": False,
        },
        "recovery": {
            "state": "UNKNOWN", "candidate_observed_state": snapshot.recovery_state if snapshot else None,
            "candidate_reconciliation_scope": "LOCAL_SHADOW_ONLY",
            "candidate_observed_reconciliation": snapshot.reconciliation_state if snapshot else None,
        },
        "build_identity": {"state": "UNKNOWN", "runtime_commit": None},
        "provenance": {
            "snapshot_fingerprint": snapshot.snapshot_fingerprint if snapshot else None,
            "bundle_fingerprint": bundle.fingerprint if bundle else None,
            "evidence_kind": "OBSERVATION_ONLY_NOT_EXECUTION_AUTHORIZATION",
        },
        "execution_capability": "NONE", "order_execution_enabled": False,
        "shadow_authorized": True, "demo_paper_execution_authorized": False, "live_authorized": False,
    }
    _assert_credential_free(projection)
    projection["console_fingerprint"] = stable_fingerprint(projection)
    return projection


def _observation_age(now: datetime, observed: datetime) -> float:
    if observed.tzinfo is None or observed.utcoffset() is None:
        raise ValueError("operator observation must be timezone-aware")
    age = (now - observed).total_seconds()
    if age < 0:
        raise ValueError("operator observation is in the future")
    return age


def _tile(state: str, value: Any) -> dict[str, Any]:
    return {"state": state, "value": value}
