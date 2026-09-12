"""CAND-001 adapter into the existing forward SHADOW performance contract.

Only real directional breakout signals become performance observations. Ordinary
processed bars such as OR building, OR ready, outside-session or no-breakout do
not inflate generated-signal counts.
"""
from __future__ import annotations

from daxlab.research.forward_shadow_performance import (
    ALLOWED,
    BLOCKED,
    ShadowSignalObservation,
)
from daxlab.runtime.candidate_admission import AdmissionStatus, Cand001AdmissionResult
from daxlab.runtime.candidate_signal import Cand001Signal, SignalDirection
from daxlab.runtime.candidate_virtual_outcome import Cand001VirtualOutcomeEvidence
from daxlab.runtime.decision import DecisionRecord, FinalAction


def build_cand001_forward_observation(
    *,
    signal: Cand001Signal,
    admission: Cand001AdmissionResult,
    decision: DecisionRecord,
    outcome: Cand001VirtualOutcomeEvidence | None = None,
) -> ShadowSignalObservation | None:
    """Return one terminal signal observation, or None for a non-signal bar."""
    directional = signal.direction in {SignalDirection.LONG, SignalDirection.SHORT}
    if not directional:
        if admission.status is not AdmissionStatus.NO_SIGNAL:
            raise ValueError("non-directional signal requires NO_SIGNAL admission")
        if decision.final_action is not FinalAction.NO_TRADE:
            raise ValueError("non-directional signal cannot produce TRADE decision")
        if outcome is not None:
            raise ValueError("non-directional signal cannot carry an outcome")
        return None

    if decision.data_fingerprint != signal.data_fingerprint:
        raise ValueError("signal/decision provenance drift")

    if admission.status is AdmissionStatus.ALLOWED:
        if decision.final_action is not FinalAction.TRADE:
            raise ValueError("ALLOWED admission requires TRADE decision")
        if outcome is None:
            raise ValueError("ALLOWED signal requires a closed virtual outcome")
        if outcome.decision_id != decision.decision_id:
            raise ValueError("outcome decision identity drift")
        return ShadowSignalObservation(
            signal_id=decision.decision_id,
            status=ALLOWED,
            r_result=outcome.net_r,
        )

    if admission.status is AdmissionStatus.SESSION_LIMIT:
        if decision.final_action is not FinalAction.NO_TRADE:
            raise ValueError("SESSION_LIMIT admission requires NO_TRADE decision")
        if outcome is not None:
            raise ValueError("blocked signal cannot carry an outcome")
        if "SESSION_TRADE_LIMIT" not in decision.blockers:
            raise ValueError("SESSION_LIMIT decision must expose SESSION_TRADE_LIMIT blocker")
        return ShadowSignalObservation(
            signal_id=decision.decision_id,
            status=BLOCKED,
            block_reason="SESSION_TRADE_LIMIT",
        )

    raise ValueError("directional signal requires ALLOWED or SESSION_LIMIT admission")
