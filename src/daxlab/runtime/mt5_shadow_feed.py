"""Fail-closed adapter from credential-free MT5 Windows evidence to SHADOW.

The adapter consumes an already captured read-only MT5 probe bundle. It has no
MetaTrader5 dependency, no network access and no order capability. The only
possible SHADOW action remains ``NO_ORDER``.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping

from daxlab.runtime.mt5_readonly import Mt5Bar, market_data_is_fresh
from daxlab.runtime.shadow_soak import SoakCheckpoint, SoakFault, SoakResult, run_shadow_soak

_EXPECTED_SCHEMA = "DAXLAB_MT5_WINDOWS_BUNDLE_V1"


@dataclass(frozen=True, slots=True)
class Mt5ShadowFeedStatus:
    symbol: str
    bars: int
    host_read_only_healthy: bool
    feed_fresh: bool
    clock_ok: bool
    broker_timezone_configured: bool
    order_execution_enabled: bool = False


def shadow_from_mt5_bundle(
    payload: Mapping[str, Any],
    *,
    observed_at: datetime,
    max_age_seconds: float,
    single_instance_lock_held: bool = True,
    checkpoint: SoakCheckpoint | None = None,
) -> tuple[SoakResult, Mt5ShadowFeedStatus]:
    """Convert one MT5 read-only evidence bundle into deterministic SHADOW output.

    The function deliberately requires explicit broker-timezone normalization in
    the source bundle and rejects any bundle that claims order execution is
    enabled. All bars are passed through the existing SHADOW soak engine.
    """
    if observed_at.tzinfo is None:
        raise ValueError("observed_at must be timezone-aware")
    if max_age_seconds < 0:
        raise ValueError("max_age_seconds must be non-negative")
    if payload.get("schema") != _EXPECTED_SCHEMA:
        raise ValueError("MT5 Windows bundle schema mismatch")

    host = _mapping(payload.get("host_probe"), "host_probe")
    feed = _mapping(payload.get("closed_m5_feed"), "closed_m5_feed")

    if host.get("order_execution_enabled") is not False:
        raise ValueError("MT5 SHADOW source must keep order execution disabled")
    if feed.get("broker_timezone") in (None, ""):
        raise ValueError("MT5 SHADOW source requires explicit broker timezone")
    if feed.get("timestamp_interpretation") != "EXPLICIT_BROKER_WALL_CLOCK":
        raise ValueError("MT5 SHADOW source requires normalized broker timestamps")
    if int(feed.get("requested_start_pos", 0)) < 1:
        raise ValueError("MT5 SHADOW source must exclude bar 0")

    symbols_raw = host.get("symbols")
    if not isinstance(symbols_raw, list) or not symbols_raw:
        raise ValueError("MT5 SHADOW source has no resolved symbol metadata")
    symbol = str(symbols_raw[0].get("name", "")).strip()
    if not symbol:
        raise ValueError("MT5 SHADOW source symbol is empty")

    bars = _bars(feed.get("bars"))
    if not bars:
        raise ValueError("MT5 SHADOW source has no closed M5 bars")

    latest = bars[-1]
    feed_fresh = market_data_is_fresh(
        latest_closed_bar_open=latest.open_time,
        timeframe_minutes=5,
        observed_at=observed_at,
        max_age_seconds=max_age_seconds,
    )
    clock_ok = bool(host.get("clock_ok"))
    host_read_only_healthy = bool(
        host.get("terminal_connected")
        and host.get("account_connected")
        and host.get("engine_loop_healthy")
        and host.get("order_execution_enabled") is False
    )

    fault = SoakFault(
        host_read_only_healthy=host_read_only_healthy,
        feed_fresh=feed_fresh,
        clock_ok=clock_ok,
        single_instance_lock_held=single_instance_lock_held,
    )
    faults = {index: fault for index in range(len(bars))}
    result = run_shadow_soak(
        bars,
        symbol=symbol,
        checkpoint=checkpoint,
        faults=faults,
    )
    if result.order_execution_enabled is not False or result.execution_capability != "NONE":
        raise RuntimeError("MT5 SHADOW adapter produced an execution-capable result")
    if any(item.action != "NO_ORDER" for item in result.decisions):
        raise RuntimeError("MT5 SHADOW adapter emitted order-capable action")

    status = Mt5ShadowFeedStatus(
        symbol=symbol,
        bars=len(bars),
        host_read_only_healthy=host_read_only_healthy,
        feed_fresh=feed_fresh,
        clock_ok=clock_ok,
        broker_timezone_configured=True,
    )
    return result, status


def _mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"MT5 Windows bundle {field} missing or invalid")
    return value


def _bars(value: Any) -> tuple[Mt5Bar, ...]:
    if not isinstance(value, list):
        raise ValueError("MT5 SHADOW bars must be a list")
    result: list[Mt5Bar] = []
    for row in value:
        if not isinstance(row, Mapping):
            raise ValueError("MT5 SHADOW bar row must be an object")
        open_time = datetime.fromisoformat(str(row["open_time"]))
        if open_time.tzinfo is None:
            raise ValueError("MT5 SHADOW bar timestamp must be timezone-aware")
        bar = Mt5Bar(
            open_time=open_time,
            open=float(row["open"]),
            high=float(row["high"]),
            low=float(row["low"]),
            close=float(row["close"]),
        )
        if bar.high < max(bar.open, bar.close) or bar.low > min(bar.open, bar.close):
            raise ValueError("MT5 SHADOW bar OHLC invariant failed")
        if bar.high < bar.low:
            raise ValueError("MT5 SHADOW bar high below low")
        result.append(bar)
    ordered = tuple(sorted(result, key=lambda item: item.open_time))
    if len({item.open_time for item in ordered}) != len(ordered):
        raise ValueError("MT5 SHADOW source contains duplicate bar timestamps")
    return ordered
