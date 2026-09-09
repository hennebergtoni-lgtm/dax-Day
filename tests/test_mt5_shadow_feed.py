from datetime import datetime, timedelta, timezone

import pytest

from daxlab.runtime.mt5_shadow_feed import shadow_from_mt5_bundle


def bundle(*, observed_at: datetime, bars: int = 3) -> dict:
    start = observed_at - timedelta(minutes=5 * bars, seconds=1)
    rows = []
    for index in range(bars):
        open_time = start + timedelta(minutes=5 * index)
        price = 25000.0 + index
        rows.append(
            {
                "open_time": open_time.isoformat(),
                "open": price,
                "high": price + 2.0,
                "low": price - 1.0,
                "close": price + 1.0,
            }
        )
    return {
        "schema": "DAXLAB_MT5_WINDOWS_BUNDLE_V1",
        "symbol_resolution_state": "CONFIGURED_EXACT_DATA_ONLY",
        "host_probe": {
            "observed_at": observed_at.isoformat(),
            "terminal_connected": True,
            "account_connected": True,
            "account_trade_allowed": False,
            "order_execution_enabled": False,
            "engine_loop_healthy": True,
            "clock_ok": True,
            "broker_timezone": "Europe/Berlin",
            "symbols": [
                {
                    "name": "DE40",
                    "digits": 2,
                    "point": 0.01,
                    "trade_mode": "DISABLED",
                    "contract_size": 1.0,
                    "volume_min": 0.01,
                    "volume_step": 0.01,
                }
            ],
        },
        "closed_m5_feed": {
            "observed_at": observed_at.isoformat(),
            "requested_start_pos": 1,
            "max_age_seconds": 600.0,
            "broker_timezone": "Europe/Berlin",
            "timestamp_interpretation": "EXPLICIT_BROKER_WALL_CLOCK",
            "bars": rows,
        },
        "notes": ["READ_ONLY", "BAR_0_EXCLUDED", "NO_CREDENTIALS", "NO_ORDER_API"],
    }


def test_green_bundle_becomes_no_order_shadow() -> None:
    observed = datetime(2026, 9, 9, 19, 30, 1, tzinfo=timezone.utc)
    result, status = shadow_from_mt5_bundle(
        bundle(observed_at=observed),
        observed_at=observed,
        max_age_seconds=600,
    )
    assert result.processed == 3
    assert result.blocked == 0
    assert result.execution_capability == "NONE"
    assert result.order_execution_enabled is False
    assert all(item.action == "NO_ORDER" for item in result.decisions)
    assert status.symbol == "DE40"
    assert status.feed_fresh is True
    assert status.clock_ok is True


def test_stale_feed_blocks_every_observation_but_never_orders() -> None:
    source_time = datetime(2026, 9, 9, 19, 30, 1, tzinfo=timezone.utc)
    observed = source_time + timedelta(hours=1)
    result, status = shadow_from_mt5_bundle(
        bundle(observed_at=source_time),
        observed_at=observed,
        max_age_seconds=600,
    )
    assert status.feed_fresh is False
    assert result.blocked == result.processed
    assert all("CLOSED_M5_FEED_NOT_FRESH" in item.reason_codes for item in result.decisions)
    assert all(item.action == "NO_ORDER" for item in result.decisions)


def test_clock_failure_blocks_without_order_capability() -> None:
    observed = datetime(2026, 9, 9, 19, 30, 1, tzinfo=timezone.utc)
    source = bundle(observed_at=observed)
    source["host_probe"]["clock_ok"] = False
    result, status = shadow_from_mt5_bundle(
        source,
        observed_at=observed,
        max_age_seconds=600,
    )
    assert status.clock_ok is False
    assert result.blocked == result.processed
    assert all("CLOCK_NOT_SAFE" in item.reason_codes for item in result.decisions)


def test_rejects_order_enabled_source() -> None:
    observed = datetime(2026, 9, 9, 19, 30, 1, tzinfo=timezone.utc)
    source = bundle(observed_at=observed)
    source["host_probe"]["order_execution_enabled"] = True
    with pytest.raises(ValueError, match="order execution disabled"):
        shadow_from_mt5_bundle(source, observed_at=observed, max_age_seconds=600)


def test_rejects_bar_zero_source() -> None:
    observed = datetime(2026, 9, 9, 19, 30, 1, tzinfo=timezone.utc)
    source = bundle(observed_at=observed)
    source["closed_m5_feed"]["requested_start_pos"] = 0
    with pytest.raises(ValueError, match="exclude bar 0"):
        shadow_from_mt5_bundle(source, observed_at=observed, max_age_seconds=600)


def test_rejects_missing_broker_timezone() -> None:
    observed = datetime(2026, 9, 9, 19, 30, 1, tzinfo=timezone.utc)
    source = bundle(observed_at=observed)
    source["closed_m5_feed"]["broker_timezone"] = None
    with pytest.raises(ValueError, match="explicit broker timezone"):
        shadow_from_mt5_bundle(source, observed_at=observed, max_age_seconds=600)


def test_resume_suppresses_previously_seen_bars() -> None:
    observed = datetime(2026, 9, 9, 19, 30, 1, tzinfo=timezone.utc)
    source = bundle(observed_at=observed, bars=3)
    first, _ = shadow_from_mt5_bundle(
        source,
        observed_at=observed,
        max_age_seconds=600,
    )
    second, _ = shadow_from_mt5_bundle(
        source,
        observed_at=observed,
        max_age_seconds=600,
        checkpoint=first.checkpoint,
    )
    assert second.processed == first.processed
    assert second.duplicates_suppressed == 3
    assert second.decisions == ()


def test_rejects_duplicate_bar_timestamps() -> None:
    observed = datetime(2026, 9, 9, 19, 30, 1, tzinfo=timezone.utc)
    source = bundle(observed_at=observed, bars=2)
    source["closed_m5_feed"]["bars"][1]["open_time"] = source["closed_m5_feed"]["bars"][0]["open_time"]
    with pytest.raises(ValueError, match="duplicate bar timestamps"):
        shadow_from_mt5_bundle(source, observed_at=observed, max_age_seconds=600)
