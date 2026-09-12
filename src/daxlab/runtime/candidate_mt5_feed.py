"""Explicit read-only MT5 CLOSED-M5 -> CAND-001 Candle bridge.

Timestamp interpretation, freshness and discontinuity detection remain owned by
``mt5_feed_payload``. This module only converts an already validated/fresh feed
into the canonical runtime Candle contract used by CAND-001.
"""
from __future__ import annotations

from datetime import timedelta

from daxlab.runtime.contracts import Candle, DataQualityState
from daxlab.runtime.mt5_feed_payload import ClosedM5Feed
from daxlab.runtime.mt5_readonly import Mt5Bar


SOURCE_PREFIX = "MT5_READ_ONLY"
CANDIDATE_TIMEFRAME = "5m"


def mt5_bar_to_candidate_candle(
    bar: Mt5Bar,
    *,
    broker_symbol: str,
    observed_at,
    runtime_symbol: str = "DE40",
) -> Candle:
    """Convert one already-closed MT5 M5 bar without changing its time semantics."""
    clean_broker_symbol = broker_symbol.strip()
    clean_runtime_symbol = runtime_symbol.strip()
    if not clean_broker_symbol:
        raise ValueError("broker_symbol must be non-empty")
    if not clean_runtime_symbol:
        raise ValueError("runtime_symbol must be non-empty")
    if bar.open_time.tzinfo is None or observed_at.tzinfo is None:
        raise ValueError("MT5 candidate timestamps must be timezone-aware")
    close_time = bar.open_time + timedelta(minutes=5)
    if close_time > observed_at:
        raise ValueError("MT5 candidate bridge accepts closed bars only")

    return Candle(
        symbol=clean_runtime_symbol,
        timeframe=CANDIDATE_TIMEFRAME,
        event_time=bar.open_time,
        close_time=close_time,
        open=float(bar.open),
        high=float(bar.high),
        low=float(bar.low),
        close=float(bar.close),
        volume=None,
        source=f"{SOURCE_PREFIX}:{clean_broker_symbol}",
        received_at=observed_at,
        is_closed=True,
        quality_state=DataQualityState.OK,
    )


def validated_mt5_feed_to_candidate_candles(
    feed: ClosedM5Feed,
    *,
    broker_symbol: str,
    runtime_symbol: str = "DE40",
) -> tuple[Candle, ...]:
    """Convert one validated current MT5 feed; unsafe feed state fails closed."""
    if not feed.fresh:
        raise ValueError("CAND-001 requires fresh MT5 CLOSED-M5 feed")
    if feed.discontinuities:
        raise ValueError("CAND-001 requires continuous MT5 CLOSED-M5 feed")
    if not feed.bars:
        raise ValueError("CAND-001 requires at least one MT5 CLOSED-M5 bar")

    candles = tuple(
        mt5_bar_to_candidate_candle(
            bar,
            broker_symbol=broker_symbol,
            observed_at=feed.observed_at,
            runtime_symbol=runtime_symbol,
        )
        for bar in feed.bars
    )
    close_times = tuple(candle.close_time for candle in candles)
    if close_times != tuple(sorted(close_times)):
        raise ValueError("candidate candles must remain chronological")
    if len(set(close_times)) != len(close_times):
        raise ValueError("candidate candle close times must remain unique")
    return candles
