"""Causal market-structure research primitives for STRUCT001.

The module reuses LIQ001 confirmed levels so swing timing has one canonical research
implementation. Structure labels are emitted only from already-confirmed levels.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

import pandas as pd

from daxlab.research.liquidity_sweep import ConfirmedLevel, LevelKind


class StructureLabel(StrEnum):
    HH = "HH"
    LH = "LH"
    HL = "HL"
    LL = "LL"


@dataclass(frozen=True, slots=True)
class LabeledStructurePoint:
    level: ConfirmedLevel
    label: StructureLabel | None


@dataclass(frozen=True, slots=True)
class BreakOfStructure:
    bar_index: int
    bar_time: pd.Timestamp
    direction: str
    reference: ConfirmedLevel
    close: float


def label_structure(levels: list[ConfirmedLevel]) -> list[LabeledStructurePoint]:
    """Label confirmed highs/lows relative to the previous confirmed level of same kind."""
    previous: dict[LevelKind, ConfirmedLevel] = {}
    out: list[LabeledStructurePoint] = []
    for level in sorted(levels, key=lambda item: (item.confirmed_index, item.pivot_index)):
        prior = previous.get(level.kind)
        label: StructureLabel | None = None
        if prior is not None:
            if level.kind is LevelKind.HIGH:
                label = StructureLabel.HH if level.price > prior.price else StructureLabel.LH
            else:
                label = StructureLabel.LL if level.price < prior.price else StructureLabel.HL
        out.append(LabeledStructurePoint(level=level, label=label))
        previous[level.kind] = level
    return out


def close_breaks(frame: pd.DataFrame, levels: list[ConfirmedLevel]) -> list[BreakOfStructure]:
    """Emit first completed-close break of each confirmed reference level.

    A level cannot be broken before it was confirmed, and each level emits at most one
    BOS event. This is descriptive research state, not an entry rule.
    """
    required = {"datetime", "close"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"missing columns: {sorted(missing)}")
    times = pd.to_datetime(frame["datetime"], utc=True)
    closes = frame["close"].astype(float).to_numpy()
    out: list[BreakOfStructure] = []
    broken: set[tuple[int, str]] = set()
    ordered = sorted(levels, key=lambda item: (item.confirmed_index, item.pivot_index))
    for i, close in enumerate(closes):
        for level in ordered:
            key = (level.pivot_index, level.kind.value)
            if key in broken or level.confirmed_index >= i:
                continue
            if level.kind is LevelKind.HIGH and close > level.price:
                out.append(
                    BreakOfStructure(
                        bar_index=i,
                        bar_time=times.iloc[i],
                        direction="UP",
                        reference=level,
                        close=float(close),
                    )
                )
                broken.add(key)
            elif level.kind is LevelKind.LOW and close < level.price:
                out.append(
                    BreakOfStructure(
                        bar_index=i,
                        bar_time=times.iloc[i],
                        direction="DOWN",
                        reference=level,
                        close=float(close),
                    )
                )
                broken.add(key)
    return out
