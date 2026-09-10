"""Dated SHADOW outcome evidence linked to an existing deterministic DecisionRecord.

This module does not create decisions or orders. It attaches an observed finite R outcome
to an already-created SHADOW trade decision so time-based reporting can remain evidence-linked.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import timezone
import hashlib
import json
import math

from daxlab.runtime.decision import DecisionRecord, FinalAction


@dataclass(frozen=True, slots=True)
class DatedShadowOutcome:
    decision_id: str
    event_time_utc: str
    regime: str
    structure: str
    setup: str
    r_result: float
    outcome_sha256: str
    evidence_state: str = "SHADOW_OBSERVED_OUTCOME"
    simulated_only: bool = True
    broker_balance: bool = False
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def to_payload(self) -> dict[str, object]:
        return {
            "schema_version": "DAXLAB_DATED_SHADOW_OUTCOME_V1",
            "decision_id": self.decision_id,
            "event_time_utc": self.event_time_utc,
            "regime": self.regime,
            "structure": self.structure,
            "setup": self.setup,
            "r_result": self.r_result,
            "outcome_sha256": self.outcome_sha256,
            "evidence_state": self.evidence_state,
            "simulated_only": self.simulated_only,
            "broker_balance": self.broker_balance,
            "execution_capability": self.execution_capability,
            "order_execution_enabled": self.order_execution_enabled,
        }


def build_dated_shadow_outcome(
    decision: DecisionRecord,
    *,
    r_result: float,
) -> DatedShadowOutcome:
    """Attach an observed R result to one existing timezone-aware TRADE decision."""
    if decision.final_action is not FinalAction.TRADE:
        raise ValueError("dated SHADOW outcome requires an existing TRADE decision")
    if decision.event_time.tzinfo is None:
        raise ValueError("decision event_time must be timezone-aware")
    value = float(r_result)
    if not math.isfinite(value):
        raise ValueError("r_result must be finite")
    if not decision.decision_id.strip():
        raise ValueError("decision_id must be non-empty")

    event_time_utc = decision.event_time.astimezone(timezone.utc).isoformat()
    identity = {
        "schema_version": "DAXLAB_DATED_SHADOW_OUTCOME_V1",
        "decision_id": decision.decision_id,
        "event_time_utc": event_time_utc,
        "regime": decision.regime,
        "structure": decision.structure,
        "setup": decision.setup,
        "r_result": value,
        "evidence_state": "SHADOW_OBSERVED_OUTCOME",
        "simulated_only": True,
        "broker_balance": False,
        "execution_capability": "NONE",
        "order_execution_enabled": False,
    }
    digest = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return DatedShadowOutcome(
        decision_id=decision.decision_id,
        event_time_utc=event_time_utc,
        regime=decision.regime,
        structure=decision.structure,
        setup=decision.setup,
        r_result=value,
        outcome_sha256=digest,
    )
