"""Translate MT5 read-only adapter state into canonical runtime health."""

from __future__ import annotations

from daxlab.runtime.health import HealthState
from daxlab.runtime.mt5_readonly import Mt5Health


def mt5_execution_health(state: Mt5Health) -> tuple[HealthState, tuple[str, ...]]:
    blockers: list[str] = []
    if not state.terminal_connected:
        blockers.append("MT5_TERMINAL_DISCONNECTED")
    if not state.account_connected:
        blockers.append("MT5_ACCOUNT_DISCONNECTED")
    if not state.symbol_available:
        blockers.append("MT5_SYMBOL_UNAVAILABLE")
    if not state.market_data_fresh:
        blockers.append("MT5_MARKET_DATA_STALE")
    if not state.clock_ok:
        blockers.append("MT5_CLOCK_UNSAFE")
    if not state.read_only_mode:
        blockers.append("MT5_READ_ONLY_GUARD_DISABLED")
    if not state.engine_loop_healthy:
        blockers.append("MT5_ENGINE_LOOP_UNHEALTHY")
    return (HealthState.GREEN if not blockers else HealthState.RED, tuple(blockers))
