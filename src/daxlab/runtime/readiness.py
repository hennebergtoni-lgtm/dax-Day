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
    # Legacy coarse execution-boundary evidence. Retained for compatibility, but
    # it is deliberately insufficient to unlock PAPER by itself.
    execution_boundary_verified: bool = False
    mt5_readonly_health_verified: bool = False
    dataset_identity: RecoveryIdentity | None = None
    broker_economics_verified: bool = False
    broker_risk_sizing_verified: bool = False
    risk_profile_policy_verified: bool = False
    loss_cap_policy_verified: bool = False
    # Explicit broker-facing PAPER evidence. Contracts/vocabulary or SHADOW-only
    # simulation do not satisfy these booleans.
    broker_order_lifecycle_verified: bool = False
    broker_execution_checkpoint_verified: bool = False
    broker_reconciliation_verified: bool = False
    execution_protection_gates_verified: bool = False
    broker_order_telemetry_verified: bool = False
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

    # Keep the historical coarse gate for compatibility/provenance, but make it
    # impossible for one boolean to stand in for the broker lifecycle, restart
    # checkpoint, reconnect reconciliation, execution-protection and telemetry
    # evidence required for PAPER.
    if kind is RunKind.PAPER and not snapshot.execution_boundary_verified:
        blockers.append("EXECUTION_BOUNDARY_UNVERIFIED")

    if kind is RunKind.PAPER:
        paper_execution_gates = (
            (
                snapshot.broker_order_lifecycle_verified,
                "BROKER_ORDER_LIFECYCLE_UNVERIFIED",
            ),
            (
                snapshot.broker_execution_checkpoint_verified,
                "BROKER_EXECUTION_CHECKPOINT_UNVERIFIED",
            ),
            (
                snapshot.broker_reconciliation_verified,
                "BROKER_RECONCILIATION_UNVERIFIED",
            ),
            (
                snapshot.execution_protection_gates_verified,
                "EXECUTION_PROTECTION_GATES_UNVERIFIED",
            ),
            (
                snapshot.broker_order_telemetry_verified,
                "BROKER_ORDER_TELEMETRY_UNVERIFIED",
            ),
        )
        for passed, blocker in paper_execution_gates:
            if not passed:
                blockers.append(blocker)

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


def project_partial_evidence(*, gate_id: int, gate_contract_version: str,
                             composite_status: str, required_dimensions: tuple[str, ...],
                             observations: tuple, expected, now: str,
                             required_scope: str, historical_claims: tuple = ()) -> dict:
    """Read-only dimension projection; NEVER writes/promotes the owning gate.

    The current 27-gate closeout remains authoritative. Observations are tuples
    (dimension_id, status, provenance). Conflicts veto reuse, not erase history.
    The trusted caller owns the closed required catalog and source attribution.
    """
    from daxlab.research.turbo_contract import SCOPES, count, tokens, token
    from dataclasses import asdict
    count(gate_id, 1, 27)
    token(gate_contract_version)
    tokens(required_dimensions, required=True)
    statuses = {'VERIFIED', 'IMPLEMENTED', 'WAITING_EXTERNAL', 'BLOCKED', 'UNKNOWN'}
    if composite_status not in statuses or required_scope not in SCOPES:
        raise ValueError('PARTIAL_GATE_CONTRACT')
    if type(observations) is not tuple or len(observations) > 512:
        raise ValueError('PARTIAL_GATE_OBSERVATIONS')
    from daxlab.research.turbo_contract import HistoricalClaim
    if type(historical_claims) is not tuple or len(historical_claims) > 256:
        raise ValueError('PARTIAL_GATE_HISTORICAL_BOUND')
    for claim in historical_claims:
        if type(claim) is not HistoricalClaim or claim.dimension_id not in required_dimensions:
            raise ValueError('PARTIAL_GATE_HISTORICAL_SCHEMA')
        claim.__post_init__()
    grouped = {name: [] for name in required_dimensions}
    for name, status, provenance in observations:
        if name not in grouped or status not in statuses:
            raise ValueError('PARTIAL_GATE_UNKNOWN_DIMENSION')
        grouped[name].append((status, provenance))
    rows = []
    for name, values in grouped.items():
        matching = [(s, p) for s, p in values if p.matches(
            expected, now=now, scopes=(required_scope,))]
        states = {s for s, _ in matching}
        state = ('BLOCKED' if 'BLOCKED' in states or len(states) > 1 else
                 next(iter(states)) if states else 'UNKNOWN')
        from daxlab.research.turbo_contract import read_utc
        relevant_history = [c for c in historical_claims if c.dimension_id == name
                            and c.evidence_scope == required_scope
                            and c.evidence_head == expected.evidence_head
                            and c.observed_date <= read_utc(now).date().isoformat()]
        rows.append({'dimension_id': name, 'status': state,
                     'gate_id': gate_id, 'gate_contract_version': gate_contract_version,
                     'evidence_scope': required_scope if matching else None,
                     'evidence_refs': sorted({ref for _, p in matching for ref in p.evidence_refs}),
                     'provenance_refs': sorted({p.fingerprint for _, p in values}),
                     'observations': [{'status': s, **asdict(p)} for s, p in values],
                     'historical_truth_status': 'VERIFIED' if relevant_history else None,
                     'historical_claims': [asdict(c) for c in historical_claims if c.dimension_id == name],
                     'historical_claims_authorize_current_reuse': False,
                     'reusable': state == 'VERIFIED'})
    gaps = [r['dimension_id'] for r in rows if not r['reusable']]
    # Investigate the unproved structural contract first. Historical acquisition
    # success remains useful; rereading it does not fill missing native economics.
    prioritized = [r['dimension_id'] for r in rows if not r['reusable'] and not r['historical_truth_status']]
    prioritized += [r['dimension_id'] for r in rows if not r['reusable'] and r['historical_truth_status']]
    return {'gate_id': gate_id, 'gate_contract_version': gate_contract_version,
            'composite_status': composite_status, 'dimensions': rows,
            'remaining_gaps': gaps, 'next_smallest_gap': prioritized[0] if prioritized else None,
            'composite_reassessment_required': not gaps and composite_status != 'VERIFIED',
            'execution_capability': 'NONE', 'order_execution_enabled': False}
