"""Read-only MT5 CLOSED-M5 adapter for the canonical NextGen market-data port.

The established runtime MT5 payload layer remains responsible for broker symbol
resolution, timestamp interpretation, freshness and continuity checks. This
adapter only maps an already validated ``ClosedM5Feed`` into broker-neutral UTC
``domain.market.Candle`` objects and exposes the pull-style ``CandleSourcePort``
shape. It contains no MetaTrader5 SDK import and no order/execution capability.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Callable

from daxlab.domain.market import Candle, DataQualityState, InstrumentId
from daxlab.runtime.mt5_feed_payload import ClosedM5Feed
from daxlab.runtime.mt5_readonly import Mt5Bar, closed_rates_start_pos


FeedProvider = Callable[[], ClosedM5Feed | None]
SOURCE_PREFIX = "MT5_READ_ONLY"
CANONICAL_TIMEFRAME = "M5"
_TIMEFRAME_DELTA = timedelta(minutes=5)


@dataclass(slots=True)
class Mt5ClosedM5CandleSource:
    """Stateful read-only adapter yielding each safe closed M5 bar at most once."""

    feed_provider: FeedProvider
    broker_symbol: str
    instrument_id: InstrumentId
    _last_close_time: datetime | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        clean_symbol = self.broker_symbol.strip()
        if not clean_symbol:
            raise ValueError("broker_symbol must be non-empty")
        if clean_symbol != self.broker_symbol:
            raise ValueError("broker_symbol must not contain leading or trailing whitespace")
        if not callable(self.feed_provider):
            raise TypeError("feed_provider must be callable")

    @property
    def last_close_time(self) -> datetime | None:
        return self._last_close_time

    def next_candle(self) -> Candle | None:
        """Return the earliest not-yet-emitted safe candle from the latest feed snapshot."""

        feed = self.feed_provider()
        if feed is None:
            return None
        self._validate_feed(feed)

        for bar in feed.bars:
            candle = self._to_candle(bar, observed_at=feed.observed_at)
            if self._last_close_time is None or candle.close_time > self._last_close_time:
                self._last_close_time = candle.close_time
                return candle
        return None

    def _validate_feed(self, feed: ClosedM5Feed) -> None:
        closed_rates_start_pos(feed.requested_start_pos)
        if not feed.bars:
            raise ValueError("MT5 candle source requires at least one closed M5 bar")
        if not feed.fresh:
            raise ValueError("MT5 candle source requires fresh market data")
        if feed.discontinuities:
            raise ValueError("MT5 candle source requires continuous closed M5 data")
        if feed.observed_at.tzinfo is None:
            raise ValueError("MT5 observed_at must be timezone-aware")

        open_times = tuple(bar.open_time for bar in feed.bars)
        if any(value.tzinfo is None for value in open_times):
            raise ValueError("MT5 bar timestamps must be timezone-aware")
        if open_times != tuple(sorted(open_times)):
            raise ValueError("MT5 bars must remain chronological")
        if len(set(open_times)) != len(open_times):
            raise ValueError("MT5 bar timestamps must remain unique")
        if any(bar.open_time + _TIMEFRAME_DELTA > feed.observed_at for bar in feed.bars):
            raise ValueError("MT5 candle source accepts closed bars only")

    def _to_candle(self, bar: Mt5Bar, *, observed_at: datetime) -> Candle:
        event_time = bar.open_time.astimezone(timezone.utc)
        close_time = (bar.open_time + _TIMEFRAME_DELTA).astimezone(timezone.utc)
        received_at = observed_at.astimezone(timezone.utc)
        return Candle(
            instrument_id=self.instrument_id,
            timeframe=CANONICAL_TIMEFRAME,
            event_time=event_time,
            close_time=close_time,
            open=float(bar.open),
            high=float(bar.high),
            low=float(bar.low),
            close=float(bar.close),
            volume=None,
            source=f"{SOURCE_PREFIX}:{self.broker_symbol}",
            received_at=received_at,
            is_closed=True,
            quality_state=DataQualityState.OK,
        )
