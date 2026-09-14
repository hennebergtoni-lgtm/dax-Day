"""Read-only IG CLOSED-M5 adapter for canonical broker-neutral candles.

The network/session layer is deliberately outside this module. A provider supplies
already-fetched IG price payloads together with the broker EPIC and observation
time. This adapter performs deterministic quote-bar normalization only and has no
credentials, HTTP dependency, dealing endpoint or execution capability.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from math import isfinite
from typing import Callable, Mapping, Sequence

from daxlab.domain.market import Candle, DataQualityState, InstrumentId


CANONICAL_TIMEFRAME = "M5"
SOURCE_PREFIX = "IG_READ_ONLY"
_TIMEFRAME_DELTA = timedelta(minutes=5)
_DEFAULT_MAX_AGE = timedelta(minutes=10)


@dataclass(frozen=True, slots=True)
class IgClosedM5Feed:
    """Normalized read-only IG price response supplied by a transport owner."""

    epic: str
    observed_at: datetime
    prices: Sequence[Mapping[str, object]]

    def __post_init__(self) -> None:
        if not self.epic or self.epic.strip() != self.epic:
            raise ValueError("IG epic must be non-empty without surrounding whitespace")
        if self.observed_at.tzinfo is None:
            raise ValueError("IG observed_at must be timezone-aware")


FeedProvider = Callable[[], IgClosedM5Feed | None]


@dataclass(slots=True)
class IgClosedM5CandleSource:
    """Yield each safe closed IG M5 quote candle at most once.

    IG historical price rows expose bid/ask OHLC independently and may omit
    ``lastTraded``. The canonical price is therefore the deterministic midpoint
    of bid and ask for each OHLC component. No last-traded value is fabricated.
    """

    feed_provider: FeedProvider
    epic: str
    instrument_id: InstrumentId
    max_age: timedelta = _DEFAULT_MAX_AGE
    _last_close_time: datetime | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if not callable(self.feed_provider):
            raise TypeError("feed_provider must be callable")
        if not self.epic or self.epic.strip() != self.epic:
            raise ValueError("epic must be non-empty without surrounding whitespace")
        if self.max_age <= timedelta(0):
            raise ValueError("max_age must be positive")

    @property
    def last_close_time(self) -> datetime | None:
        return self._last_close_time

    def next_candle(self) -> Candle | None:
        feed = self.feed_provider()
        if feed is None:
            return None
        rows = self._validate_feed(feed)
        received_at = feed.observed_at.astimezone(timezone.utc)

        for row in rows:
            candle = self._to_candle(row, received_at=received_at)
            if self._last_close_time is None or candle.close_time > self._last_close_time:
                self._last_close_time = candle.close_time
                return candle
        return None

    def _validate_feed(
        self,
        feed: IgClosedM5Feed,
    ) -> tuple[Mapping[str, object], ...]:
        if feed.epic != self.epic:
            raise ValueError("IG feed epic does not match configured epic")
        if not feed.prices:
            raise ValueError("IG candle source requires at least one M5 price row")

        rows = tuple(feed.prices)
        open_times = tuple(_snapshot_time_utc(row) for row in rows)
        if open_times != tuple(sorted(open_times)):
            raise ValueError("IG price rows must remain chronological")
        if len(set(open_times)) != len(open_times):
            raise ValueError("IG price timestamps must remain unique")
        if any(
            current - previous != _TIMEFRAME_DELTA
            for previous, current in zip(open_times, open_times[1:])
        ):
            raise ValueError("IG price rows must remain continuous M5 bars")

        observed_at = feed.observed_at.astimezone(timezone.utc)
        close_times = tuple(open_time + _TIMEFRAME_DELTA for open_time in open_times)
        if any(close_time > observed_at for close_time in close_times):
            raise ValueError("IG candle source accepts closed M5 bars only")
        if observed_at - close_times[-1] > self.max_age:
            raise ValueError("IG candle source requires fresh M5 data")
        return rows

    def _to_candle(
        self,
        row: Mapping[str, object],
        *,
        received_at: datetime,
    ) -> Candle:
        event_time = _snapshot_time_utc(row)
        prices = {
            field: _midpoint_price(row, field)
            for field in ("openPrice", "highPrice", "lowPrice", "closePrice")
        }
        volume = _optional_non_negative_number(row.get("lastTradedVolume"), "lastTradedVolume")
        return Candle(
            instrument_id=self.instrument_id,
            timeframe=CANONICAL_TIMEFRAME,
            event_time=event_time,
            close_time=event_time + _TIMEFRAME_DELTA,
            open=prices["openPrice"],
            high=prices["highPrice"],
            low=prices["lowPrice"],
            close=prices["closePrice"],
            volume=volume,
            source=f"{SOURCE_PREFIX}:{self.epic}:MID_BID_ASK",
            received_at=received_at,
            is_closed=True,
            quality_state=DataQualityState.OK,
        )


def _snapshot_time_utc(row: Mapping[str, object]) -> datetime:
    raw = row.get("snapshotTimeUTC")
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("IG price row requires snapshotTimeUTC")
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("IG snapshotTimeUTC must be ISO-8601") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _midpoint_price(row: Mapping[str, object], field: str) -> float:
    raw = row.get(field)
    if not isinstance(raw, Mapping):
        raise ValueError(f"IG {field} must contain bid and ask")
    bid = _required_finite_number(raw.get("bid"), f"{field}.bid")
    ask = _required_finite_number(raw.get("ask"), f"{field}.ask")
    if ask < bid:
        raise ValueError(f"IG {field} ask must not be below bid")
    return (bid + ask) / 2.0


def _required_finite_number(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"IG {field} must be numeric")
    result = float(value)
    if not isfinite(result):
        raise ValueError(f"IG {field} must be finite")
    return result


def _optional_non_negative_number(value: object, field: str) -> float | None:
    if value is None:
        return None
    result = _required_finite_number(value, field)
    if result < 0:
        raise ValueError(f"IG {field} must be non-negative")
    return result
