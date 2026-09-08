from datetime import datetime

from daxlab.runtime.mt5_watchdog import (
    build_mt5_watchdog_snapshot,
    why_no_trade,
)


def healthy():
    return build_mt5_watchdog_snapshot(
        observed_at=datetime.fromisoformat("2026-09-08T22:00:00+02:00"),
        terminal_connected=True,
        account_connected=True,
        clock_skew_seconds=0.2,
        max_clock_skew_seconds=2,
        heartbeat_age_seconds=1,
        max_heartbeat_age_seconds=10,
        feed_age_seconds=30,
        max_feed_age_seconds=360,
        single_instance_lock_held=True,
        order_execution_enabled=False,
    )


def test_read_only_health_never_implies_execution_ready() -> None:
    snapshot = healthy()
    assert snapshot.read_only_healthy
    assert snapshot.execution_ready is False
    assert why_no_trade(snapshot) == "READ_ONLY_HEALTHY_BUT_EXECUTION_NOT_AUTHORIZED"


def test_connectivity_reasons_have_no_account_identifier() -> None:
    snapshot = build_mt5_watchdog_snapshot(
        observed_at=datetime.fromisoformat("2026-09-08T22:00:00+02:00"),
        terminal_connected=False,
        account_connected=False,
        clock_skew_seconds=0,
        max_clock_skew_seconds=2,
        heartbeat_age_seconds=0,
        max_heartbeat_age_seconds=10,
        feed_age_seconds=0,
        max_feed_age_seconds=360,
        single_instance_lock_held=True,
        order_execution_enabled=False,
    )
    assert snapshot.blockers[:2] == (
        "MT5_TERMINAL_DISCONNECTED",
        "MT5_ACCOUNT_DISCONNECTED",
    )


def test_clock_heartbeat_feed_lock_and_execution_blockers() -> None:
    snapshot = build_mt5_watchdog_snapshot(
        observed_at=datetime.fromisoformat("2026-09-08T22:00:00+02:00"),
        terminal_connected=True,
        account_connected=True,
        clock_skew_seconds=3,
        max_clock_skew_seconds=2,
        heartbeat_age_seconds=11,
        max_heartbeat_age_seconds=10,
        feed_age_seconds=361,
        max_feed_age_seconds=360,
        single_instance_lock_held=False,
        order_execution_enabled=True,
    )
    assert "MT5_CLOCK_SKEW" in snapshot.blockers
    assert "MT5_ENGINE_HEARTBEAT_STALE" in snapshot.blockers
    assert "MT5_MARKET_DATA_STALE" in snapshot.blockers
    assert "MT5_SINGLE_INSTANCE_LOCK_NOT_HELD" in snapshot.blockers
    assert "MT5_ORDER_EXECUTION_ENABLED" in snapshot.blockers
    assert not snapshot.read_only_healthy
    assert not snapshot.execution_ready
