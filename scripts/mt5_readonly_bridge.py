#!/usr/bin/env python3
"""Minimal fail-closed HTTP bridge for closed DE40 M5 bars from local MT5.

No credentials, no filesystem serving, no order/trade API.
Intended to bind to the host's Tailscale IP only.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import MetaTrader5 as mt5


def closed_bars(symbol: str, count: int) -> dict:
    if not mt5.initialize():
        raise RuntimeError(f"MT5 initialize failed: {mt5.last_error()}")
    try:
        terminal = mt5.terminal_info()
        info = mt5.symbol_info(symbol)
        if terminal is None or not terminal.connected:
            raise RuntimeError("MT5 terminal not connected")
        if info is None:
            raise RuntimeError(f"symbol not found: {symbol}")
        if info.trade_mode != mt5.SYMBOL_TRADE_MODE_DISABLED:
            raise RuntimeError(f"fail-closed: {symbol} trade_mode is not DISABLED")
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 1, count)
        if rates is None or len(rates) == 0:
            raise RuntimeError(f"no closed M5 bars: {mt5.last_error()}")
        bars = [
            {
                "time_raw": int(r["time"]),
                "open": float(r["open"]),
                "high": float(r["high"]),
                "low": float(r["low"]),
                "close": float(r["close"]),
                "tick_volume": int(r["tick_volume"]),
            }
            for r in rates
        ]
        return {
            "schema": "DAXLAB_MT5_READONLY_BRIDGE_V1",
            "observed_at_utc": datetime.now(timezone.utc).isoformat(),
            "symbol": symbol,
            "timeframe": "M5",
            "bar_0_excluded": True,
            "order_execution_enabled": False,
            "trade_mode": "DISABLED",
            "bars": bars,
        }
    finally:
        mt5.shutdown()


class Handler(BaseHTTPRequestHandler):
    server_version = "DAXLABReadOnly/1"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self._json(200, {"ok": True, "read_only": True, "order_execution_enabled": False})
            return
        if parsed.path != "/v1/de40/m5":
            self._json(404, {"error": "not_found"})
            return
        query = parse_qs(parsed.query)
        try:
            count = int(query.get("count", ["3"])[0])
        except ValueError:
            self._json(400, {"error": "count_must_be_integer"})
            return
        if not 1 <= count <= 1000:
            self._json(400, {"error": "count_out_of_range", "min": 1, "max": 1000})
            return
        try:
            self._json(200, closed_bars("DE40", count))
        except Exception as exc:
            self._json(503, {"error": str(exc), "order_execution_enabled": False})

    def do_POST(self) -> None:
        self._json(405, {"error": "method_not_allowed", "read_only": True})

    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"[bridge] {self.address_string()} {fmt % args}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bind", required=True, help="Bind explicitly to the host Tailscale IP")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    if not args.bind.startswith("100."):
        raise SystemExit("Refusing to bind: --bind must be a Tailscale 100.x address")
    server = ThreadingHTTPServer((args.bind, args.port), Handler)
    print(f"DAXLAB MT5 READ-ONLY bridge listening on http://{args.bind}:{args.port}")
    print("DE40 M5 | BAR_0_EXCLUDED | NO_CREDENTIALS | NO_ORDER_API")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
