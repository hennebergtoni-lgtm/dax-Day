"""Parse serialized observations from a future Windows MT5 read-only probe.

The parser is intentionally dependency-free and has no order/trade API. It is
safe to develop and test before any terminal is connected.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

from daxlab.runtime.mt5_host_contract import Mt5HostObservation
from daxlab.runtime.mt5_readonly import BrokerSymbol

_REQUIRED = {
    "observed_at",
    "terminal_connected",
    "account_connected",
    "account_trade_allowed",
    "order_execution_enabled",
    "engine_loop_healthy",
    "clock_ok",
    "symbols",
}
_SYMBOL_REQUIRED = {"name", "digits", "point", "trade_mode"}


def parse_mt5_probe_payload(payload: Mapping[str, Any]) -> Mt5HostObservation:
    """Convert a strict JSON-like payload into the fail-closed host contract."""
    missing = _REQUIRED - payload.keys()
    unknown = payload.keys() - _REQUIRED
    if missing:
        raise ValueError(f"missing MT5 probe fields: {sorted(missing)}")
    if unknown:
        raise ValueError(f"unknown MT5 probe fields: {sorted(unknown)}")

    observed_at = _timestamp(payload["observed_at"])
    symbols_raw = payload["symbols"]
    if not isinstance(symbols_raw, list):
        raise ValueError("symbols must be a list")
    symbols = tuple(_symbol(item) for item in symbols_raw)

    return Mt5HostObservation(
        observed_at=observed_at,
        terminal_connected=_bool(payload, "terminal_connected"),
        account_connected=_bool(payload, "account_connected"),
        account_trade_allowed=_bool(payload, "account_trade_allowed"),
        order_execution_enabled=_bool(payload, "order_execution_enabled"),
        engine_loop_healthy=_bool(payload, "engine_loop_healthy"),
        clock_ok=_bool(payload, "clock_ok"),
        symbols=symbols,
    )


def _timestamp(value: Any) -> datetime:
    if not isinstance(value, str):
        raise ValueError("observed_at must be an ISO-8601 string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("observed_at must be valid ISO-8601") from exc
    if parsed.tzinfo is None:
        raise ValueError("observed_at must be timezone-aware")
    return parsed


def _bool(payload: Mapping[str, Any], key: str) -> bool:
    value = payload[key]
    if type(value) is not bool:
        raise ValueError(f"{key} must be boolean")
    return value


def _symbol(value: Any) -> BrokerSymbol:
    if not isinstance(value, Mapping):
        raise ValueError("each symbol must be an object")
    missing = _SYMBOL_REQUIRED - value.keys()
    allowed = _SYMBOL_REQUIRED | {"contract_size", "volume_min", "volume_step"}
    unknown = value.keys() - allowed
    if missing:
        raise ValueError(f"missing symbol fields: {sorted(missing)}")
    if unknown:
        raise ValueError(f"unknown symbol fields: {sorted(unknown)}")
    name = value["name"]
    trade_mode = value["trade_mode"]
    digits = value["digits"]
    point = value["point"]
    if not isinstance(name, str) or not name.strip():
        raise ValueError("symbol name must be non-empty")
    if not isinstance(trade_mode, str) or not trade_mode.strip():
        raise ValueError("symbol trade_mode must be non-empty")
    if type(digits) is not int or digits < 0:
        raise ValueError("symbol digits must be a non-negative integer")
    if not isinstance(point, (int, float)) or isinstance(point, bool) or point <= 0:
        raise ValueError("symbol point must be positive")
    return BrokerSymbol(
        name=name,
        digits=digits,
        point=float(point),
        trade_mode=trade_mode,
        contract_size=_optional_positive(value.get("contract_size"), "contract_size"),
        volume_min=_optional_positive(value.get("volume_min"), "volume_min"),
        volume_step=_optional_positive(value.get("volume_step"), "volume_step"),
    )


def _optional_positive(value: Any, field: str) -> float | None:
    if value is None:
        return None
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
        raise ValueError(f"symbol {field} must be positive when supplied")
    return float(value)
