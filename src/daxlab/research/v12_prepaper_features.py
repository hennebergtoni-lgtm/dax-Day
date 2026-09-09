"""Causal OHLC-only feature primitives for V12 pre-paper research.

Research only: no production promotion and no execution capability.
All functions consume closed bars only and never inspect bars after ``asof_index``.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import fsum
from typing import Sequence


@dataclass(frozen=True, slots=True)
class ClosedBar:
    open: float
    high: float
    low: float
    close: float

    def __post_init__(self) -> None:
        if self.high < max(self.open, self.close) or self.low > min(self.open, self.close):
            raise ValueError("invalid OHLC bar")
        if self.high < self.low:
            raise ValueError("high below low")


@dataclass(frozen=True, slots=True)
class AdxFeature:
    adx: float
    plus_di: float
    minus_di: float


@dataclass(frozen=True, slots=True)
class BodyQualityFeature:
    body_fraction: float
    close_location: float
    direction: int


@dataclass(frozen=True, slots=True)
class CompressionFeature:
    true_range: float
    mean_true_range: float
    tr_ratio: float


def _closed_prefix(bars: Sequence[ClosedBar], asof_index: int) -> Sequence[ClosedBar]:
    if asof_index < 0 or asof_index >= len(bars):
        raise IndexError("asof_index outside closed-bar sequence")
    return bars[: asof_index + 1]


def _true_range(current: ClosedBar, previous_close: float | None) -> float:
    if previous_close is None:
        return current.high - current.low
    return max(
        current.high - current.low,
        abs(current.high - previous_close),
        abs(current.low - previous_close),
    )


def body_quality(bars: Sequence[ClosedBar], asof_index: int) -> BodyQualityFeature:
    bar = _closed_prefix(bars, asof_index)[-1]
    span = bar.high - bar.low
    if span <= 0:
        return BodyQualityFeature(body_fraction=0.0, close_location=0.5, direction=0)
    body = abs(bar.close - bar.open) / span
    location = (bar.close - bar.low) / span
    direction = 1 if bar.close > bar.open else -1 if bar.close < bar.open else 0
    return BodyQualityFeature(body_fraction=body, close_location=location, direction=direction)


def range_compression(
    bars: Sequence[ClosedBar], asof_index: int, *, lookback: int = 14
) -> CompressionFeature | None:
    if lookback < 2:
        raise ValueError("lookback must be >= 2")
    prefix = _closed_prefix(bars, asof_index)
    if len(prefix) < lookback + 1:
        return None
    trs: list[float] = []
    start = len(prefix) - lookback
    for idx in range(start, len(prefix)):
        trs.append(_true_range(prefix[idx], prefix[idx - 1].close))
    current_tr = trs[-1]
    mean_tr = fsum(trs[:-1]) / len(trs[:-1])
    if mean_tr <= 0:
        return None
    return CompressionFeature(
        true_range=current_tr,
        mean_true_range=mean_tr,
        tr_ratio=current_tr / mean_tr,
    )


def adx_feature(
    bars: Sequence[ClosedBar], asof_index: int, *, period: int = 14
) -> AdxFeature | None:
    """Return a causal Wilder-style ADX estimate using only closed bars <= asof."""
    if period < 2:
        raise ValueError("period must be >= 2")
    prefix = _closed_prefix(bars, asof_index)
    # Need period DM/TR observations to seed DI and another period DX values for ADX.
    if len(prefix) < (period * 2) + 1:
        return None

    trs: list[float] = []
    plus_dm: list[float] = []
    minus_dm: list[float] = []
    for idx in range(1, len(prefix)):
        current = prefix[idx]
        previous = prefix[idx - 1]
        up = current.high - previous.high
        down = previous.low - current.low
        plus_dm.append(up if up > down and up > 0 else 0.0)
        minus_dm.append(down if down > up and down > 0 else 0.0)
        trs.append(_true_range(current, previous.close))

    sm_tr = fsum(trs[:period])
    sm_plus = fsum(plus_dm[:period])
    sm_minus = fsum(minus_dm[:period])
    dx_values: list[float] = []
    last_plus_di = 0.0
    last_minus_di = 0.0

    for idx in range(period - 1, len(trs)):
        if idx >= period:
            sm_tr = sm_tr - (sm_tr / period) + trs[idx]
            sm_plus = sm_plus - (sm_plus / period) + plus_dm[idx]
            sm_minus = sm_minus - (sm_minus / period) + minus_dm[idx]
        if sm_tr <= 0:
            last_plus_di = last_minus_di = 0.0
            dx_values.append(0.0)
            continue
        last_plus_di = 100.0 * sm_plus / sm_tr
        last_minus_di = 100.0 * sm_minus / sm_tr
        denom = last_plus_di + last_minus_di
        dx_values.append(0.0 if denom <= 0 else 100.0 * abs(last_plus_di - last_minus_di) / denom)

    if len(dx_values) < period:
        return None
    adx = fsum(dx_values[:period]) / period
    for dx in dx_values[period:]:
        adx = ((adx * (period - 1)) + dx) / period
    return AdxFeature(adx=adx, plus_di=last_plus_di, minus_di=last_minus_di)


def retest_staleness(*, breakout_index: int, asof_index: int) -> int | None:
    """Closed-bar age of a confirmed breakout; never accepts a future/same-bar breakout."""
    if breakout_index < 0 or asof_index < 0:
        raise ValueError("indices must be non-negative")
    if breakout_index >= asof_index:
        return None
    return asof_index - breakout_index
