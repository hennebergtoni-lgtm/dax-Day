"""Causal completed-bar momentum primitives for MOM001 research only."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import isfinite
from typing import Sequence


@dataclass(frozen=True, slots=True)
class MomentumBar:
    time: datetime
    open: float
    high: float
    low: float
    close: float


@dataclass(frozen=True, slots=True)
class MomentumState:
    state_time: datetime
    return_1: float | None
    return_3: float | None
    directional_closes_3: int
    body_fraction: float
    range_points: float


def _validate_bar(bar: MomentumBar) -> None:
    values = (bar.open, bar.high, bar.low, bar.close)
    if not all(isfinite(value) for value in values):
        raise ValueError("non-finite momentum bar")
    if bar.high < max(bar.open, bar.close) or bar.low > min(bar.open, bar.close):
        raise ValueError("invalid OHLC momentum bar")
    if bar.high < bar.low:
        raise ValueError("invalid momentum range")


def completed_momentum_state(
    bars: Sequence[MomentumBar], *, entry_time: datetime
) -> MomentumState | None:
    """Return momentum state using only bars completed strictly before entry_time.

    `MomentumBar.time` is the time at which the bar is fully known. Therefore the
    entry bar itself is never eligible when its completion time is >= entry_time.
    """
    eligible = [bar for bar in bars if bar.time < entry_time]
    if not eligible:
        return None
    for bar in eligible:
        _validate_bar(bar)
    eligible = sorted(eligible, key=lambda bar: bar.time)
    latest = eligible[-1]

    def horizon_return(periods: int) -> float | None:
        if len(eligible) <= periods:
            return None
        base = eligible[-1 - periods].close
        if base == 0:
            return None
        return latest.close / base - 1.0

    tail = eligible[-3:]
    signs = [1 if bar.close > bar.open else -1 if bar.close < bar.open else 0 for bar in tail]
    directional = 0
    if len(signs) == 3 and all(sign > 0 for sign in signs):
        directional = 3
    elif len(signs) == 3 and all(sign < 0 for sign in signs):
        directional = -3

    range_points = latest.high - latest.low
    body_fraction = 0.0 if range_points == 0 else abs(latest.close - latest.open) / range_points
    return MomentumState(
        state_time=latest.time,
        return_1=horizon_return(1),
        return_3=horizon_return(3),
        directional_closes_3=directional,
        body_fraction=body_fraction,
        range_points=range_points,
    )
