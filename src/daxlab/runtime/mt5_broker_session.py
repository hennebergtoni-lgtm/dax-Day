"""Broker/session observation normalization; never rewrites historical assumptions."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, time
from zoneinfo import ZoneInfo
from daxlab.runtime.mt5_readonly import BrokerSymbol, resolve_dax_symbol

@dataclass(frozen=True, slots=True)
class BrokerSessionObservation:
    broker_timezone: str
    observed_at: datetime
    session_open: time | None
    session_close: time | None
    session_source: str

@dataclass(frozen=True, slots=True)
class SymbolAudit:
    state: str
    configured_symbol: str | None
    selected_symbol: str | None
    candidates: tuple[tuple[str,int,float,str], ...]

def normalize_to_berlin(value: datetime, broker_timezone: str) -> datetime:
    if value.tzinfo is None: raise ValueError("broker timestamp must be timezone-aware")
    ZoneInfo(broker_timezone)  # validates IANA zone
    return value.astimezone(ZoneInfo("Europe/Berlin"))

def validate_session_observation(obs: BrokerSessionObservation) -> None:
    ZoneInfo(obs.broker_timezone)
    if obs.observed_at.tzinfo is None: raise ValueError("observed_at must be timezone-aware")
    if obs.session_source not in {"BROKER_OBSERVED","BROKER_DOCUMENTED","UNKNOWN"}: raise ValueError("invalid session_source")
    if (obs.session_open is None) != (obs.session_close is None): raise ValueError("session open/close must be supplied together")
    if obs.session_source=="UNKNOWN" and (obs.session_open is not None or obs.session_close is not None): raise ValueError("unknown session source cannot assert session hours")

def symbol_audit(symbols: tuple[BrokerSymbol,...], configured_symbol: str|None=None) -> SymbolAudit:
    r=resolve_dax_symbol(symbols,configured_symbol=configured_symbol)
    candidates=tuple(sorted((s.name,s.digits,s.point,s.trade_mode) for s in symbols if s.name in r.candidates))
    return SymbolAudit(r.state,configured_symbol,r.broker_symbol.name if r.broker_symbol else None,candidates)
