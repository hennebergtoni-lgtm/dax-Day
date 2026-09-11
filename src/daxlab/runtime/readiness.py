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
    mt5_readonly_health_verified: bool = False
    dataset_identity: RecoveryIdentity | None = None
    broker_economics_verified: bool = False
    broker_risk_sizing_verified: bool = False
    risk_profile_policy_verified: bool = False
    loss_cap_policy_verified: bool = False
    # Explicit operator STOP-GATE. Technical evidence alone must never unlock
    # broker-facing demo/PAPER execution.
    paper_user_authorized: bool = False


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
        if snapshot.dataset_identity is not RecoveryIdentity.HASH_VERIFIED:
            blockers.append("DATASET_IDENTITY_NOT_HASH_VERIFIED")

    # A clean-reference replay may use a recovered source whose normalized session
    # surface is HASH_VERIFIED against the frozen active-reference fingerprint.
    if kind is RunKind.PAPER and not snapshot.audited_bundle_available:
        blockers.append("AUDITED_BUNDLE_UNAVAILABLE")

    # A clean-reference replay produces this evidence; Paper consumes it.
    if kind is RunKind.PAPER and not snapshot.full_reference_replay_verified:
        blockers.append("FULL_REFERENCE_REPLAY_UNVERIFIED")

    if kind is RunKind.PAPER and not snapshot.execution_boundary_verified:
        blockers.append("EXECUTION_BOUNDARY_UNVERIFIED")

    # Paper must not be unlocked merely because execution code exists. The actual
    # broker-facing read-only observation path must first prove terminal/account/
    # symbol/data/clock/loop health under the fail-closed MT5 bridge.
    if kind is RunKind.PAPER and not snapshot.mt5_readonly_health_verified:
        blockers.append("MT5_READONLY_HEALTH_UNVERIFIED")

    # Broker-aware risk evidence is a separate prerequisite from host health and
    # from user authorization. Repository-only research code cannot satisfy these
    # booleans; they require separately verified broker/policy evidence.
    paper_risk_gates = (
        (snapshot.broker_economics_verified, "BROKER_ECONOMICS_UNVERIFIED"),
        (snapshot.broker_risk_sizing_verified, "BROKER_RISK_SIZING_UNVERIFIED"),
        (snapshot.risk_profile_policy_verified, "RISK_PROFILE_POLICY_UNVERIFIED"),
        (snapshot.loss_cap_policy_verified, "LOSS_CAP_POLICY_UNVERIFIED"),
    )
    if kind is RunKind.PAPER:
        for passed, blocker in paper_risk_gates:
            if not passed:
                blockers.append(blocker)

        # The project contract requires a user STOP-GATE review before broker-facing
        # demo/PAPER execution starts. Keep this independent from all technical gates
        # so a future software change cannot infer authorization from readiness.
        if not snapshot.paper_user_authorized:
            blockers.append("PAPER_USER_AUTHORIZATION_REQUIRED")

    return RunReadiness(kind=kind, allowed=not blockers, blockers=tuple(blockers))
