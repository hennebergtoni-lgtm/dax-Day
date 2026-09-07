"""Deterministic day-based walk-forward scheduling."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, TypeVar

from daxlab.contracts import WalkForwardSpec

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class WalkForwardWindow:
    number: int
    train: tuple[object, ...]
    oos: tuple[object, ...]


def build_walk_forwards(days: Sequence[T], spec: WalkForwardSpec) -> list[WalkForwardWindow]:
    """Build rolling train/OOS windows without overlap leakage between each pair."""
    windows: list[WalkForwardWindow] = []
    start = 0
    number = 1
    required = spec.train_days + spec.oos_days

    while start + required <= len(days):
        split = start + spec.train_days
        end = split + spec.oos_days
        windows.append(
            WalkForwardWindow(
                number=number,
                train=tuple(days[start:split]),
                oos=tuple(days[split:end]),
            )
        )
        start += spec.step_days
        number += 1

    return windows
