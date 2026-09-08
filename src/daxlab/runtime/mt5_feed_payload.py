"""Strict closed-M5 feed payload validation for future read-only MT5 probes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import json
from typing import Any, Mapping

from daxlab.runtime.mt5_readonly import Mt5Bar, closed_rates_start_pos


@dataclass(frozen=True, slots=True)
class ClosedM5Feed:
    observed_at: datetime
    requested_start_pos: int
    bars: tuple[Mt5Bar, ...]
    latest_closed_fingerprint: str
    age_seconds: float
    fresh: bool
    discontinuities: tuple[str, ...]


_REQUIRED = {"observed_at", "requested_start_pos", "max_age_seconds", "bars"}
_BAR_REQUIRED = {"open_time", "open", "high", "low", "close"}


def parse_closed_m5_feed(payload: Mapping[str, Any]) -> ClosedM5Feed:
    missing = _REQUIRED - payload.keys()
    unknown = payload.keys() - _REQUIRED
    if missing:
        raise ValueError(f"missing feed fields: {sorted(missing)}")
    if unknown:
        raise ValueError(f"unknown feed fields: {sorted(unknown)}")

    observed = _ts(payload["observed_at"], "observed_at")
    requested_start_pos = payload["requested_start_pos"]
    if type(requested_start_pos) is not int:
        raise ValueError("requested_start_pos must be integer")
    closed_rates_start_pos(requested_start_pos)

    max_age_seconds = _number(
        payload["max_age_seconds"],
        "max_age_seconds",
        allow_zero=True,
    )
    raw_bars = payload["bars"]
    if not isinstance(raw_bars, list) or not raw_bars:
        raise ValueError("bars must be a non-empty list")

    bars = tuple(_bar(item) for item in raw_bars)
    times = [bar.open_time for bar in bars]
    if times != sorted(times):
        raise ValueError("bars must be chronological")
    if len(set(times)) != len(times):
        raise ValueError("bar open_time values must be unique")

    for bar in bars:
        if bar.open_time + timedelta(minutes=5) > observed:
            raise ValueError("feed contains an unclosed M5 bar")

    latest = bars[-1]
    age_seconds = (
        observed - (latest.open_time + timedelta(minutes=5))
    ).total_seconds()

    discontinuities: list[str] = []
    for previous, current in zip(bars, bars[1:]):
        delta_seconds = (current.open_time - previous.open_time).total_seconds()
        if delta_seconds != 300:
            discontinuities.append(
                f"{previous.open_time.isoformat()}->"
                f"{current.open_time.isoformat()}:{int(delta_seconds)}s"
            )

    return ClosedM5Feed(
        observed_at=observed,
        requested_start_pos=requested_start_pos,
        bars=bars,
        latest_closed_fingerprint=_fingerprint(latest),
        age_seconds=age_seconds,
        fresh=age_seconds <= max_age_seconds,
        discontinuities=tuple(discontinuities),
    )


def feed_blocker(feed: ClosedM5Feed) -> str | None:
    if not feed.fresh:
        return "MARKET_DATA_STALE"
    if feed.discontinuities:
        return "MARKET_DATA_DISCONTINUITY"
    return None


def _bar(value: Any) -> Mt5Bar:
    if not isinstance(value, Mapping):
        raise ValueError("each bar must be an object")

    missing = _BAR_REQUIRED - value.keys()
    unknown = value.keys() - _BAR_REQUIRED
    if missing:
        raise ValueError(f"missing bar fields: {sorted(missing)}")
    if unknown:
        raise ValueError(f"unknown bar fields: {sorted(unknown)}")

    open_time = _ts(value["open_time"], "open_time")
    open_price = _number(value["open"], "open")
    high_price = _number(value["high"], "high")
    low_price = _number(value["low"], "low")
    close_price = _number(value["close"], "close")

    if high_price < max(open_price, close_price, low_price):
        raise ValueError("OHLC invariant violated")
    if low_price > min(open_price, close_price, high_price):
        raise ValueError("OHLC invariant violated")

    return Mt5Bar(
        open_time=open_time,
        open=open_price,
        high=high_price,
        low=low_price,
        close=close_price,
    )


def _ts(value: Any, field: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be ISO-8601 string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be valid ISO-8601") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must be timezone-aware")
    return parsed


def _number(value: Any, field: str, allow_zero: bool = False) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{field} must be numeric")
    parsed = float(value)
    if field == "max_age_seconds" and (
        parsed < 0 or (parsed == 0 and not allow_zero)
    ):
        raise ValueError("max_age_seconds must be non-negative")
    return parsed


def _fingerprint(bar: Mt5Bar) -> str:
    canonical = json.dumps(
        {
            "open_time": bar.open_time.isoformat(),
            "open": bar.open,
            "high": bar.high,
            "low": bar.low,
            "close": bar.close,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode()).hexdigest()
