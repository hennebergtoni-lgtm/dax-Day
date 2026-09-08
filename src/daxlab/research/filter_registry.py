from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum


class EvidenceStatus(str, Enum):
    RESEARCH = "research"
    VALIDATED = "validated"
    DEPLOYABLE = "deployable"


class ControlMode(str, Enum):
    VISIBLE_ONLY = "visible_only"
    MANUAL = "manual"
    REGIME_AUTOMATIC = "regime_automatic"


@dataclass(frozen=True)
class FilterCapability:
    key: str
    label: str
    evidence_status: EvidenceStatus
    allowed_modes: tuple[ControlMode, ...]
    default_enabled: bool = False
    rationale: str = ""

    def can_use(self, mode: ControlMode) -> bool:
        return mode in self.allowed_modes


class FilterRegistry:
    def __init__(self, capabilities: Iterable[FilterCapability] = ()) -> None:
        self._items: dict[str, FilterCapability] = {}
        for capability in capabilities:
            self.register(capability)

    def register(self, capability: FilterCapability) -> None:
        if capability.key in self._items:
            raise ValueError(f"duplicate filter capability: {capability.key}")
        if capability.evidence_status is EvidenceStatus.RESEARCH and (
            ControlMode.MANUAL in capability.allowed_modes
            or ControlMode.REGIME_AUTOMATIC in capability.allowed_modes
        ):
            raise ValueError("research filters may not be live-switchable")
        if capability.evidence_status is EvidenceStatus.VALIDATED and (
            ControlMode.REGIME_AUTOMATIC in capability.allowed_modes
        ):
            raise ValueError("validated filters need explicit deployable promotion before auto mode")
        self._items[capability.key] = capability

    def get(self, key: str) -> FilterCapability:
        return self._items[key]

    def all(self) -> tuple[FilterCapability, ...]:
        return tuple(self._items.values())

    def eligible_for(self, mode: ControlMode) -> tuple[FilterCapability, ...]:
        return tuple(item for item in self._items.values() if item.can_use(mode))


def default_research_registry() -> FilterRegistry:
    """Registry reflecting current evidence, not future promotion intent."""
    return FilterRegistry(
        [
            FilterCapability(
                key="bb001",
                label="Bollinger quality/regime filter",
                evidence_status=EvidenceStatus.RESEARCH,
                allowed_modes=(ControlMode.VISIBLE_ONLY,),
                rationale="Causal research tool; promising interactions but not promotion-eligible.",
            ),
            FilterCapability(
                key="fib001",
                label="Causal Fibonacci retracement context",
                evidence_status=EvidenceStatus.RESEARCH,
                allowed_modes=(ControlMode.VISIBLE_ONLY,),
                rationale="Fixed retracement zones from causally known impulses; isolated research only.",
            ),
            FilterCapability(
                key="gap001",
                label="Opening-gap context",
                evidence_status=EvidenceStatus.RESEARCH,
                allowed_modes=(ControlMode.VISIBLE_ONLY,),
                rationale="Opening-gap feature family; no gap-fill assumption or live eligibility.",
            ),
            FilterCapability(
                key="prev_range_atr",
                label="Prior-day extension context",
                evidence_status=EvidenceStatus.RESEARCH,
                allowed_modes=(ControlMode.VISIBLE_ONLY,),
                rationale="Train-derived hypothesis; requires independent/prospective validation.",
            ),
        ]
    )
