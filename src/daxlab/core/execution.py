"""Deterministic execution primitives.

Ambiguous OHLC bars must never be resolved using hindsight or distance-to-open heuristics.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Side(StrEnum):
    LONG = "long"
    SHORT = "short"


class ExitReason(StrEnum):
    STOP = "stop"
    TARGET = "target"
    NONE = "none"


@dataclass(frozen=True, slots=True)
class Bar:
    open: float
    high: float
    low: float
    close: float


@dataclass(frozen=True, slots=True)
class Bracket:
    stop: float
    target: float


def resolve_bracket_bar(bar: Bar, bracket: Bracket, side: Side) -> ExitReason:
    """Resolve stop/target touches conservatively.

    When both stop and target are touched inside the same OHLC bar, ordering is unknowable
    at this resolution. The frozen research policy therefore resolves STOP first. A future
    M1/tick resolver may replace ambiguity only when finer data proves the path.
    """
    if side is Side.LONG:
        stop_hit = bar.low <= bracket.stop
        target_hit = bar.high >= bracket.target
    else:
        stop_hit = bar.high >= bracket.stop
        target_hit = bar.low <= bracket.target

    if stop_hit:
        return ExitReason.STOP
    if target_hit:
        return ExitReason.TARGET
    return ExitReason.NONE
