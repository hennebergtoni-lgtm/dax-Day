"""Replay boundary that enforces closed, safe candles before decisions."""
from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Generic, TypeVar

from daxlab.runtime.contracts import Candle

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class ReplayResult(Generic[T]):
    decisions: tuple[T, ...]
    blocked_candles: int


class ReplayEngine(Generic[T]):
    """Feed the same decision core deterministic closed-candle history."""

    def __init__(self, decision_core: Callable[[tuple[Candle, ...]], T]) -> None:
        self._decision_core = decision_core

    def run(self, candles: Iterable[Candle]) -> ReplayResult[T]:
        history: list[Candle] = []
        decisions: list[T] = []
        blocked = 0
        for candle in candles:
            if not candle.safe_for_decision:
                blocked += 1
                continue
            history.append(candle)
            decisions.append(self._decision_core(tuple(history)))
        return ReplayResult(tuple(decisions), blocked)


def assert_decision_parity(historical: Iterable[object], replay: Iterable[object]) -> None:
    left = tuple(historical)
    right = tuple(replay)
    if left != right:
        raise AssertionError(f"historical/replay decision mismatch: {left!r} != {right!r}")
