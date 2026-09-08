"""Hard runtime safety gates shared by replay, shadow, paper and later live modes."""
from __future__ import annotations

from dataclasses import dataclass

from daxlab.runtime.contracts import UNSAFE_STATES, DataQualityState
from daxlab.runtime.decision import FinalAction


@dataclass(frozen=True, slots=True)
class RuntimeSafetySnapshot:
    data_quality: DataQualityState
    feed_connected: bool
    spread: float
    max_spread: float
    contradictory_state: bool = False

    def __post_init__(self) -> None:
        if self.spread < 0:
            raise ValueError("spread must be non-negative")
        if self.max_spread <= 0:
            raise ValueError("max_spread must be positive")


@dataclass(frozen=True, slots=True)
class SafetyGateResult:
    allowed: bool
    blockers: tuple[str, ...]

    def guard_action(self, requested: FinalAction) -> FinalAction:
        """Hard blockers always collapse the requested action to NO_TRADE."""
        if not self.allowed:
            return FinalAction.NO_TRADE
        return requested


def evaluate_runtime_safety(snapshot: RuntimeSafetySnapshot) -> SafetyGateResult:
    """Evaluate non-overridable data and execution safety conditions."""
    blockers: list[str] = []
    if snapshot.data_quality in UNSAFE_STATES:
        blockers.append("DATA_UNSAFE")
    if not snapshot.feed_connected:
        blockers.append("FEED_INTERRUPTION")
    if snapshot.spread > snapshot.max_spread:
        blockers.append("EXTREME_SPREAD")
    if snapshot.contradictory_state:
        blockers.append("CONTRADICTORY_STATE")
    return SafetyGateResult(allowed=not blockers, blockers=tuple(blockers))
