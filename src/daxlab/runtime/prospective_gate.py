"""Fail-closed authorization boundary for prospective shadow/paper/live modes.

This module records user authorization scope but never grants execution by itself.
Live-money execution always requires a distinct live authorization and a separate
execution adapter that is not implemented here.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ProspectiveMode(StrEnum):
    SHADOW = "SHADOW"
    PAPER = "PAPER"
    LIVE = "LIVE"


@dataclass(frozen=True, slots=True)
class ProspectiveAuthorization:
    gate_id: str
    shadow_authorized: bool
    paper_authorized: bool
    live_authorized: bool


@dataclass(frozen=True, slots=True)
class ProspectiveGateResult:
    allowed: bool
    blockers: tuple[str, ...]


def evaluate_prospective_gate(
    *,
    mode: ProspectiveMode,
    authorization: ProspectiveAuthorization,
    host_read_only_healthy: bool,
    exact_broker_symbol_resolved: bool,
    closed_m5_feed_fresh: bool,
    clock_ok: bool,
    single_instance_lock_held: bool,
    order_execution_enabled: bool,
) -> ProspectiveGateResult:
    """Return a deterministic, fail-closed readiness decision.

    Authorization is necessary but never sufficient. LIVE is additionally blocked
    unless live_authorized is explicitly true. order_execution_enabled must remain
    false for SHADOW and PAPER preparation in this module.
    """
    blockers: list[str] = []

    if authorization.gate_id != "STEP_91_USER_AUTHORIZATION":
        blockers.append("PROSPECTIVE_AUTHORIZATION_MISSING")

    if mode is ProspectiveMode.SHADOW and not authorization.shadow_authorized:
        blockers.append("SHADOW_NOT_AUTHORIZED")
    if mode is ProspectiveMode.PAPER and not authorization.paper_authorized:
        blockers.append("PAPER_NOT_AUTHORIZED")
    if mode is ProspectiveMode.LIVE and not authorization.live_authorized:
        blockers.append("LIVE_NOT_AUTHORIZED")

    if not host_read_only_healthy:
        blockers.append("MT5_HOST_NOT_HEALTHY")
    if not exact_broker_symbol_resolved:
        blockers.append("BROKER_SYMBOL_NOT_EXACT")
    if not closed_m5_feed_fresh:
        blockers.append("CLOSED_M5_FEED_NOT_FRESH")
    if not clock_ok:
        blockers.append("CLOCK_NOT_SAFE")
    if not single_instance_lock_held:
        blockers.append("SINGLE_INSTANCE_LOCK_NOT_HELD")

    if mode in {ProspectiveMode.SHADOW, ProspectiveMode.PAPER} and order_execution_enabled:
        blockers.append("EXECUTION_MUST_REMAIN_DISABLED")

    return ProspectiveGateResult(allowed=not blockers, blockers=tuple(blockers))
