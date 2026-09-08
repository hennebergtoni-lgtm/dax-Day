"""Deterministic data-quality classification for closed-candle pipelines."""
from __future__ import annotations

from datetime import timedelta

from daxlab.runtime.contracts import Candle, DataQualityState


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


def source_agrees(left: Candle, right: Candle, *, tolerance: float = 0.0) -> DataQualityState:
    """Compare two source candles for the same bar."""
    if left.event_time != right.event_time or left.timeframe != right.timeframe:
        return DataQualityState.SOURCE_DISAGREEMENT
    values_left = (left.open, left.high, left.low, left.close)
    values_right = (right.open, right.high, right.low, right.close)
    if any(abs(a - b) > tolerance for a, b in zip(values_left, values_right, strict=True)):
        return DataQualityState.SOURCE_DISAGREEMENT
    return DataQualityState.OK
