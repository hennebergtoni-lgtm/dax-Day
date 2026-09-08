"""MetaTrader 5 read-only adapter boundary primitives.

No MetaTrader5 package import and no order capability live in this module. It
normalizes external observations before they can reach the Decision Core.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable


@dataclass(frozen=True, slots=True)
class BrokerSymbol:
    name: str
    digits: int
    point: float
    trade_mode: str
    contract_size: float | None = None
    volume_min: float | None = None
    volume_step: float | None = None


@dataclass(frozen=True, slots=True)
class SymbolResolution:
    canonical_symbol: str
    state: str
    broker_symbol: BrokerSymbol | None
    candidates: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Mt5Bar:
    open_time: datetime
    open: float
    high: float
    low: float
    close: float


@dataclass(frozen=True, slots=True)
class Mt5Health:
    terminal_connected: bool
    account_connected: bool
    symbol_available: bool
    market_data_fresh: bool
    clock_ok: bool
    read_only_mode: bool
    engine_loop_healthy: bool

    @property
    def green(self) -> bool:
        return all(
            (
                self.terminal_connected,
                self.account_connected,
                self.symbol_available,
                self.market_data_fresh,
                self.clock_ok,
                self.read_only_mode,
                self.engine_loop_healthy,
            )
        )


def resolve_dax_symbol(
    symbols: Iterable[BrokerSymbol], *, configured_symbol: str | None = None
) -> SymbolResolution:
    """Resolve DAX broker symbol conservatively; ambiguity fails closed."""
    items = tuple(symbols)
    if configured_symbol is not None:
        exact = [s for s in items if s.name == configured_symbol]
        if len(exact) == 1:
            return SymbolResolution("DAX", "CONFIGURED_EXACT", exact[0], (exact[0].name,))
        return SymbolResolution("DAX", "CONFIGURED_NOT_FOUND", None, tuple())

    aliases = {"DAX", "DAX40", "DE40", "GER40", "GER30"}
    exact_aliases = [s for s in items if s.name.upper() in aliases]
    tradeable = [s for s in exact_aliases if s.trade_mode.upper() not in {"DISABLED", "CLOSEONLY"}]
    if len(tradeable) == 1:
        s = tradeable[0]
        return SymbolResolution("DAX", "AUTO_EXACT_ALIAS", s, (s.name,))
    if len(tradeable) > 1:
        return SymbolResolution(
            "DAX", "AMBIGUOUS", None, tuple(sorted(s.name for s in tradeable))
        )
    return SymbolResolution("DAX", "NOT_FOUND", None, tuple())


def closed_bars(
    bars: Iterable[Mt5Bar], *, timeframe_minutes: int, observed_at: datetime
) -> tuple[Mt5Bar, ...]:
    """Return only fully closed bars; the current/open bar is excluded."""
    if observed_at.tzinfo is None:
        raise ValueError("observed_at must be timezone-aware")
    if timeframe_minutes <= 0:
        raise ValueError("timeframe_minutes must be positive")
    result = []
    delta = timedelta(minutes=timeframe_minutes)
    for bar in bars:
        if bar.open_time.tzinfo is None:
            raise ValueError("MT5 bar timestamps must be timezone-aware")
        if bar.open_time + delta <= observed_at:
            result.append(bar)
    return tuple(sorted(result, key=lambda b: b.open_time))
