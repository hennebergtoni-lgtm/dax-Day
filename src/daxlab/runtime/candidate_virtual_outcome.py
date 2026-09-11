"""Costed SHADOW outcome bridge for the CAND-001 virtual lifecycle.

The lifecycle owns causal price progression. This module converts one CLOSED
virtual lifecycle into an evidence-linked R result and reuses the existing
DatedShadowOutcome contract. It creates no broker capability and does not
authorize PAPER or LIVE.

NEW_1X_COST_SEMANTICS V1:
- the virtual lifecycle's filled/exit prices represent the causal market-price path;
- configured spread, slippage and commission are modelled separately as additive
  adverse points once per completed virtual trade;
- R is normalized by the original planned risk distance
  abs(requested_price - stop_price), so later gaps/slippage affect achieved R
  without silently redefining the strategy's original risk unit.

This is an explicit DAX-BOT 1.x simulation contract, not a claim of V11.2 cost
formula parity. Broker-demo evidence may later calibrate the configured values
without changing strategy signal semantics.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from daxlab.core.execution import ExitReason
from daxlab.research.dated_shadow_outcome import DatedShadowOutcome, build_dated_shadow_outcome
from daxlab.runtime.candidate_virtual_lifecycle import (
    Cand001VirtualLifecycleState,
    VirtualPositionStatus,
)
from daxlab.runtime.decision import DecisionRecord, FinalAction, stable_fingerprint
from daxlab.runtime.paper_contracts import PaperFillModelConfig, Side

_SCHEMA_VERSION = "DAXLAB_CAND001_VIRTUAL_OUTCOME_V1"
_COST_SEMANTICS_VERSION = "DAXLAB_CAND001_COST_APPLICATION_V1"


@dataclass(frozen=True, slots=True)
class Cand001VirtualOutcomeEvidence:
    schema_version: str
    cost_semantics_version: str
    outcome_id: str
    lifecycle_id: str
    decision_id: str
    fill_model_fingerprint: str
    closed_at: datetime
    exit_reason: ExitReason
    side: Side
    filled_price: float
    exit_price: float
    planned_risk_points: float
    gross_points: float
    configured_cost_points: float
    gross_r: float
    cost_r: float
    net_r: float
    dated_outcome: DatedShadowOutcome
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported CAND-001 virtual outcome schema")
        if self.cost_semantics_version != _COST_SEMANTICS_VERSION:
            raise ValueError("unsupported CAND-001 cost semantics")
        if self.closed_at.tzinfo is None:
            raise ValueError("closed_at must be timezone-aware")
        if self.exit_reason is ExitReason.NONE:
            raise ValueError("virtual outcome requires a terminal exit reason")
        if self.planned_risk_points <= 0:
            raise ValueError("planned_risk_points must be positive")
        if self.configured_cost_points < 0:
            raise ValueError("configured_cost_points must be non-negative")
        if self.execution_capability != "NONE" or self.order_execution_enabled:
            raise ValueError("virtual outcome cannot authorize order execution")
        if self.dated_outcome.decision_id != self.decision_id:
            raise ValueError("dated outcome decision identity drift")
        if self.dated_outcome.r_result != self.net_r:
            raise ValueError("dated outcome must carry the costed net R result")


def build_cand001_virtual_outcome(
    *,
    decision: DecisionRecord,
    lifecycle: Cand001VirtualLifecycleState,
    fill_model: PaperFillModelConfig | None = None,
) -> Cand001VirtualOutcomeEvidence:
    """Convert one CLOSED SHADOW lifecycle into deterministic costed R evidence."""
    model = fill_model or PaperFillModelConfig()

    if decision.final_action is not FinalAction.TRADE:
        raise ValueError("CAND-001 virtual outcome requires a TRADE decision")
    if lifecycle.status is not VirtualPositionStatus.CLOSED:
        raise ValueError("CAND-001 virtual outcome requires a CLOSED lifecycle")
    if lifecycle.decision_id != decision.decision_id:
        raise ValueError("lifecycle decision_id does not match DecisionRecord")
    if lifecycle.fill_model_fingerprint != model.fingerprint:
        raise ValueError("fill-model fingerprint drift")
    if lifecycle.filled_price is None or lifecycle.exit_price is None or lifecycle.closed_at is None:
        raise ValueError("closed lifecycle is missing fill/exit evidence")
    if lifecycle.exit_reason is ExitReason.NONE:
        raise ValueError("closed lifecycle is missing exit reason")

    planned_risk_points = abs(lifecycle.requested_price - lifecycle.stop_price)
    if planned_risk_points <= 0:
        raise ValueError("planned risk distance must be positive")

    direction = 1.0 if lifecycle.side is Side.BUY else -1.0
    gross_points = (lifecycle.exit_price - lifecycle.filled_price) * direction
    configured_cost_points = (
        float(model.spread_points)
        + float(model.slippage_points)
        + float(model.commission_points)
    )
    gross_r = gross_points / planned_risk_points
    cost_r = configured_cost_points / planned_risk_points
    net_r = gross_r - cost_r

    dated = build_dated_shadow_outcome(decision, r_result=net_r)
    identity = {
        "schema_version": _SCHEMA_VERSION,
        "cost_semantics_version": _COST_SEMANTICS_VERSION,
        "lifecycle_id": lifecycle.lifecycle_id,
        "decision_id": decision.decision_id,
        "fill_model_fingerprint": model.fingerprint,
        "closed_at": lifecycle.closed_at.isoformat(),
        "exit_reason": lifecycle.exit_reason.value,
        "side": lifecycle.side.value,
        "filled_price": float(lifecycle.filled_price),
        "exit_price": float(lifecycle.exit_price),
        "planned_risk_points": float(planned_risk_points),
        "gross_points": float(gross_points),
        "configured_cost_points": float(configured_cost_points),
        "gross_r": float(gross_r),
        "cost_r": float(cost_r),
        "net_r": float(net_r),
        "dated_outcome_sha256": dated.outcome_sha256,
        "execution_capability": "NONE",
        "order_execution_enabled": False,
    }
    return Cand001VirtualOutcomeEvidence(
        schema_version=_SCHEMA_VERSION,
        cost_semantics_version=_COST_SEMANTICS_VERSION,
        outcome_id=stable_fingerprint(identity),
        lifecycle_id=lifecycle.lifecycle_id,
        decision_id=decision.decision_id,
        fill_model_fingerprint=model.fingerprint,
        closed_at=lifecycle.closed_at,
        exit_reason=lifecycle.exit_reason,
        side=lifecycle.side,
        filled_price=float(lifecycle.filled_price),
        exit_price=float(lifecycle.exit_price),
        planned_risk_points=float(planned_risk_points),
        gross_points=float(gross_points),
        configured_cost_points=float(configured_cost_points),
        gross_r=float(gross_r),
        cost_r=float(cost_r),
        net_r=float(net_r),
        dated_outcome=dated,
    )
