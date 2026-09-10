"""Cross-cycle integrity checks for validated MT5 closed-M5 feeds.

This module is observation-only. It compares two already validated closed-M5
snapshots and detects history rewrites or time regressions across polling cycles.
It has no broker dependency and no execution capability.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from daxlab.runtime.mt5_feed_payload import ClosedM5Feed
from daxlab.runtime.mt5_readonly import Mt5Bar


@dataclass(frozen=True, slots=True)
class CrossCycleIntegrityResult:
    status: str
    blockers: tuple[str, ...]
    overlapping_bars: int
    identical_overlaps: int
    mutated_overlaps: int
    latest_previous_open_time: datetime
    latest_current_open_time: datetime
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False


def evaluate_cross_cycle_integrity(
    previous: ClosedM5Feed,
    current: ClosedM5Feed,
) -> CrossCycleIntegrityResult:
    """Fail closed on historical bar mutation or latest-time regression.

    The function intentionally does not classify large time gaps as acceptable or
    unacceptable; broker-session knowledge is required for that separate gate.
    """
    if previous.requested_start_pos != current.requested_start_pos:
        raise ValueError("cross-cycle requested_start_pos mismatch")
    if not previous.bars or not current.bars:
        raise ValueError("cross-cycle feeds must contain bars")

    previous_by_time = _bars_by_time(previous.bars)
    current_by_time = _bars_by_time(current.bars)

    overlapping_times = sorted(previous_by_time.keys() & current_by_time.keys())
    identical = 0
    mutated = 0
    blockers: list[str] = []

    for open_time in overlapping_times:
        if previous_by_time[open_time] == current_by_time[open_time]:
            identical += 1
        else:
            mutated += 1

    if mutated:
        blockers.append("HISTORICAL_BAR_MUTATION")

    latest_previous = previous.bars[-1].open_time
    latest_current = current.bars[-1].open_time
    if latest_current < latest_previous:
        blockers.append("LATEST_BAR_TIME_REGRESSION")

    return CrossCycleIntegrityResult(
        status="GREEN" if not blockers else "BLOCKED",
        blockers=tuple(blockers),
        overlapping_bars=len(overlapping_times),
        identical_overlaps=identical,
        mutated_overlaps=mutated,
        latest_previous_open_time=latest_previous,
        latest_current_open_time=latest_current,
    )


def _bars_by_time(bars: Iterable[Mt5Bar]) -> dict[datetime, Mt5Bar]:
    result: dict[datetime, Mt5Bar] = {}
    for bar in bars:
        if bar.open_time in result:
            raise ValueError("duplicate bar open_time in cross-cycle input")
        result[bar.open_time] = bar
    return result
