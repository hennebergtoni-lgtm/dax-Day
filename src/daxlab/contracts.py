"""Stable contracts shared by the bot, data layer and research lab."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum


class ResearchStatus(StrEnum):
    IDEA = "IDEA"
    RESEARCH = "RESEARCH"
    PILOT = "PILOT"
    VALIDATED_TOOL = "VALIDATED TOOL"
    COMBINATION_TEST = "COMBINATION TEST"
    CANDIDATE_BOT = "CANDIDATE BOT"
    WF_OOS = "WF/OOS"
    NEW_BOT_VERSION = "NEW BOT VERSION"


@dataclass(frozen=True, slots=True)
class CostModel:
    name: str
    multiplier: float = 1.0

    def __post_init__(self) -> None:
        if self.multiplier <= 0:
            raise ValueError("cost multiplier must be positive")


@dataclass(frozen=True, slots=True)
class WalkForwardSpec:
    train_days: int = 45
    oos_days: int = 20
    step_days: int = 20

    def __post_init__(self) -> None:
        if min(self.train_days, self.oos_days, self.step_days) <= 0:
            raise ValueError("walk-forward lengths must be positive")


@dataclass(frozen=True, slots=True)
class ExperimentManifest:
    experiment_id: str
    hypothesis: str
    status: ResearchStatus
    baseline: str
    parameters: Mapping[str, object]
    data_fingerprint: str
    engine_fingerprint: str

    def __post_init__(self) -> None:
        if not self.experiment_id.strip():
            raise ValueError("experiment_id is required")
        if not self.hypothesis.strip():
            raise ValueError("hypothesis is required")
        if not self.data_fingerprint.strip() or not self.engine_fingerprint.strip():
            raise ValueError("data and engine fingerprints are required")


REFERENCE_WF = WalkForwardSpec(45, 20, 20)
REFERENCE_COSTS = (
    CostModel("normal", 1.0),
    CostModel("stress_1.5x", 1.5),
    CostModel("stress_2x", 2.0),
)
