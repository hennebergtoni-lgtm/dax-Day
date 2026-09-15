"""Canonical IG M5 market-data contract and read-only candle normalization.

Attempt03 original evidence establishes the operational interval mapping. IG's raw
snapshotTimeUTC is the interval start; canonical close is five minutes later.
The transport/session owner stays outside this module. This module is the sole
owner of timestamp semantics, closure, Candidate finalization, freshness and
normalized provenance. It has no credentials, HTTP dependency or execution path.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from math import isfinite
from typing import Callable, Mapping, Sequence

from daxlab.domain.market import Candle, DataQualityState, InstrumentId


CANONICAL_TIMEFRAME = "M5"
SOURCE_PREFIX = "IG_READ_ONLY"
MARKET_DATA_CONTRACT_SCHEMA = "DAXLAB_IG_M5_MARKET_DATA_CONTRACT_V2"
TIMESTAMP_CONTRACT = "IG_MINUTE_5_SNAPSHOT_UTC_INTERVAL_START_V2"
CANDIDATE_FINALIZATION_CONTRACT = "IG_M5_TRUE_CLOSE_NO_EXTRA_GRACE_V2"
PROVIDER_TIMESTAMP_SEMANTICS = "INTERVAL_START"
PROVIDER_REVISION_STATE = "POST_CLOSE_REVISION_BOUND_NOT_ESTABLISHED"
_TIMEFRAME_DELTA = timedelta(minutes=5)
DEFAULT_MAX_AGE = timedelta(minutes=10)

_ATTEMPT03_PROVENANCE = {
    "namespace": ".runtime/ig_raw_m5_truth_2233_v2_attempt_03",
    "evidence_head": "2a99f96e06f7ce1f311c767dec43d236bb63eedd",
    "export_runtime_head": "7728453c3c4f8fcd2cf6f8189b0f94562ccfa04f",
    "original_bundle": "ig_raw_truth_2233_attempt_03_originals.zip",
    "historical_review": "DAX_IG_RAW_REVIEW_V1:OTHER_UNKNOWN:PRESERVED",
    "final_review": "DAX_IG_RAW_REVIEW_V2:INTERVAL_START",
}


def canonical_ig_m5_contract() -> dict[str, object]:
    """Return the immutable, manifest-safe canonical contract projection."""
    return {
        "schema": MARKET_DATA_CONTRACT_SCHEMA,
        "raw_timestamp_field": "snapshotTimeUTC",
        "raw_timestamp_semantics": PROVIDER_TIMESTAMP_SEMANTICS,
        "event_time_rule": "event_time=snapshotTimeUTC",
        "close_time_rule": "close_time=snapshotTimeUTC+PT5M",
        "closed_rule": "close_time<=price_request_started_at_utc",
        "candidate_finalized_rule": "closed;no_additional_time_grace",
        "candidate_finalization_contract": CANDIDATE_FINALIZATION_CONTRACT,
        "freshness_rule": "age=observation_time-close_time",
        "freshness_max_age_seconds": DEFAULT_MAX_AGE.total_seconds(),
        "revision_state": PROVIDER_REVISION_STATE,
        "raw_provenance": dict(_ATTEMPT03_PROVENANCE),
        "normalized_provenance": TIMESTAMP_CONTRACT,
    }


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
    """Yield each canonical, true-close IG M5 quote candle at most once."""

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


def raw_snapshot_time_utc(row: Mapping[str, object]) -> datetime:
    """Parse only IG's raw UTC field; never use local snapshotTime as fallback."""
    raw = row.get("snapshotTimeUTC")
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("IG price row requires snapshotTimeUTC")
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("IG snapshotTimeUTC must be ISO-8601") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    event_time = parsed.astimezone(timezone.utc)
    if event_time.minute % 5 or event_time.second or event_time.microsecond:
        raise ValueError("IG snapshotTimeUTC must be aligned to the M5 boundary")
    return event_time


def ig_m5_interval(row: Mapping[str, object]) -> tuple[datetime, datetime]:
    """Map the verified interval-start wire timestamp to [event, event+5m)."""
    event_time = raw_snapshot_time_utc(row)
    return event_time, event_time + _TIMEFRAME_DELTA


def closed_m5_price_rows(
    prices: Sequence[Mapping[str, object]], *, observed_at: datetime,
) -> tuple[Mapping[str, object], ...]:
    """Validate the full response and exclude every row whose true close is future."""
    if observed_at.tzinfo is None or observed_at.utcoffset() is None:
        raise ValueError("IG observed_at must be timezone-aware")
    if not prices:
        raise ValueError("IG candle source requires at least one M5 price row")
    if any(not isinstance(row, Mapping) for row in prices):
        raise ValueError("IG price row must be an object")
    rows = tuple(prices)
    intervals = tuple(ig_m5_interval(row) for row in rows)
    event_times = tuple(interval[0] for interval in intervals)
    close_times = tuple(interval[1] for interval in intervals)
    if event_times != tuple(sorted(event_times)):
        raise ValueError("IG price rows must remain chronological")
    if len(set(event_times)) != len(event_times):
        raise ValueError("IG price timestamps must remain unique")
    if any(b - a != _TIMEFRAME_DELTA for a, b in zip(event_times, event_times[1:])):
        raise ValueError("IG price rows must remain continuous M5 bars")
    now = observed_at.astimezone(timezone.utc)
    current_boundary = now.replace(
        minute=now.minute - now.minute % 5,
        second=0,
        microsecond=0,
    )
    if event_times[-1] > current_boundary:
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
