"""Read-only operator models for filter visibility and system health."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from daxlab.research.filter_registry import FilterCapability


class HealthState(StrEnum):
    GREEN = "GREEN"
    AMBER = "AMBER"
    RED = "RED"


@dataclass(frozen=True, slots=True)
class FilterCard:
    key: str
    label: str
    evidence_status: str
    allowed_modes: tuple[str, ...]
    enabled: bool
    rationale: str
    provenance: str
    blocker: str | None


@dataclass(frozen=True, slots=True)
class ReferenceHealth:
    state: HealthState
    active_reference: str
    dataset_verified: bool
    engine_verified: bool
    database_verified: bool
    technical_replay_verified: bool
    full_reference_replay_verified: bool
    detailed_rows_imported: bool
    blockers: tuple[str, ...]


def filter_card(
    capability: FilterCapability,
    *,
    provenance: str,
    enabled: bool = False,
    blocker: str | None = None,
) -> FilterCard:
    if enabled and not capability.default_enabled:
        raise ValueError("operator read model cannot enable a filter outside registry state")
    return FilterCard(
        key=capability.key,
        label=capability.label,
        evidence_status=capability.evidence_status.value,
        allowed_modes=tuple(mode.value for mode in capability.allowed_modes),
        enabled=enabled,
        rationale=capability.rationale,
        provenance=provenance,
        blocker=blocker,
    )


def reference_health(
    *,
    active_reference: str,
    dataset_verified: bool,
    engine_verified: bool,
    database_verified: bool,
    technical_replay_verified: bool,
    full_reference_replay_verified: bool,
    detailed_rows_imported: bool,
) -> ReferenceHealth:
    blockers: list[str] = []
    critical = (
        (dataset_verified, "DATASET_UNVERIFIED"),
        (engine_verified, "ENGINE_UNVERIFIED"),
        (database_verified, "DATABASE_UNVERIFIED"),
        (technical_replay_verified, "TECHNICAL_REPLAY_UNVERIFIED"),
    )
    for passed, blocker in critical:
        if not passed:
            blockers.append(blocker)

    if blockers:
        state = HealthState.RED
    else:
        if not full_reference_replay_verified:
            blockers.append("FULL_REFERENCE_REPLAY_PENDING")
        if not detailed_rows_imported:
            blockers.append("DETAIL_ROWS_NOT_IMPORTED")
        state = HealthState.AMBER if blockers else HealthState.GREEN

    return ReferenceHealth(
        state=state,
        active_reference=active_reference,
        dataset_verified=dataset_verified,
        engine_verified=engine_verified,
        database_verified=database_verified,
        technical_replay_verified=technical_replay_verified,
        full_reference_replay_verified=full_reference_replay_verified,
        detailed_rows_imported=detailed_rows_imported,
        blockers=tuple(blockers),
    )
