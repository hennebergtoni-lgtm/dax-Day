"""Credential-free read-only operator snapshot for DAX-BOT 1.x.

The snapshot separates the current strategy decision from any still-open or just-
closed virtual position. A position may originate from an earlier TRADE decision
while the current bar legitimately produces a later NO_TRADE decision.
"""
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


SCHEMA_VERSION = "DAX_BOT_OPERATOR_SNAPSHOT_V3"


@dataclass(frozen=True, slots=True)
class OperatorSnapshot:
    schema_version: str
    generated_at: datetime
    core_version: str
    candidate_id: str
    config_fingerprint: str
    regime: str
    structure: str
    setup: str
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
    last_bar_id: str | None
    last_bar_close_time: datetime | None
    freshness_seconds: float | None
    health_state: str | None
    health_source: str | None
    runtime_events: tuple[str, ...]
    recovery_state: str | None
    reconciliation_state: str | None
    virtual_lifecycle_id: str | None
    virtual_decision_id: str | None
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
        for value in (
            self.last_bar_close_time,
            self.virtual_filled_at,
            self.virtual_closed_at,
        ):
            if value is not None and value.tzinfo is None:
                raise ValueError("operator snapshot timestamps must be timezone-aware")

        runtime_values = (
            self.last_bar_id,
            self.last_bar_close_time,
            self.freshness_seconds,
        )
        if any(value is not None for value in runtime_values) and any(
            value is None for value in runtime_values
        ):
            raise ValueError("operator runtime bar context must be complete")
        if self.last_bar_id is not None:
            _sha(self.last_bar_id, "last_bar_id")
            assert self.last_bar_close_time is not None
            assert self.freshness_seconds is not None
            if self.freshness_seconds < 0:
                raise ValueError("freshness_seconds cannot be negative")
            if self.generated_at < self.last_bar_close_time:
                raise ValueError("operator snapshot cannot precede last closed bar")

        if (self.health_state is None) != (self.health_source is None):
            raise ValueError("health_state and health_source must be supplied together")
        if self.health_state is not None and not self.health_state.strip():
            raise ValueError("health_state must be non-empty")
        if self.health_source is not None and not self.health_source.strip():
            raise ValueError("health_source must be non-empty")
        if any(not event.strip() for event in self.runtime_events):
            raise ValueError("runtime_events must be non-empty strings")
        if len(set(self.runtime_events)) != len(self.runtime_events):
            raise ValueError("runtime_events must be unique")

        if self.execution_capability != "NONE":
            raise ValueError("operator snapshot cannot carry execution capability")
        if self.order_execution_enabled is not False:
            raise ValueError("operator snapshot cannot enable order execution")

        _sha(self.config_fingerprint, "config_fingerprint")
        _sha(self.decision_id, "decision_id")
        if self.virtual_lifecycle_id is not None:
            _sha(self.virtual_lifecycle_id, "virtual_lifecycle_id")
        if self.virtual_decision_id is not None:
            _sha(self.virtual_decision_id, "virtual_decision_id")
        if (self.virtual_lifecycle_id is None) != (self.virtual_decision_id is None):
            raise ValueError("virtual lifecycle and origin decision identity must be paired")
        if self.outcome_id is not None:
            _sha(self.outcome_id, "outcome_id")
        _sha(self.snapshot_fingerprint, "snapshot_fingerprint")

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at.isoformat(),
            "core_version": self.core_version,
            "candidate_id": self.candidate_id,
            "config_fingerprint": self.config_fingerprint,
            "strategy": {
                "regime": self.regime,
                "structure": self.structure,
                "setup": self.setup,
            },
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
            "runtime": {
                "last_bar_id": self.last_bar_id,
                "last_bar_close_time": (
                    self.last_bar_close_time.isoformat()
                    if self.last_bar_close_time is not None
                    else None
                ),
                "freshness_seconds": self.freshness_seconds,
                "health_state": self.health_state,
                "health_source": self.health_source,
                "events": list(self.runtime_events),
                "recovery_state": self.recovery_state,
                "reconciliation_state": self.reconciliation_state,
            },
            "virtual_position": {
                "lifecycle_id": self.virtual_lifecycle_id,
                "origin_decision_id": self.virtual_decision_id,
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
    last_bar_id: str | None = None,
    last_bar_close_time: datetime | None = None,
    freshness_seconds: float | None = None,
    health_state: str | None = None,
    health_source: str | None = None,
    runtime_events: tuple[str, ...] = (),
    recovery_state: str | None = None,
    reconciliation_state: str | None = None,
    lifecycle: Cand001VirtualLifecycleState | None = None,
    outcome: Cand001VirtualOutcomeEvidence | None = None,
) -> OperatorSnapshot:
    """Build a read-only current-decision view plus independent position context."""
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

    runtime_fields = _runtime_fields(
        generated_at=generated_at,
        last_bar_id=last_bar_id,
        last_bar_close_time=last_bar_close_time,
        freshness_seconds=freshness_seconds,
        health_state=health_state,
        health_source=health_source,
        runtime_events=runtime_events,
        recovery_state=recovery_state,
        reconciliation_state=reconciliation_state,
    )
    lifecycle_fields = _lifecycle_fields(
        generated_at=generated_at,
        lifecycle=lifecycle,
    )
    outcome_fields = _outcome_fields(
        generated_at=generated_at,
        lifecycle=lifecycle,
        outcome=outcome,
    )

    payload = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "core_version": identity.core_version,
        "candidate_id": identity.candidate_id,
        "config_fingerprint": identity.config_fingerprint,
        "regime": decision.regime,
        "structure": decision.structure,
        "setup": decision.setup,
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
        **runtime_fields,
        **lifecycle_fields,
        **outcome_fields,
        "execution_capability": "NONE",
        "order_execution_enabled": False,
    }
    return OperatorSnapshot(
        **payload,
        snapshot_fingerprint=stable_fingerprint(payload),
    )


def _runtime_fields(
    *,
    generated_at: datetime,
    last_bar_id: str | None,
    last_bar_close_time: datetime | None,
    freshness_seconds: float | None,
    health_state: str | None,
    health_source: str | None,
    runtime_events: tuple[str, ...],
    recovery_state: str | None,
    reconciliation_state: str | None,
) -> dict[str, object]:
    values = (last_bar_id, last_bar_close_time, freshness_seconds)
    if all(value is None for value in values):
        bar_fields: dict[str, object] = {
            "last_bar_id": None,
            "last_bar_close_time": None,
            "freshness_seconds": None,
        }
    else:
        if any(value is None for value in values):
            raise ValueError("operator runtime bar context must be complete")
        assert last_bar_id is not None
        assert last_bar_close_time is not None
        assert freshness_seconds is not None
        _sha(last_bar_id, "last_bar_id")
        if last_bar_close_time.tzinfo is None:
            raise ValueError("last_bar_close_time must be timezone-aware")
        if freshness_seconds < 0:
            raise ValueError("freshness_seconds cannot be negative")
        if generated_at < last_bar_close_time:
            raise ValueError("operator snapshot cannot precede last closed bar")
        bar_fields = {
            "last_bar_id": last_bar_id,
            "last_bar_close_time": last_bar_close_time,
            "freshness_seconds": float(freshness_seconds),
        }

    if (health_state is None) != (health_source is None):
        raise ValueError("health_state and health_source must be supplied together")
    if health_state is not None and not health_state.strip():
        raise ValueError("health_state must be non-empty")
    if health_source is not None and not health_source.strip():
        raise ValueError("health_source must be non-empty")

    events = tuple(dict.fromkeys(runtime_events))
    if any(not isinstance(event, str) or not event.strip() for event in events):
        raise ValueError("runtime_events must be non-empty strings")
    for value, field in (
        (recovery_state, "recovery_state"),
        (reconciliation_state, "reconciliation_state"),
    ):
        if value is not None and (not isinstance(value, str) or not value.strip()):
            raise ValueError(f"{field} must be non-empty string or null")

    return {
        **bar_fields,
        "health_state": health_state,
        "health_source": health_source,
        "runtime_events": events,
        "recovery_state": recovery_state,
        "reconciliation_state": reconciliation_state,
    }


def _lifecycle_fields(
    *,
    generated_at: datetime,
    lifecycle: Cand001VirtualLifecycleState | None,
) -> dict[str, object]:
    if lifecycle is None:
        return {
            "virtual_lifecycle_id": None,
            "virtual_decision_id": None,
            "virtual_status": None,
            "virtual_side": None,
            "virtual_filled_at": None,
            "virtual_filled_price": None,
            "virtual_closed_at": None,
            "virtual_exit_price": None,
            "virtual_exit_reason": None,
        }

    if generated_at < lifecycle.requested_at:
        raise ValueError("operator snapshot cannot observe a future virtual request")
    if lifecycle.filled_at is not None and generated_at < lifecycle.filled_at:
        raise ValueError("operator snapshot cannot observe a future virtual fill")
    if lifecycle.closed_at is not None and generated_at < lifecycle.closed_at:
        raise ValueError("operator snapshot cannot observe a future virtual close")

    return {
        "virtual_lifecycle_id": lifecycle.lifecycle_id,
        "virtual_decision_id": lifecycle.decision_id,
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
    if outcome.decision_id != lifecycle.decision_id:
        raise ValueError("virtual outcome origin decision identity drift")
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


def _sha(value: str, field: str) -> None:
    if len(value) != 64:
        raise ValueError(f"{field} must be sha256 hex")
    int(value, 16)
