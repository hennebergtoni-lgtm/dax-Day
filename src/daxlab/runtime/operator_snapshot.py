"""Credential-free read-only operator snapshot for DAX-BOT 1.x."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from daxlab.runtime.candidate_admission import AdmissionStatus, Cand001AdmissionResult
from daxlab.runtime.candidate_config import Cand001Config
from daxlab.runtime.candidate_signal import Cand001Signal
from daxlab.runtime.candidate_trade_plan import Cand001TradePlan
from daxlab.runtime.candidate_virtual_lifecycle import (
    Cand001VirtualLifecycleState,
    VirtualPositionStatus,
)
from daxlab.runtime.candidate_virtual_outcome import Cand001VirtualOutcomeEvidence
from daxlab.runtime.decision import DecisionRecord, FinalAction, stable_fingerprint


SCHEMA_VERSION = "DAX_BOT_OPERATOR_SNAPSHOT_V2"


@dataclass(frozen=True, slots=True)
class OperatorSnapshot:
    schema_version: str
    generated_at: datetime
    core_version: str
    candidate_id: str
    config_fingerprint: str
    signal_direction: str
    signal_reason: str
    admission_status: str
    decision_action: str
    decision_id: str
    blockers: tuple[str, ...]
    risk_result: str
    proposed_entry: float | None
    proposed_stop: float | None
    proposed_target: float | None
    proposed_reward_risk: float | None
    virtual_lifecycle_id: str | None
    virtual_status: str | None
    virtual_side: str | None
    virtual_filled_at: datetime | None
    virtual_filled_price: float | None
    virtual_closed_at: datetime | None
    virtual_exit_price: float | None
    virtual_exit_reason: str | None
    outcome_id: str | None
    outcome_gross_r: float | None
    outcome_cost_r: float | None
    outcome_net_r: float | None
    execution_capability: str
    order_execution_enabled: bool
    snapshot_fingerprint: str

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError("operator snapshot schema mismatch")
        if self.generated_at.tzinfo is None:
            raise ValueError("generated_at must be timezone-aware")
        for value in (self.virtual_filled_at, self.virtual_closed_at):
            if value is not None and value.tzinfo is None:
                raise ValueError("virtual lifecycle timestamps must be timezone-aware")
        if self.execution_capability != "NONE":
            raise ValueError("operator snapshot cannot carry execution capability")
        if self.order_execution_enabled is not False:
            raise ValueError("operator snapshot cannot enable order execution")
        if len(self.config_fingerprint) != 64 or len(self.decision_id) != 64:
            raise ValueError("operator snapshot identity fingerprints must be sha256 hex")
        int(self.config_fingerprint, 16)
        int(self.decision_id, 16)
        if self.virtual_lifecycle_id is not None:
            if len(self.virtual_lifecycle_id) != 64:
                raise ValueError("virtual_lifecycle_id must be sha256 hex")
            int(self.virtual_lifecycle_id, 16)
        if self.outcome_id is not None:
            if len(self.outcome_id) != 64:
                raise ValueError("outcome_id must be sha256 hex")
            int(self.outcome_id, 16)
        if len(self.snapshot_fingerprint) != 64:
            raise ValueError("snapshot_fingerprint must be sha256 hex")
        int(self.snapshot_fingerprint, 16)

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at.isoformat(),
            "core_version": self.core_version,
            "candidate_id": self.candidate_id,
            "config_fingerprint": self.config_fingerprint,
            "signal": {
                "direction": self.signal_direction,
                "reason": self.signal_reason,
            },
            "admission": {"status": self.admission_status},
            "decision": {
                "action": self.decision_action,
                "decision_id": self.decision_id,
                "blockers": list(self.blockers),
                "risk_result": self.risk_result,
            },
            "trade_plan": {
                "entry": self.proposed_entry,
                "stop": self.proposed_stop,
                "target": self.proposed_target,
                "reward_risk": self.proposed_reward_risk,
            },
            "virtual_position": {
                "lifecycle_id": self.virtual_lifecycle_id,
                "status": self.virtual_status,
                "side": self.virtual_side,
                "filled_at": (
                    self.virtual_filled_at.isoformat()
                    if self.virtual_filled_at is not None
                    else None
                ),
                "filled_price": self.virtual_filled_price,
                "closed_at": (
                    self.virtual_closed_at.isoformat()
                    if self.virtual_closed_at is not None
                    else None
                ),
                "exit_price": self.virtual_exit_price,
                "exit_reason": self.virtual_exit_reason,
            },
            "outcome": {
                "outcome_id": self.outcome_id,
                "gross_r": self.outcome_gross_r,
                "cost_r": self.outcome_cost_r,
                "net_r": self.outcome_net_r,
            },
            "safety": {
                "execution_capability": self.execution_capability,
                "order_execution_enabled": self.order_execution_enabled,
            },
            "snapshot_fingerprint": self.snapshot_fingerprint,
        }


def build_operator_snapshot(
    *,
    generated_at: datetime,
    config: Cand001Config,
    signal: Cand001Signal,
    proposed_trade_plan: Cand001TradePlan | None,
    admission: Cand001AdmissionResult,
    decision: DecisionRecord,
    lifecycle: Cand001VirtualLifecycleState | None = None,
    outcome: Cand001VirtualOutcomeEvidence | None = None,
) -> OperatorSnapshot:
    """Build a read-only consistency-checked view for operators and the web layer."""
    if generated_at.tzinfo is None:
        raise ValueError("generated_at must be timezone-aware")
    identity = config.product_identity()
    if decision.event_time != signal.close_time:
        raise ValueError("decision time must match closed signal time")
    if decision.data_fingerprint != signal.data_fingerprint:
        raise ValueError("decision provenance must match signal data fingerprint")
    if admission.status is AdmissionStatus.ALLOWED:
        if admission.admitted_plan is None or decision.final_action is not FinalAction.TRADE:
            raise ValueError("ALLOWED admission must map to TRADE decision")
    elif decision.final_action is FinalAction.TRADE:
        raise ValueError("non-ALLOWED admission cannot map to TRADE decision")
    if proposed_trade_plan is not None:
        if proposed_trade_plan.signal_data_fingerprint != signal.data_fingerprint:
            raise ValueError("proposed trade-plan provenance mismatch")
        entry = proposed_trade_plan.entry_price
        stop = proposed_trade_plan.stop_price
        target = proposed_trade_plan.target_price
        reward_risk = proposed_trade_plan.reward_risk
    else:
        entry = stop = target = reward_risk = None

    lifecycle_fields = _lifecycle_fields(
        generated_at=generated_at,
        decision=decision,
        lifecycle=lifecycle,
    )
    outcome_fields = _outcome_fields(
        generated_at=generated_at,
        decision=decision,
        lifecycle=lifecycle,
        outcome=outcome,
    )

    payload = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "core_version": identity.core_version,
        "candidate_id": identity.candidate_id,
        "config_fingerprint": identity.config_fingerprint,
        "signal_direction": signal.direction.value,
        "signal_reason": signal.reason.value,
        "admission_status": admission.status.value,
        "decision_action": decision.final_action.value,
        "decision_id": decision.decision_id,
        "blockers": decision.blockers,
        "risk_result": decision.risk_result,
        "proposed_entry": entry,
        "proposed_stop": stop,
        "proposed_target": target,
        "proposed_reward_risk": reward_risk,
        **lifecycle_fields,
        **outcome_fields,
        "execution_capability": "NONE",
        "order_execution_enabled": False,
    }
    return OperatorSnapshot(
        **payload,
        snapshot_fingerprint=stable_fingerprint(payload),
    )


def _lifecycle_fields(
    *,
    generated_at: datetime,
    decision: DecisionRecord,
    lifecycle: Cand001VirtualLifecycleState | None,
) -> dict[str, object]:
    if lifecycle is None:
        return {
            "virtual_lifecycle_id": None,
            "virtual_status": None,
            "virtual_side": None,
            "virtual_filled_at": None,
            "virtual_filled_price": None,
            "virtual_closed_at": None,
            "virtual_exit_price": None,
            "virtual_exit_reason": None,
        }
    if decision.final_action is not FinalAction.TRADE:
        raise ValueError("virtual lifecycle requires TRADE decision")
    if lifecycle.decision_id != decision.decision_id:
        raise ValueError("virtual lifecycle decision identity drift")
    if lifecycle.requested_at != decision.event_time:
        raise ValueError("virtual lifecycle request time must match decision time")
    if lifecycle.filled_at is not None and generated_at < lifecycle.filled_at:
        raise ValueError("operator snapshot cannot observe a future virtual fill")
    if lifecycle.closed_at is not None and generated_at < lifecycle.closed_at:
        raise ValueError("operator snapshot cannot observe a future virtual close")
    return {
        "virtual_lifecycle_id": lifecycle.lifecycle_id,
        "virtual_status": lifecycle.status.value,
        "virtual_side": lifecycle.side.value,
        "virtual_filled_at": lifecycle.filled_at,
        "virtual_filled_price": lifecycle.filled_price,
        "virtual_closed_at": lifecycle.closed_at,
        "virtual_exit_price": lifecycle.exit_price,
        "virtual_exit_reason": (
            lifecycle.exit_reason.value
            if lifecycle.status is VirtualPositionStatus.CLOSED
            else None
        ),
    }


def _outcome_fields(
    *,
    generated_at: datetime,
    decision: DecisionRecord,
    lifecycle: Cand001VirtualLifecycleState | None,
    outcome: Cand001VirtualOutcomeEvidence | None,
) -> dict[str, object]:
    if outcome is None:
        return {
            "outcome_id": None,
            "outcome_gross_r": None,
            "outcome_cost_r": None,
            "outcome_net_r": None,
        }
    if lifecycle is None or lifecycle.status is not VirtualPositionStatus.CLOSED:
        raise ValueError("virtual outcome requires CLOSED lifecycle in operator snapshot")
    if outcome.decision_id != decision.decision_id:
        raise ValueError("virtual outcome decision identity drift")
    if outcome.lifecycle_id != lifecycle.lifecycle_id:
        raise ValueError("virtual outcome lifecycle identity drift")
    if generated_at < outcome.closed_at:
        raise ValueError("operator snapshot cannot observe a future virtual outcome")
    return {
        "outcome_id": outcome.outcome_id,
        "outcome_gross_r": outcome.gross_r,
        "outcome_cost_r": outcome.cost_r,
        "outcome_net_r": outcome.net_r,
    }
