"""Run-readiness gates for visible research/replay execution surfaces."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from daxlab.data.recovery import RecoveryIdentity


class RunKind(StrEnum):
    FIXTURE_REPLAY_SMOKE = "FIXTURE_REPLAY_SMOKE"
    CLEAN_REFERENCE_REPLAY = "CLEAN_REFERENCE_REPLAY"
    PAPER = "PAPER"


@dataclass(frozen=True, slots=True)
class ReadinessSnapshot:
    ci_green: bool
    dataset_verified: bool
    engine_verified: bool
    database_verified: bool
    technical_replay_verified: bool
    audited_bundle_available: bool
    full_reference_replay_verified: bool
    execution_boundary_verified: bool = False
    dataset_identity: RecoveryIdentity | None = None


@dataclass(frozen=True, slots=True)
class RunReadiness:
    kind: RunKind
    allowed: bool
    blockers: tuple[str, ...]


def evaluate_run_readiness(kind: RunKind, snapshot: ReadinessSnapshot) -> RunReadiness:
    blockers: list[str] = []
    common = (
        (snapshot.ci_green, "CI_NOT_GREEN"),
        (snapshot.engine_verified, "ENGINE_UNVERIFIED"),
        (snapshot.database_verified, "DATABASE_UNVERIFIED"),
        (snapshot.technical_replay_verified, "TECHNICAL_REPLAY_UNVERIFIED"),
    )
    for passed, blocker in common:
        if not passed:
            blockers.append(blocker)

    if kind in (RunKind.CLEAN_REFERENCE_REPLAY, RunKind.PAPER):
        if not snapshot.dataset_verified:
            blockers.append("DATASET_UNVERIFIED")
        if snapshot.dataset_identity is not None and (
            snapshot.dataset_identity is not RecoveryIdentity.HASH_VERIFIED
        ):
            blockers.append("DATASET_IDENTITY_NOT_HASH_VERIFIED")
        if not snapshot.audited_bundle_available:
            blockers.append("AUDITED_BUNDLE_UNAVAILABLE")
        if not snapshot.full_reference_replay_verified:
            blockers.append("FULL_REFERENCE_REPLAY_UNVERIFIED")

    if kind is RunKind.PAPER and not snapshot.execution_boundary_verified:
        blockers.append("EXECUTION_BOUNDARY_UNVERIFIED")

    return RunReadiness(kind=kind, allowed=not blockers, blockers=tuple(blockers))
