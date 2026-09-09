from datetime import datetime, timezone

from daxlab.runtime.mt5_watchdog import build_mt5_watchdog_snapshot, why_no_trade


def test_multi_bar_soak_watchdog_healthy_summary_is_non_executing() -> None:
    snapshot = build_mt5_watchdog_snapshot(
        observed_at=datetime(2026, 9, 9, 8, 0, tzinfo=timezone.utc),
        terminal_connected=True,
        account_connected=True,
        clock_skew_seconds=0.1,
        max_clock_skew_seconds=2.0,
        heartbeat_age_seconds=1.0,
        max_heartbeat_age_seconds=10.0,
        feed_age_seconds=1.0,
        max_feed_age_seconds=360.0,
        single_instance_lock_held=True,
        order_execution_enabled=False,
    )
    assert snapshot.read_only_healthy
    assert snapshot.execution_ready is False
    assert why_no_trade(snapshot) == "READ_ONLY_HEALTHY_BUT_EXECUTION_NOT_AUTHORIZED"


def test_multi_fault_watchdog_summary_keeps_all_blockers() -> None:
    snapshot = build_mt5_watchdog_snapshot(
        observed_at=datetime(2026, 9, 9, 8, 0, tzinfo=timezone.utc),
        terminal_connected=False,
        account_connected=False,
        clock_skew_seconds=3.0,
        max_clock_skew_seconds=2.0,
        heartbeat_age_seconds=11.0,
        max_heartbeat_age_seconds=10.0,
        feed_age_seconds=361.0,
        max_feed_age_seconds=360.0,
        single_instance_lock_held=False,
        order_execution_enabled=False,
    )
    assert snapshot.blockers == (
        "MT5_TERMINAL_DISCONNECTED",
        "MT5_ACCOUNT_DISCONNECTED",
        "MT5_CLOCK_SKEW",
        "MT5_ENGINE_HEARTBEAT_STALE",
        "MT5_MARKET_DATA_STALE",
        "MT5_SINGLE_INSTANCE_LOCK_NOT_HELD",
    )
    assert not snapshot.read_only_healthy
    assert snapshot.execution_ready is False
