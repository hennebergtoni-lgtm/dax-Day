"""Causal liquidity-sweep research primitives for LIQ001.

Research only. These helpers deliberately separate reference-level confirmation from
subsequent sweep detection and never backdate a level before its confirmation bar.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

import pandas as pd


class LevelKind(StrEnum):
    HIGH = "HIGH"
    LOW = "LOW"


@dataclass(frozen=True, slots=True)
class ConfirmedLevel:
    pivot_index: int
    pivot_time: pd.Timestamp
    confirmed_index: int
    confirmed_time: pd.Timestamp
    price: float
    kind: LevelKind


@dataclass(frozen=True, slots=True)
class SweepEvent:
    bar_index: int
    bar_time: pd.Timestamp
    level: ConfirmedLevel
    side: str
    overshoot_points: float
    close_reclaimed: bool


def confirmed_levels(frame: pd.DataFrame, *, half_window: int = 2) -> list[ConfirmedLevel]:
    """Return delayed, immutable swing levels.

    A pivot at index ``i`` is emitted only after bar ``i + half_window`` is present.
    This uses a centered structural definition but delays *knowledge* until the
    future-side confirmation bars have actually closed, preventing repainting.
    """
    if half_window < 1:
        raise ValueError("half_window must be >= 1")
    required = {"datetime", "high", "low"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"missing columns: {sorted(missing)}")
    if len(frame) < (2 * half_window + 1):
        return []

    out: list[ConfirmedLevel] = []
    highs = frame["high"].astype(float).to_numpy()
    lows = frame["low"].astype(float).to_numpy()
    times = pd.to_datetime(frame["datetime"], utc=True)

    for i in range(half_window, len(frame) - half_window):
        left = i - half_window
        right = i + half_window + 1
        hi = highs[left:right]
        lo = lows[left:right]
        confirm_i = i + half_window
        if highs[i] == hi.max() and (hi == highs[i]).sum() == 1:
            out.append(
                ConfirmedLevel(
                    pivot_index=i,
                    pivot_time=times.iloc[i],
                    confirmed_index=confirm_i,
                    confirmed_time=times.iloc[confirm_i],
                    price=float(highs[i]),
                    kind=LevelKind.HIGH,
                )
            )
        if lows[i] == lo.min() and (lo == lows[i]).sum() == 1:
            out.append(
                ConfirmedLevel(
                    pivot_index=i,
                    pivot_time=times.iloc[i],
                    confirmed_index=confirm_i,
                    confirmed_time=times.iloc[confirm_i],
                    price=float(lows[i]),
                    kind=LevelKind.LOW,
                )
            )
    return out


def wick_rejection_sweeps(frame: pd.DataFrame, levels: list[ConfirmedLevel]) -> list[SweepEvent]:
    """Detect LIQ001 Variant A only after the reference level was confirmed.

    High-side sweep: bar high exceeds a known HIGH level and closes back below it.
    Low-side sweep: bar low exceeds a known LOW level downward and closes back above it.
    The event becomes known only at the completed sweep bar.
    """
    required = {"datetime", "high", "low", "close"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"missing columns: {sorted(missing)}")

    times = pd.to_datetime(frame["datetime"], utc=True)
    out: list[SweepEvent] = []
    for i, row in frame.reset_index(drop=True).iterrows():
        bar_time = times.iloc[i]
        for level in levels:
            if level.confirmed_index >= i:
                continue
            if level.kind is LevelKind.HIGH:
                if float(row.high) > level.price and float(row.close) < level.price:
                    out.append(
                        SweepEvent(
                            bar_index=i,
                            bar_time=bar_time,
                            level=level,
                            side="HIGH_SIDE",
                            overshoot_points=float(row.high) - level.price,
                            close_reclaimed=True,
                        )
                    )
            else:
                if float(row.low) < level.price and float(row.close) > level.price:
                    out.append(
                        SweepEvent(
                            bar_index=i,
                            bar_time=bar_time,
                            level=level,
                            side="LOW_SIDE",
                            overshoot_points=level.price - float(row.low),
                            close_reclaimed=True,
                        )
                    )
    return out
