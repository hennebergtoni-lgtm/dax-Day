"""Credential-free read-only operator snapshot for DAX-BOT 1.x."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from daxlab.runtime.candidate_admission import AdmissionStatus, Cand001AdmissionResult
from daxlab.runtime.candidate_config import Cand001Config
from daxlab.runtime.candidate_signal import Cand001Signal
from daxlab.runtime.candidate_trade_plan import Cand001TradePlan
from daxlab.runtime.decision import DecisionRecord, FinalAction, stable_fingerprint


SCHEMA_VERSION = "DAX_BOT_OPERATOR_SNAPSHOT_V1"


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
    execution_capability: str
    order_execution_enabled: bool
    snapshot_fingerprint: str

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError("operator snapshot schema mismatch")
        if self.generated_at.tzinfo is None:
            raise ValueError("generated_at must be timezone-aware")
        if self.execution_capability != "NONE":
            raise ValueError("operator snapshot cannot carry execution capability")
        if self.order_execution_enabled is not False:
            raise ValueError("operator snapshot cannot enable order execution")
        if len(self.config_fingerprint) != 64 or len(self.decision_id) != 64:
            raise ValueError("operator snapshot identity fingerprints must be sha256 hex")
        int(self.config_fingerprint, 16)
        int(self.decision_id, 16)
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
        "execution_capability": "NONE",
        "order_execution_enabled": False,
    }
    return OperatorSnapshot(
        **payload,
        snapshot_fingerprint=stable_fingerprint(payload),
    )
