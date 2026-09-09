"""Credential-free, read-only MT5 desktop probe for the Windows host.

Run this only on the Windows machine where MetaTrader 5 Desktop is already open
and logged into a demo account. The script never accepts login/password fields
and never calls any order API.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from daxlab.runtime.mt5_readonly import BrokerSymbol, closed_rates_start_pos, resolve_dax_symbol


FORBIDDEN_OUTPUT_KEYS = {"login", "password", "token", "secret", "email", "phone", "account"}


def _trade_mode_name(value: Any) -> str:
    return str(value)


def _safe_symbol(info: Any) -> BrokerSymbol:
    return BrokerSymbol(
        name=str(info.name),
        digits=int(info.digits),
        point=float(info.point),
        trade_mode=_trade_mode_name(info.trade_mode),
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


def collect_probe(*, configured_symbol: str | None, bars: int) -> dict[str, Any]:
    try:
        import MetaTrader5 as mt5
    except ImportError as exc:  # pragma: no cover - Windows-only dependency
        raise RuntimeError("MetaTrader5 Python package is not installed") from exc

    if bars < 2:
        raise ValueError("bars must be >= 2")
    if not mt5.initialize():
        code, message = mt5.last_error()
        raise RuntimeError(f"MT5 initialize failed: {code} {message}")

    try:
        terminal = mt5.terminal_info()
        account_info = mt5.account_info()
        symbols_raw = mt5.symbols_get() or ()
        symbols = tuple(_safe_symbol(s) for s in symbols_raw)
        resolution = resolve_dax_symbol(symbols, configured_symbol=configured_symbol)

        payload: dict[str, Any] = {
            "schema": "DAXLAB_MT5_WINDOWS_PROBE_V1",
            "observed_at_utc": datetime.now(timezone.utc).isoformat(),
            "terminal_connected": bool(terminal and terminal.connected),
            "demo_account_connected": bool(account_info is not None),
            "order_execution_enabled": False,
            "symbol_resolution": {
                "state": resolution.state,
                "broker_symbol": resolution.broker_symbol.name if resolution.broker_symbol else None,
                "candidates": list(resolution.candidates),
            },
            "symbol_metadata": asdict(resolution.broker_symbol) if resolution.broker_symbol else None,
            "closed_m5": [],
            "notes": ["READ_ONLY", "BAR_0_EXCLUDED", "NO_CREDENTIALS"],
        }

        if resolution.broker_symbol is not None:
            symbol = resolution.broker_symbol.name
            mt5.symbol_select(symbol, True)
            start_pos = closed_rates_start_pos(1)
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, start_pos, bars)
            if rates is not None:
                payload["closed_m5"] = [
                    {
                        "time_utc": datetime.fromtimestamp(int(row["time"]), timezone.utc).isoformat(),
                        "open": float(row["open"]),
                        "high": float(row["high"]),
                        "low": float(row["low"]),
                        "close": float(row["close"]),
                    }
                    for row in rates
                ]

        _assert_credential_free(payload)
        return payload
    finally:
        mt5.shutdown()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default=None, help="Exact broker symbol if auto-resolution is ambiguous")
    parser.add_argument("--bars", type=int, default=20)
    parser.add_argument("--output", default="mt5_probe.json")
    args = parser.parse_args()
    payload = collect_probe(configured_symbol=args.symbol, bars=args.bars)
    path = Path(args.output)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    print(f"WROTE {path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
