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
TIMESTAMP_CONTRACT = "IG_MINUTE_5_SNAPSHOT_UTC_INTERVAL_END_V1"
_TIMEFRAME_DELTA = timedelta(minutes=5)
DEFAULT_MAX_AGE = timedelta(minutes=10)


@dataclass(frozen=True, slots=True)
class IgClosedM5Feed:
    """Normalized read-only IG price response supplied by a transport owner."""

    epic: str
    observed_at: datetime
    prices: Sequence[Mapping[str, object]]

    def __post_init__(self) -> None:
        if not self.epic or self.epic.strip() != self.epic:
            raise ValueError("IG epic must be non-empty without surrounding whitespace")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
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
    max_age: timedelta = DEFAULT_MAX_AGE
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
        rows = closed_m5_price_rows(feed.prices, observed_at=feed.observed_at)
        observed_at = feed.observed_at.astimezone(timezone.utc)
        if observed_at - ig_m5_interval(rows[-1])[1] > self.max_age:
            raise ValueError("IG candle source requires fresh M5 data")
        return rows

    def _to_candle(
        self,
        row: Mapping[str, object],
        *,
        received_at: datetime,
    ) -> Candle:
        event_time, close_time = ig_m5_interval(row)
        prices = {
            field: _midpoint_price(row, field)
            for field in ("openPrice", "highPrice", "lowPrice", "closePrice")
        }
        volume = _optional_non_negative_number(row.get("lastTradedVolume"), "lastTradedVolume")
        return Candle(
            instrument_id=self.instrument_id,
            timeframe=CANONICAL_TIMEFRAME,
            event_time=event_time,
            close_time=close_time,
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


def ig_m5_interval(row: Mapping[str, object]) -> tuple[datetime, datetime]:
    """Normalize this IG lane's supplied interval-end timestamp convention.

    The supplied IG Demo host sample at 09:02:59 includes a row labelled 09:05.
    This contract maps its 09:00 predecessor to [08:55, 09:00). IG REST docs
    call the field "Snapshot time" without formally specifying open versus close;
    the corrected lane still requires a real-host rerun, not an inferred VERIFIED.
    IG's wire UTC field may omit an offset; that field alone is assigned UTC.
    Never fall back to local snapshotTime or apply broker/DST wallclock offsets.
    See docs/IG_DEMO_M5_TIMESTAMP_HANDOFF.md for evidence and documentation limits.
    """
    raw = row.get("snapshotTimeUTC")
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("IG price row requires snapshotTimeUTC")
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("IG snapshotTimeUTC must be ISO-8601") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    close_time = parsed.astimezone(timezone.utc)
    if close_time.minute % 5 or close_time.second or close_time.microsecond:
        raise ValueError("IG snapshotTimeUTC must be aligned to the M5 boundary")
    return close_time - _TIMEFRAME_DELTA, close_time


def closed_m5_price_rows(
    prices: Sequence[Mapping[str, object]], *, observed_at: datetime,
) -> tuple[Mapping[str, object], ...]:
    """Validate the full response, then omit its not-yet-closed tail.

    This is the sole IG closure rule used by both the feed and host probe.
    Even an omitted live row must have a valid chronological timestamp; it
    cannot hide malformed, duplicated, gapped or implausibly future history.
    """
    if observed_at.tzinfo is None or observed_at.utcoffset() is None:
        raise ValueError("IG observed_at must be timezone-aware")
    if not prices:
        raise ValueError("IG candle source requires at least one M5 price row")
    if any(not isinstance(row, Mapping) for row in prices):
        raise ValueError("IG price row must be an object")
    rows = tuple(prices)
    close_times = tuple(ig_m5_interval(row)[1] for row in rows)
    if close_times != tuple(sorted(close_times)):
        raise ValueError("IG price rows must remain chronological")
    if len(set(close_times)) != len(close_times):
        raise ValueError("IG price timestamps must remain unique")
    if any(b - a != _TIMEFRAME_DELTA for a, b in zip(close_times, close_times[1:])):
        raise ValueError("IG price rows must remain continuous M5 bars")
    now = observed_at.astimezone(timezone.utc)
    next_boundary = now.replace(minute=now.minute - now.minute % 5, second=0,
                                microsecond=0) + _TIMEFRAME_DELTA
    if close_times[-1] > next_boundary:
        raise ValueError("IG history extends beyond the current M5 interval")
    closed = tuple(row for row, close in zip(rows, close_times) if close <= now)
    if not closed:
        raise ValueError("IG candle source accepts closed M5 bars only; none available")
    return closed


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
