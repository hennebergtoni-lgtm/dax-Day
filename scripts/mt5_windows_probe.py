"""Credential-free, read-only MT5 desktop probe for the Windows host.

Run this only where MetaTrader 5 Desktop is already open and logged into a demo
account. The script never accepts login/password fields and never calls order APIs.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from daxlab.runtime.mt5_broker_session import server_wall_clock_epoch_to_utc
from daxlab.runtime.mt5_readonly import BrokerSymbol, closed_rates_start_pos, resolve_dax_symbol

FORBIDDEN_OUTPUT_KEYS = {"login", "password", "token", "secret", "email", "phone", "account_id"}


def _trade_mode_name(mt5: Any, value: Any) -> str:
    mapping = {
        getattr(mt5, "SYMBOL_TRADE_MODE_DISABLED", object()): "DISABLED",
        getattr(mt5, "SYMBOL_TRADE_MODE_LONGONLY", object()): "LONGONLY",
        getattr(mt5, "SYMBOL_TRADE_MODE_SHORTONLY", object()): "SHORTONLY",
        getattr(mt5, "SYMBOL_TRADE_MODE_CLOSEONLY", object()): "CLOSEONLY",
        getattr(mt5, "SYMBOL_TRADE_MODE_FULL", object()): "FULL",
    }
    return mapping.get(value, str(value))


def _safe_symbol(mt5: Any, info: Any) -> BrokerSymbol:
    return BrokerSymbol(
        name=str(info.name),
        digits=int(info.digits),
        point=float(info.point),
        trade_mode=_trade_mode_name(mt5, info.trade_mode),
        contract_size=float(info.trade_contract_size),
        volume_min=float(info.volume_min),
        volume_step=float(info.volume_step),
    )


def _assert_credential_free(payload: dict[str, Any]) -> None:
    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                if key.lower() in FORBIDDEN_OUTPUT_KEYS:
                    raise RuntimeError(f"forbidden evidence key: {key}")
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(payload)


def _fingerprint(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def _mt5_epoch_to_utc(value: int | float, broker_timezone: str | None) -> datetime:
    if broker_timezone is None:
        return datetime.fromtimestamp(float(value), timezone.utc)
    return server_wall_clock_epoch_to_utc(value, broker_timezone)


def collect_probe(
    *,
    configured_symbol: str | None,
    bars: int,
    max_age_seconds: float,
    broker_timezone: str | None = None,
) -> dict[str, Any]:
    try:
        import MetaTrader5 as mt5
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("MetaTrader5 Python package is not installed") from exc
    if bars < 2:
        raise ValueError("bars must be >= 2")
    if max_age_seconds < 0:
        raise ValueError("max_age_seconds must be non-negative")
    if not mt5.initialize():
        code, message = mt5.last_error()
        raise RuntimeError(f"MT5 initialize failed: {code} {message}")

    try:
        observed = datetime.now(timezone.utc)
        terminal = mt5.terminal_info()
        account = mt5.account_info()
        symbols = tuple(_safe_symbol(mt5, s) for s in (mt5.symbols_get() or ()))
        resolution = resolve_dax_symbol(
            symbols,
            configured_symbol=configured_symbol,
            allow_data_only=True,
        )
        selected = resolution.broker_symbol
        safe_symbols = [
            {
                "name": s.name,
                "digits": s.digits,
                "point": s.point,
                "trade_mode": s.trade_mode,
                "contract_size": s.contract_size,
                "volume_min": s.volume_min,
                "volume_step": s.volume_step,
            }
            for s in symbols
            if s.name in resolution.candidates or (selected and s.name == selected.name)
        ]

        raw_tick_delta_seconds = None
        normalized_tick_delta_seconds = None
        clock_ok = False
        feed = None
        if selected is not None:
            mt5.symbol_select(selected.name, True)
            tick = mt5.symbol_info_tick(selected.name)
            if tick is not None and getattr(tick, "time", None):
                raw_tick_time = datetime.fromtimestamp(float(tick.time), timezone.utc)
                raw_tick_delta_seconds = (observed - raw_tick_time).total_seconds()
                normalized_tick_time = _mt5_epoch_to_utc(tick.time, broker_timezone)
                normalized_tick_delta_seconds = (observed - normalized_tick_time).total_seconds()
                clock_ok = abs(normalized_tick_delta_seconds) <= max_age_seconds
            start_pos = closed_rates_start_pos(1)
            rates = mt5.copy_rates_from_pos(selected.name, mt5.TIMEFRAME_M5, start_pos, bars)
            rate_rows = rates if rates is not None else ()
            feed = {
                "observed_at": observed.isoformat(),
                "requested_start_pos": start_pos,
                "max_age_seconds": max_age_seconds,
                "broker_timezone": broker_timezone,
                "timestamp_interpretation": (
                    "EXPLICIT_BROKER_WALL_CLOCK" if broker_timezone else "RAW_UTC_ASSUMPTION"
                ),
                "bars": [
                    {
                        "open_time": _mt5_epoch_to_utc(
                            int(row["time"]), broker_timezone
                        ).isoformat(),
                        "open": float(row["open"]),
                        "high": float(row["high"]),
                        "low": float(row["low"]),
                        "close": float(row["close"]),
                    }
                    for row in rate_rows
                ],
            }

        host_probe = {
            "observed_at": observed.isoformat(),
            "terminal_connected": bool(terminal and terminal.connected),
            "account_connected": bool(account is not None),
            "account_trade_allowed": bool(account and account.trade_allowed),
            "order_execution_enabled": False,
            "engine_loop_healthy": True,
            "clock_ok": clock_ok,
            "broker_timezone": broker_timezone,
            "symbols": safe_symbols,
        }
        notes = ["READ_ONLY", "BAR_0_EXCLUDED", "NO_CREDENTIALS", "NO_ORDER_API"]
        if raw_tick_delta_seconds is not None:
            notes.append(f"RAW_TICK_CLOCK_DELTA_SECONDS={raw_tick_delta_seconds:.3f}")
        if normalized_tick_delta_seconds is not None:
            notes.append(
                f"NORMALIZED_TICK_CLOCK_DELTA_SECONDS={normalized_tick_delta_seconds:.3f}"
            )
        if broker_timezone is None:
            notes.append("BROKER_TIMEZONE_NOT_CONFIGURED")
        bundle = {
            "schema": "DAXLAB_MT5_WINDOWS_BUNDLE_V1",
            "symbol_resolution_state": resolution.state,
            "host_probe": host_probe,
            "closed_m5_feed": feed,
            "notes": notes,
        }
        _assert_credential_free(bundle)
        bundle["sha256"] = _fingerprint(bundle)
        return bundle
    finally:
        mt5.shutdown()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default=None)
    parser.add_argument("--bars", type=int, default=20)
    parser.add_argument("--max-age-seconds", type=float, default=600.0)
    parser.add_argument("--broker-timezone", default=None)
    parser.add_argument("--output", default="mt5_probe.json")
    parser.add_argument("--timestamped", action="store_true")
    args = parser.parse_args()
    payload = collect_probe(
        configured_symbol=args.symbol,
        bars=args.bars,
        max_age_seconds=args.max_age_seconds,
        broker_timezone=args.broker_timezone,
    )
    path = Path(args.output)
    if args.timestamped:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = path.with_name(f"{path.stem}_{stamp}{path.suffix}")
    if path.exists():
        raise RuntimeError(f"refusing to overwrite existing evidence file: {path}")
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    print(f"WROTE {path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
