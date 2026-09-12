"""Canonical broker- and storage-neutral market-data domain contracts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from math import isfinite


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
class InstrumentId:
    """Stable product identity independent of any broker-specific symbol alias."""

    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip()
        if not normalized:
            raise ValueError("instrument id is required")
        if normalized != self.value:
            raise ValueError("instrument id must not contain leading or trailing whitespace")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class Candle:
    """Canonical closed/open bar event with explicit UTC and source provenance."""

    instrument_id: InstrumentId
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
        if not self.timeframe.strip() or not self.source.strip():
            raise ValueError("timeframe and source are required")
        for field_name, value in (
            ("event_time", self.event_time),
            ("close_time", self.close_time),
            ("received_at", self.received_at),
        ):
            _require_utc(value, field_name)
        if self.close_time <= self.event_time:
            raise ValueError("close_time must be after event_time")

        prices = (self.open, self.high, self.low, self.close)
        if not all(isfinite(value) for value in prices):
            raise ValueError("OHLC values must be finite")
        if self.high < max(self.open, self.close, self.low):
            raise ValueError("high violates OHLC invariants")
        if self.low > min(self.open, self.close, self.high):
            raise ValueError("low violates OHLC invariants")
        if self.volume is not None and (not isfinite(self.volume) or self.volume < 0):
            raise ValueError("volume must be finite and non-negative when provided")

    @property
    def safe_for_decision(self) -> bool:
        return self.is_closed and self.quality_state not in UNSAFE_STATES


def _require_utc(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError(f"{field_name} must be timezone-aware UTC")
