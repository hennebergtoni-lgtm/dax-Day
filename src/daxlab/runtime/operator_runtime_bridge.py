"""Read-only bridge from existing host/restart evidence into operator runtime context.

This module does not evaluate strategy rules, submit orders, or authorize PAPER/LIVE.
It translates already-owned MT5 SHADOW and restart/reconcile evidence into the
generic fields accepted by ``OperatorSnapshot``.
"""
from __future__ import annotations

from dataclasses import dataclass

from daxlab.runtime.health import HealthState
from daxlab.runtime.mt5_shadow_integration import HostShadowStatus
from daxlab.runtime.restart_reconcile import RestartReconcileResult


@dataclass(frozen=True, slots=True)
class OperatorRuntimeContext:
    health_state: str
    health_source: str
    freshness_seconds: float | None
    runtime_events: tuple[str, ...]
    recovery_state: str | None
    reconciliation_state: str | None
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.health_state not in {state.value for state in HealthState}:
            raise ValueError("unsupported operator runtime health_state")
        if not self.health_source.strip():
            raise ValueError("health_source must be non-empty")
        if self.freshness_seconds is not None and self.freshness_seconds < 0:
            raise ValueError("freshness_seconds cannot be negative")
        if any(not event.strip() for event in self.runtime_events):
            raise ValueError("runtime_events must be non-empty strings")
        if len(set(self.runtime_events)) != len(self.runtime_events):
            raise ValueError("runtime_events must be unique")
        if self.execution_capability != "NONE" or self.order_execution_enabled:
            raise ValueError("operator runtime context cannot authorize execution")

    def snapshot_kwargs(self) -> dict[str, object]:
        """Return only generic runtime fields accepted by ``build_operator_snapshot``."""
        return {
            "freshness_seconds": self.freshness_seconds,
            "health_state": self.health_state,
            "health_source": self.health_source,
            "runtime_events": self.runtime_events,
            "recovery_state": self.recovery_state,
            "reconciliation_state": self.reconciliation_state,
        }


def build_mt5_shadow_operator_runtime_context(
    host_status: HostShadowStatus,
    *,
    restart_reconcile: RestartReconcileResult | None = None,
) -> OperatorRuntimeContext:
    """Translate existing read-only MT5 SHADOW evidence without inventing new gates."""
    if host_status.order_execution_enabled:
        raise ValueError("MT5 SHADOW host status cannot enable order execution")
    if host_status.latest_closed_bar_age_seconds is not None:
        if host_status.latest_closed_bar_age_seconds < 0:
            raise ValueError("host freshness cannot be negative")

    if host_status.status == "GREEN" and not host_status.blockers:
        health = HealthState.GREEN
    elif host_status.status == "BLOCKED" or host_status.blockers:
        health = HealthState.RED
    else:
        raise ValueError("unsupported MT5 SHADOW host status")

    events: list[str] = [f"HOST_BLOCKER:{value}" for value in host_status.blockers]
    recovery_state: str | None = None
    telemetry = host_status.resume_telemetry
    if telemetry is not None:
        if telemetry.fresh_start:
            recovery_state = "FRESH_START"
        elif telemetry.anchor_found:
            recovery_state = "RESUME_ANCHOR_RECONCILED"
        else:
            recovery_state = "RESUME_ANCHOR_NOT_FOUND"
        if telemetry.catchup_bar_count > 0:
            events.append("RESTART_CATCHUP")
        if telemetry.prior_anchor_filtered_bar_count > 0:
            events.append("PRIOR_ANCHOR_BARS_FILTERED")

    reconciliation_state: str | None = None
    if restart_reconcile is not None:
        if restart_reconcile.execution_capability != "NONE":
            raise ValueError("restart reconcile cannot carry execution capability")
        if restart_reconcile.order_execution_enabled:
            raise ValueError("restart reconcile cannot enable order execution")
        if restart_reconcile.replay_gap_detected:
            events.append("REPLAY_GAP_DETECTED")
            reconciliation_state = (
                "REPLAY_GAP_SAFE_TO_RESUME"
                if restart_reconcile.safe_to_resume
                else "REPLAY_GAP_BLOCKED"
            )
        else:
            reconciliation_state = "IN_SYNC"

    return OperatorRuntimeContext(
        health_state=health.value,
        health_source="MT5_SHADOW_HOST",
        freshness_seconds=host_status.latest_closed_bar_age_seconds,
        runtime_events=tuple(dict.fromkeys(events)),
        recovery_state=recovery_state,
        reconciliation_state=reconciliation_state,
    )
