"""Fail-closed contract for observations from a real MT5 host.

This module deliberately has no MetaTrader5 dependency and no order API. A
Windows-side probe can serialize observations into this contract; the research
lab only accepts them after validation.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from daxlab.runtime.mt5_readonly import BrokerSymbol, Mt5Health, SymbolResolution, resolve_dax_symbol


@dataclass(frozen=True, slots=True)
class Mt5HostObservation:
    observed_at: datetime
    terminal_connected: bool
    account_connected: bool
    account_trade_allowed: bool
    order_execution_enabled: bool
    engine_loop_healthy: bool
    clock_ok: bool
    symbols: tuple[BrokerSymbol, ...]


@dataclass(frozen=True, slots=True)
class Mt5Handshake:
    health: Mt5Health
    symbol_resolution: SymbolResolution
    reason: str


def validate_read_only_host(
    observation: Mt5HostObservation,
    *,
    market_data_fresh: bool,
    configured_symbol: str | None = None,
    allow_data_only: bool = False,
) -> Mt5Handshake:
    """Validate a host observation without ever granting execution capability."""
    if observation.observed_at.tzinfo is None:
        raise ValueError("MT5 host observation timestamp must be timezone-aware")
    if observation.order_execution_enabled:
        return _blocked(observation, "ORDER_EXECUTION_ENABLED", allow_data_only=allow_data_only)

    resolution = resolve_dax_symbol(
        observation.symbols,
        configured_symbol=configured_symbol,
        allow_data_only=allow_data_only,
    )
    symbol_available = resolution.broker_symbol is not None
    health = Mt5Health(
        terminal_connected=observation.terminal_connected,
        account_connected=observation.account_connected,
        symbol_available=symbol_available,
        market_data_fresh=market_data_fresh,
        clock_ok=observation.clock_ok,
        read_only_mode=True,
        engine_loop_healthy=observation.engine_loop_healthy,
    )
    if not observation.terminal_connected:
        reason = "TERMINAL_NOT_CONNECTED"
    elif not observation.account_connected:
        reason = "ACCOUNT_NOT_CONNECTED"
    elif not symbol_available:
        reason = f"SYMBOL_{resolution.state}"
    elif not market_data_fresh:
        reason = "MARKET_DATA_STALE"
    elif not observation.clock_ok:
        reason = "CLOCK_NOT_OK"
    elif not observation.engine_loop_healthy:
        reason = "ENGINE_LOOP_UNHEALTHY"
    else:
        reason = "READ_ONLY_HEALTHY"
    return Mt5Handshake(health=health, symbol_resolution=resolution, reason=reason)


def _blocked(
    observation: Mt5HostObservation,
    reason: str,
    *,
    allow_data_only: bool = False,
) -> Mt5Handshake:
    resolution = resolve_dax_symbol(observation.symbols, allow_data_only=allow_data_only)
    health = Mt5Health(
        terminal_connected=observation.terminal_connected,
        account_connected=observation.account_connected,
        symbol_available=False,
        market_data_fresh=False,
        clock_ok=observation.clock_ok,
        read_only_mode=False,
        engine_loop_healthy=observation.engine_loop_healthy,
    )
    return Mt5Handshake(health=health, symbol_resolution=resolution, reason=reason)
