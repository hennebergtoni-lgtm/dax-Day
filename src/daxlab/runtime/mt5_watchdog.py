"""Deterministic read-only MT5 health/watchdog snapshot.

No execution capability is granted here. A healthy snapshot only means the
read-only host/feed contract is internally healthy.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Mt5WatchdogSnapshot:
    observed_at: datetime
    terminal_connected: bool
    account_connected: bool
    clock_skew_seconds: float
    heartbeat_age_seconds: float
    feed_age_seconds: float
    single_instance_lock_held: bool
    order_execution_enabled: bool
    blockers: tuple[str, ...]

    @property
    def read_only_healthy(self) -> bool:
        return not self.blockers and self.order_execution_enabled is False

    @property
    def execution_ready(self) -> bool:
        return False


def build_mt5_watchdog_snapshot(
    *,
    observed_at: datetime,
    terminal_connected: bool,
    account_connected: bool,
    clock_skew_seconds: float,
    max_clock_skew_seconds: float,
    heartbeat_age_seconds: float,
    max_heartbeat_age_seconds: float,
    feed_age_seconds: float,
    max_feed_age_seconds: float,
    single_instance_lock_held: bool,
    order_execution_enabled: bool,
) -> Mt5WatchdogSnapshot:
    if observed_at.tzinfo is None:
        raise ValueError("observed_at must be timezone-aware")

    values = {
        "clock_skew_seconds": clock_skew_seconds,
        "max_clock_skew_seconds": max_clock_skew_seconds,
        "heartbeat_age_seconds": heartbeat_age_seconds,
        "max_heartbeat_age_seconds": max_heartbeat_age_seconds,
        "feed_age_seconds": feed_age_seconds,
        "max_feed_age_seconds": max_feed_age_seconds,
    }
    for name, value in values.items():
        if value < 0:
            raise ValueError(f"{name} must be non-negative")

    blockers: list[str] = []
    if not terminal_connected:
        blockers.append("MT5_TERMINAL_DISCONNECTED")
    if not account_connected:
        blockers.append("MT5_ACCOUNT_DISCONNECTED")
    if clock_skew_seconds > max_clock_skew_seconds:
        blockers.append("MT5_CLOCK_SKEW")
    if heartbeat_age_seconds > max_heartbeat_age_seconds:
        blockers.append("MT5_ENGINE_HEARTBEAT_STALE")
    if feed_age_seconds > max_feed_age_seconds:
        blockers.append("MT5_MARKET_DATA_STALE")
    if not single_instance_lock_held:
        blockers.append("MT5_SINGLE_INSTANCE_LOCK_NOT_HELD")
    if order_execution_enabled:
        blockers.append("MT5_ORDER_EXECUTION_ENABLED")

    return Mt5WatchdogSnapshot(
        observed_at=observed_at,
        terminal_connected=terminal_connected,
        account_connected=account_connected,
        clock_skew_seconds=float(clock_skew_seconds),
        heartbeat_age_seconds=float(heartbeat_age_seconds),
        feed_age_seconds=float(feed_age_seconds),
        single_instance_lock_held=single_instance_lock_held,
        order_execution_enabled=order_execution_enabled,
        blockers=tuple(blockers),
    )


def why_no_trade(snapshot: Mt5WatchdogSnapshot) -> str:
    if snapshot.blockers:
        return ";".join(snapshot.blockers)
    return "READ_ONLY_HEALTHY_BUT_EXECUTION_NOT_AUTHORIZED"
