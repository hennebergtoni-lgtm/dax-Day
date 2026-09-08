"""Deterministic data-quality classification for closed-candle pipelines."""
from __future__ import annotations

from datetime import timedelta

from daxlab.runtime.contracts import Candle, DataQualityState
from daxlab.runtime.time import to_berlin


def classify_sequence(
    previous: Candle | None,
    current: Candle,
    expected_interval: timedelta,
    *,
    max_receive_delay: timedelta = timedelta(minutes=2),
) -> DataQualityState:
    """Classify one candle without silently repairing ordering or timing defects."""
    if not current.is_closed:
        return DataQualityState.UNSAFE
    if current.received_at < current.close_time:
        return DataQualityState.CLOCK_SKEW
    if current.received_at - current.close_time > max_receive_delay:
        return DataQualityState.STALE
    if previous is None:
        return current.quality_state
    if current.event_time == previous.event_time:
        return DataQualityState.DUPLICATE
    if current.event_time < previous.event_time:
        return DataQualityState.OUT_OF_ORDER
    if current.event_time - previous.event_time > expected_interval:
        return DataQualityState.GAP
    return current.quality_state


def classify_session_sequence(
    previous: Candle | None,
    current: Candle,
    expected_interval: timedelta,
    *,
    max_receive_delay: timedelta = timedelta(minutes=2),
) -> DataQualityState:
    """Classify a stream already partitioned to the Berlin trading session.

    A new Berlin calendar day resets the intraday adjacency check so the expected
    overnight closure is not mislabeled as an M5 GAP. This function does not prove
    that every expected trading day exists; session-calendar completeness remains a
    separate dataset/replay gate.
    """
    if previous is not None and to_berlin(previous.event_time).date() != to_berlin(
        current.event_time
    ).date():
        previous = None
    return classify_sequence(
        previous,
        current,
        expected_interval,
        max_receive_delay=max_receive_delay,
    )


def source_agrees(left: Candle, right: Candle, *, tolerance: float = 0.0) -> DataQualityState:
    """Compare two source candles for the same bar."""
    if left.event_time != right.event_time or left.timeframe != right.timeframe:
        return DataQualityState.SOURCE_DISAGREEMENT
    values_left = (left.open, left.high, left.low, left.close)
    values_right = (right.open, right.high, right.low, right.close)
    if any(abs(a - b) > tolerance for a, b in zip(values_left, values_right, strict=True)):
        return DataQualityState.SOURCE_DISAGREEMENT
    return DataQualityState.OK
