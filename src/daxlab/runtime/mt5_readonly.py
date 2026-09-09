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
    symbols: Iterable[BrokerSymbol],
    *,
    configured_symbol: str | None = None,
    allow_data_only: bool = False,
) -> SymbolResolution:
    """Resolve DAX broker symbol conservatively; ambiguity fails closed.

    `allow_data_only=True` permits a uniquely identified disabled/close-only DAX
    symbol for market-data observation only. It does not imply trading capability.

    Bare ``DAX`` is intentionally not auto-resolved because brokers may use that
    ticker for ETFs or other non-index instruments. A broker whose index really is
    named ``DAX`` remains supported through ``configured_symbol="DAX"``.
    """
    items = tuple(symbols)
    if configured_symbol is not None:
        exact = [s for s in items if s.name == configured_symbol]
        if len(exact) == 1:
            mode = exact[0].trade_mode.upper()
            if mode in {"DISABLED", "CLOSEONLY"} and allow_data_only:
                state = "CONFIGURED_EXACT_DATA_ONLY"
            else:
                state = "CONFIGURED_EXACT"
            return SymbolResolution("DAX", state, exact[0], (exact[0].name,))
        return SymbolResolution("DAX", "CONFIGURED_NOT_FOUND", None, tuple())

    aliases = {"DAX40", "DE40", "GER40", "GER30"}
    exact_aliases = [s for s in items if s.name.upper() in aliases]
    tradeable = [s for s in exact_aliases if s.trade_mode.upper() not in {"DISABLED", "CLOSEONLY"}]
    if len(tradeable) == 1:
        s = tradeable[0]
        return SymbolResolution("DAX", "AUTO_EXACT_ALIAS", s, (s.name,))
    if len(tradeable) > 1:
        return SymbolResolution(
            "DAX", "AMBIGUOUS", None, tuple(sorted(s.name for s in tradeable))
        )
    if allow_data_only and len(exact_aliases) == 1:
        s = exact_aliases[0]
        return SymbolResolution("DAX", "AUTO_EXACT_ALIAS_DATA_ONLY", s, (s.name,))
    if allow_data_only and len(exact_aliases) > 1:
        return SymbolResolution(
            "DAX", "AMBIGUOUS_DATA_ONLY", None, tuple(sorted(s.name for s in exact_aliases))
        )
    return SymbolResolution("DAX", "NOT_FOUND", None, tuple())


def closed_rates_start_pos(requested_start_pos: int = 1) -> int:
    """Validate an MT5 rates request for closed bars only."""
    if requested_start_pos < 1:
        raise ValueError("MT5 closed-bar rates request must start at position >= 1")
    return requested_start_pos


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


def closed_bar_age_seconds(
    *, latest_closed_bar_open: datetime, timeframe_minutes: int, observed_at: datetime
) -> float:
    """Return age of the latest bar close at the observation time."""
    if latest_closed_bar_open.tzinfo is None or observed_at.tzinfo is None:
        raise ValueError("MT5 freshness timestamps must be timezone-aware")
    if timeframe_minutes <= 0:
        raise ValueError("timeframe_minutes must be positive")
    closed_at = latest_closed_bar_open + timedelta(minutes=timeframe_minutes)
    age = (observed_at - closed_at).total_seconds()
    if age < 0:
        raise ValueError("latest_closed_bar_open is not closed at observed_at")
    return age


def market_data_is_fresh(
    *,
    latest_closed_bar_open: datetime,
    timeframe_minutes: int,
    observed_at: datetime,
    max_age_seconds: float,
) -> bool:
    """Fail closed when the latest completed bar is older than the configured watchdog limit."""
    if max_age_seconds < 0:
        raise ValueError("max_age_seconds must be non-negative")
    return closed_bar_age_seconds(
        latest_closed_bar_open=latest_closed_bar_open,
        timeframe_minutes=timeframe_minutes,
        observed_at=observed_at,
    ) <= max_age_seconds
