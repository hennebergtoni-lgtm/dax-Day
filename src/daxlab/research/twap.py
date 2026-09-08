"""Causal session-reset TWAP research primitive for TWAP001.

This is a price-time average over completed M5 closes, not VWAP. The audited
source has no trustworthy volume field. The entry candle is never included.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from typing import Iterable
from zoneinfo import ZoneInfo

BERLIN = ZoneInfo("Europe/Berlin")
SESSION_START = time(9, 0)
SESSION_END = time(17, 30)


@dataclass(frozen=True, slots=True)
class TwapBar:
    open_time: datetime
    close: float


@dataclass(frozen=True, slots=True)
class TwapState:
    state_time: datetime
    session_twap_close: float
    completed_bar_count: int


def session_twap_before_entry(
    bars: Iterable[TwapBar], *, entry_time: datetime, timeframe_minutes: int = 5
) -> TwapState | None:
    """Return session-reset close TWAP using information strictly before entry."""
    if entry_time.tzinfo is None:
        raise ValueError("entry_time must be timezone-aware")
    if timeframe_minutes <= 0:
        raise ValueError("timeframe_minutes must be positive")

    local_entry = entry_time.astimezone(BERLIN)
    session_date = local_entry.date()
    closes: list[float] = []
    latest: datetime | None = None
    delta = timedelta(minutes=timeframe_minutes)

    for bar in bars:
        if bar.open_time.tzinfo is None:
            raise ValueError("bar open_time must be timezone-aware")
        local_open = bar.open_time.astimezone(BERLIN)
        available = bar.open_time + delta
        if local_open.date() != session_date:
            continue
        if not (SESSION_START <= local_open.time() <= SESSION_END):
            continue
        if available >= entry_time:
            continue
        closes.append(float(bar.close))
        latest = available if latest is None or available > latest else latest

    if not closes or latest is None:
        return None
    return TwapState(
        state_time=latest,
        session_twap_close=sum(closes) / len(closes),
        completed_bar_count=len(closes),
    )
