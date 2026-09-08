"""Canonical runtime market-data contracts."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class RuntimeMode(StrEnum):
    HISTORICAL = "HISTORICAL"
    REPLAY = "REPLAY"
    SHADOW = "SHADOW"
    PAPER = "PAPER"
    LIVE = "LIVE"


class DataQualityState(StrEnum):
    OK = "OK"
    STALE = "STALE"
    GAP = "GAP"
    DUPLICATE = "DUPLICATE"
    OUT_OF_ORDER = "OUT_OF_ORDER"
    CLOCK_SKEW = "CLOCK_SKEW"
    SOURCE_DISAGREEMENT = "SOURCE_DISAGREEMENT"
    UNSAFE = "UNSAFE"


UNSAFE_STATES = frozenset(
    {
        DataQualityState.STALE,
        DataQualityState.GAP,
        DataQualityState.DUPLICATE,
        DataQualityState.OUT_OF_ORDER,
        DataQualityState.CLOCK_SKEW,
        DataQualityState.SOURCE_DISAGREEMENT,
        DataQualityState.UNSAFE,
    }
)


@dataclass(frozen=True, slots=True)
class Candle:
    symbol: str
    timeframe: str
    event_time: datetime
    close_time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float | None
    source: str
    received_at: datetime
    is_closed: bool
    quality_state: DataQualityState = DataQualityState.OK

    def __post_init__(self) -> None:
        if not self.symbol.strip() or not self.timeframe.strip() or not self.source.strip():
            raise ValueError("symbol, timeframe and source are required")
        if self.event_time.tzinfo is None or self.close_time.tzinfo is None or self.received_at.tzinfo is None:
            raise ValueError("runtime timestamps must be timezone-aware")
        if self.close_time <= self.event_time:
            raise ValueError("close_time must be after event_time")
        if self.high < max(self.open, self.close, self.low):
            raise ValueError("high violates OHLC invariants")
        if self.low > min(self.open, self.close, self.high):
            raise ValueError("low violates OHLC invariants")

    @property
    def safe_for_decision(self) -> bool:
        return self.is_closed and self.quality_state not in UNSAFE_STATES
