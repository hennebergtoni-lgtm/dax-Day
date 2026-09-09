"""Deterministic isolated-candidate metrics for V12 research.

This module evaluates already-produced trade outcomes. It does not select
thresholds, mutate V11.2, place orders, or promote research candidates.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Iterable


@dataclass(frozen=True, slots=True)
class IsolatedTradeOutcome:
    r: float
    period: str

    def __post_init__(self) -> None:
        if not isfinite(self.r):
            raise ValueError("trade R must be finite")
        if not self.period.strip():
            raise ValueError("period must be non-empty")


@dataclass(frozen=True, slots=True)
class IsolatedMetrics:
    trades: int
    return_r: float
    pf: float
    avg_r: float
    max_dd_r: float
    positive_periods: int
    negative_periods: int
    flat_periods: int
    period_returns: tuple[tuple[str, float], ...]


def evaluate_isolated_outcomes(outcomes: Iterable[IsolatedTradeOutcome]) -> IsolatedMetrics:
    items = tuple(outcomes)
    if not items:
        return IsolatedMetrics(0, 0.0, 0.0, 0.0, 0.0, 0, 0, 0, ())

    returns = [item.r for item in items]
    gross_profit = sum(value for value in returns if value > 0)
    gross_loss = -sum(value for value in returns if value < 0)
    if gross_loss > 0:
        pf = gross_profit / gross_loss
    elif gross_profit > 0:
        pf = 99.0
    else:
        pf = 0.0

    equity = 0.0
    peak = 0.0
    max_dd = 0.0
    period_map: dict[str, float] = {}
    for item in items:
        equity += item.r
        peak = max(peak, equity)
        max_dd = min(max_dd, equity - peak)
        period_map[item.period] = period_map.get(item.period, 0.0) + item.r

    ordered_periods = tuple(sorted(period_map.items()))
    positive = sum(value > 0 for _, value in ordered_periods)
    negative = sum(value < 0 for _, value in ordered_periods)
    flat = sum(value == 0 for _, value in ordered_periods)
    total = sum(returns)
    return IsolatedMetrics(
        trades=len(items),
        return_r=total,
        pf=pf,
        avg_r=total / len(items),
        max_dd_r=max_dd,
        positive_periods=positive,
        negative_periods=negative,
        flat_periods=flat,
        period_returns=ordered_periods,
    )
