from dataclasses import replace

import pytest

from daxlab.runtime.mt5_shadow_integration import HostShadowStatus, Mt5ShadowResumeTelemetry
from daxlab.runtime.operator_runtime_bridge import build_mt5_shadow_operator_runtime_context
from daxlab.runtime.restart_reconcile import RestartReconcileResult


def _host(
    *,
    status: str = "GREEN",
    blockers: tuple[str, ...] = (),
    age: float | None = 2.5,
    resume=None,
) -> HostShadowStatus:
    return HostShadowStatus(
        status=status,
        blockers=blockers,
        symbol="DE40",
        closed_m5_bars=40,
        latest_closed_bar_age_seconds=age,
        single_instance_lock_held=True,
        order_execution_enabled=False,
        evidence_fingerprint="a" * 64,
        resume_telemetry=resume,
    )


def test_green_host_maps_to_generic_operator_runtime_context() -> None:
    context = build_mt5_shadow_operator_runtime_context(_host())

    assert context.health_state == "GREEN"
    assert context.health_source == "MT5_SHADOW_HOST"
    assert context.freshness_seconds == 2.5
    assert context.runtime_events == ()
    assert context.recovery_state is None
    assert context.reconciliation_state is None
    assert context.execution_capability == "NONE"
    assert context.order_execution_enabled is False
    assert context.snapshot_kwargs()["health_state"] == "GREEN"


def test_blocked_host_surfaces_existing_blockers_without_mutating_strategy() -> None:
    context = build_mt5_shadow_operator_runtime_context(
        _host(status="BLOCKED", blockers=("FEED_STALE", "CLOCK_UNSAFE"))
    )

    assert context.health_state == "RED"
    assert context.runtime_events == (
        "HOST_BLOCKER:FEED_STALE",
        "HOST_BLOCKER:CLOCK_UNSAFE",
    )


def test_resume_telemetry_maps_to_recovery_visibility() -> None:
    resume = Mt5ShadowResumeTelemetry(
        fresh_start=False,
        anchor_found=True,
        anchor_index=10,
        feed_bar_count=40,
        catchup_bar_count=3,
        prior_anchor_filtered_bar_count=10,
    )
    context = build_mt5_shadow_operator_runtime_context(_host(resume=resume))

    assert context.recovery_state == "RESUME_ANCHOR_RECONCILED"
    assert "RESTART_CATCHUP" in context.runtime_events
    assert "PRIOR_ANCHOR_BARS_FILTERED" in context.runtime_events


def test_restart_reconcile_gap_is_explicit_operator_event() -> None:
    reconcile = RestartReconcileResult(
        checkpoint_time_iso="2026-09-11T09:20:00+00:00",
        latest_closed_bar_time_iso="2026-09-11T09:30:00+00:00",
        gap_seconds=600.0,
        replay_gap_detected=True,
        safe_to_resume=True,
    )
    context = build_mt5_shadow_operator_runtime_context(
        _host(), restart_reconcile=reconcile
    )

    assert context.reconciliation_state == "REPLAY_GAP_SAFE_TO_RESUME"
    assert "REPLAY_GAP_DETECTED" in context.runtime_events


def test_execution_escalation_fails_closed() -> None:
    with pytest.raises(ValueError, match="cannot enable order execution"):
        build_mt5_shadow_operator_runtime_context(
            replace(_host(), order_execution_enabled=True)
        )


def test_negative_host_freshness_fails_closed() -> None:
    with pytest.raises(ValueError, match="freshness"):
        build_mt5_shadow_operator_runtime_context(_host(age=-0.1))
