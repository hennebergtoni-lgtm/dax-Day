"""Operator-facing system health aggregation without trading-rule mutation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class HealthState(StrEnum):
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    RED = "RED"


@dataclass(frozen=True, slots=True)
class SystemHealth:
    data: HealthState
    reference: HealthState
    replay: HealthState
    database: HealthState
    execution: HealthState
    blockers: tuple[str, ...]

    @property
    def overall(self) -> HealthState:
        states = (self.data, self.reference, self.replay, self.database, self.execution)
        if HealthState.RED in states or self.blockers:
            return HealthState.RED
        if HealthState.YELLOW in states:
            return HealthState.YELLOW
        return HealthState.GREEN

    @property
    def trading_allowed(self) -> bool:
        return self.overall is HealthState.GREEN


def build_system_health(
    *,
    data: HealthState,
    reference: HealthState,
    replay: HealthState,
    database: HealthState,
    execution: HealthState,
    blockers: tuple[str, ...] = (),
) -> SystemHealth:
    """Build a visible health summary; callers remain responsible for hard gates."""
    return SystemHealth(
        data=data,
        reference=reference,
        replay=replay,
        database=database,
        execution=execution,
        blockers=tuple(sorted(set(blockers))),
    )
