"""Atomic local PREPARED evidence; grants no submission or retry capability.

One existing StateStorePort key owns the whole attempt. Callers must serialize
access to that key: StateStorePort offers atomic replacement, not compare-and-swap.
A restored attempt needs later reconciliation, never blind broker resubmission.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from datetime import datetime
from hashlib import sha256
import json
from typing import Any, Mapping

from daxlab.domain.execution import ExecutionIntent, OrderSide
from daxlab.domain.market import InstrumentId
from daxlab.domain.ports import StateStorePort
from daxlab.domain.session_admission import (
    SessionAdmissionAction,
    SessionAdmissionConsumptionRecord,
    SessionAdmissionConsumptionState,
    SessionAdmissionDecision,
    SessionAdmissionPolicy,
    consume_session_admission,
    evaluate_session_admission,
)
from daxlab.runtime.broker_execution_checkpoint import (
    BrokerExecutionCheckpointState,
    broker_execution_checkpoint_payload,
    parse_broker_execution_checkpoint_payload,
)
from daxlab.runtime.broker_execution_protection import (
    BrokerExecutionProtectionVerdict,
    ExecutionProtectionStatus,
)
from daxlab.runtime.broker_execution_telemetry_journal import BrokerExecutionTelemetryJournal
from daxlab.runtime.broker_order_lifecycle import BrokerOrderState, _build_event
from daxlab.runtime.nextgen_broker_lifecycle import (
    _canonical_intent_fingerprint,
    begin_nextgen_order_lifecycle,
)
from daxlab.state.session_admission import (
    SessionAdmissionGuardCheckpoint,
    build_session_admission_guard_checkpoint,
    session_admission_guard_checkpoint_from_bytes,
)

SCHEMA = "DAXLAB_NEXTGEN_PREPARED_CHECKPOINT_V1"


@dataclass(frozen=True, slots=True)
class NextgenPreparedCheckpoint:
    intent: ExecutionIntent
    policy: SessionAdmissionPolicy
    admission: SessionAdmissionDecision
    pre_guard: SessionAdmissionGuardCheckpoint
    post_guard: SessionAdmissionGuardCheckpoint
    broker: BrokerExecutionCheckpointState
    protection: BrokerExecutionProtectionVerdict
    status: str = "PREPARED"
    schema_version: str = SCHEMA
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA or self.status != "PREPARED":
            raise ValueError("prepared schema/status mismatch")
        if self.execution_capability != "NONE" or self.order_execution_enabled is not False:
            raise ValueError("prepared checkpoint cannot authorize execution")
        expected_intent = ExecutionIntent.build(
            decision_id=self.intent.decision_id,
            provenance_fingerprint=self.intent.provenance_fingerprint,
            created_at=self.intent.created_at,
            instrument_id=self.intent.instrument_id,
            side=self.intent.side,
            quantity=self.intent.quantity,
            requested_price=self.intent.requested_price,
            stop_price=self.intent.stop_price,
            target_price=self.intent.target_price,
        )
        if expected_intent != self.intent:
            raise ValueError("prepared intent identity mismatch")
        protection = self.protection
        if not protection.allow_evidence or protection.blockers:
            raise ValueError("prepared requires ALLOW_EVIDENCE protection")
        if (
            protection.execution_capability != "NONE"
            or protection.order_execution_enabled is not False
        ):
            raise ValueError("prepared protection cannot authorize execution")
        if protection.client_order_id != self.intent.intent_id:
            raise ValueError("prepared protection intent mismatch")
        if (
            self.pre_guard.policy_fingerprint != self.policy.policy_fingerprint
            or self.post_guard.policy_fingerprint != self.policy.policy_fingerprint
        ):
            raise ValueError("prepared guard policy mismatch")
        if protection.session_policy_fingerprint != self.policy.policy_fingerprint:
            raise ValueError("prepared protection policy mismatch")
        if (
            protection.session_guard_checkpoint_fingerprint != self.pre_guard.checkpoint_fingerprint
            or protection.session_observation_fingerprint
            != self.pre_guard.observation.observation_fingerprint
        ):
            raise ValueError("prepared protection pre-consumption observation mismatch")
        if (
            self.admission
            != evaluate_session_admission(
                policy=self.policy, observation=self.pre_guard.observation
            )
            or not self.admission.allowed
        ):
            raise ValueError("prepared admission pre-consumption mismatch")
        if protection.session_admission_evidence_fingerprint != self.admission.decision_fingerprint:
            raise ValueError("prepared protection admission mismatch")
        if any(r.consumption_id == self.intent.intent_id for r in self.pre_guard.state.records):
            raise ValueError("prepared pre-consumption state already contains attempt")
        record = SessionAdmissionConsumptionRecord.build(
            consumption_id=self.intent.intent_id,
            admission_decision_fingerprint=self.admission.decision_fingerprint,
        )
        expected_state = SessionAdmissionConsumptionState.build(
            session_key=self.pre_guard.state.session_key,
            records=self.pre_guard.state.records + (record,),
        )
        expected_guard = build_session_admission_guard_checkpoint(
            policy_fingerprint=self.policy.policy_fingerprint,
            state=expected_state,
            observed_at=self.pre_guard.observed_at,
        )
        if self.post_guard != expected_guard:
            raise ValueError("prepared post-consumption guard/record mismatch")
        lifecycle = self.broker.lifecycle
        if lifecycle is None or lifecycle.state is not BrokerOrderState.REQUESTED:
            raise ValueError("prepared lifecycle must be REQUESTED")
        if (
            lifecycle.client_order_id != self.intent.intent_id
            or lifecycle.intent_fingerprint != _canonical_intent_fingerprint(self.intent)
        ):
            raise ValueError("prepared lifecycle intent mismatch")
        if lifecycle.requested_quantity != self.intent.quantity or lifecycle.event_count != 1:
            raise ValueError("prepared lifecycle attempt mismatch")
        if (
            lifecycle.cumulative_filled_quantity != 0
            or lifecycle.average_fill_price is not None
            or lifecycle.venue_order_id is not None
            or self.broker.telemetry_journal.record_fingerprints
        ):
            raise ValueError("prepared cannot contain venue/fill evidence")
        if lifecycle.last_event_time < self.intent.created_at:
            raise ValueError("prepared request precedes intent")
        event = _build_event(
            client_order_id=self.intent.intent_id,
            intent_fingerprint=lifecycle.intent_fingerprint,
            sequence=0,
            previous_state=None,
            state=BrokerOrderState.REQUESTED,
            venue_event_time=lifecycle.last_event_time,
            cumulative_filled_quantity=0.0,
            last_fill_quantity=0.0,
            last_fill_price=None,
            venue_order_id=None,
            reason=None,
        )
        if lifecycle.last_event_fingerprint != event.event_fingerprint:
            raise ValueError("prepared REQUESTED event mismatch")
        # Nested owners enforce their own schemas, hashes and safety contracts.
        parse_broker_execution_checkpoint_payload(broker_execution_checkpoint_payload(self.broker))
        for guard in (self.pre_guard, self.post_guard):
            session_admission_guard_checkpoint_from_bytes(_bytes(guard.to_dict()))

    @property
    def fingerprint(self) -> str:
        return _fingerprint(_payload(self))


def build_nextgen_prepared_checkpoint(
    *,
    intent: ExecutionIntent,
    policy: SessionAdmissionPolicy,
    admission: SessionAdmissionDecision,
    pre_guard: SessionAdmissionGuardCheckpoint,
    protection: BrokerExecutionProtectionVerdict,
    requested_at: datetime,
) -> NextgenPreparedCheckpoint:
    """Consume locally once and compose existing evidence owners; perform no I/O."""
    if not protection.allow_evidence:
        raise ValueError("prepared requires ALLOW_EVIDENCE protection")
    transition = consume_session_admission(
        state=pre_guard.state,
        policy=policy,
        decision=admission,
        session_key=pre_guard.state.session_key,
        consumption_id=intent.intent_id,
    )
    post_guard = build_session_admission_guard_checkpoint(
        policy_fingerprint=policy.policy_fingerprint,
        state=transition.state,
        observed_at=pre_guard.observed_at,
    )
    lifecycle, _ = begin_nextgen_order_lifecycle(intent=intent, requested_at=requested_at)
    return NextgenPreparedCheckpoint(
        intent=intent,
        policy=policy,
        admission=admission,
        pre_guard=pre_guard,
        post_guard=post_guard,
        broker=BrokerExecutionCheckpointState(lifecycle, BrokerExecutionTelemetryJournal()),
        protection=protection,
    )


def nextgen_prepared_checkpoint_to_bytes(checkpoint: NextgenPreparedCheckpoint) -> bytes:
    checkpoint.__post_init__()
    payload = _payload(checkpoint)
    return _bytes(payload | {"prepared_fingerprint": _fingerprint(payload)})


def nextgen_prepared_checkpoint_from_bytes(payload: bytes) -> NextgenPreparedCheckpoint:
    """Restore original evidence without a clock, session reset or lifecycle start."""
    raw = json.loads(payload, object_pairs_hook=_unique, parse_constant=_reject_constant)
    expected_keys = {f.name for f in fields(NextgenPreparedCheckpoint)} | {"prepared_fingerprint"}
    if not isinstance(raw, dict) or raw.keys() != expected_keys:
        raise ValueError("prepared field set mismatch")
    observed = raw.pop("prepared_fingerprint")
    if observed != _fingerprint(raw):
        raise ValueError("prepared fingerprint mismatch")
    i = dict(raw["intent"])
    i["created_at"] = datetime.fromisoformat(i["created_at"])
    i["instrument_id"] = InstrumentId(i["instrument_id"])
    i["side"] = OrderSide(i["side"])
    a = dict(raw["admission"])
    a["action"] = SessionAdmissionAction(a["action"])
    a["reason_codes"] = tuple(a["reason_codes"])
    p = dict(raw["protection"])
    p["status"] = ExecutionProtectionStatus(p["status"])
    p["blockers"] = tuple(p["blockers"])
    p["reconciliation_fingerprints"] = tuple(p["reconciliation_fingerprints"])
    checkpoint = NextgenPreparedCheckpoint(
        intent=ExecutionIntent(**i),
        policy=SessionAdmissionPolicy(**raw["policy"]),
        admission=SessionAdmissionDecision(**a),
        pre_guard=session_admission_guard_checkpoint_from_bytes(_bytes(raw["pre_guard"])),
        post_guard=session_admission_guard_checkpoint_from_bytes(_bytes(raw["post_guard"])),
        broker=parse_broker_execution_checkpoint_payload(raw["broker"]),
        protection=BrokerExecutionProtectionVerdict(**p),
        status=raw["status"],
        schema_version=raw["schema_version"],
        execution_capability=raw["execution_capability"],
        order_execution_enabled=raw["order_execution_enabled"],
    )
    if nextgen_prepared_checkpoint_to_bytes(checkpoint) != payload:
        raise ValueError("prepared payload is not canonical")
    return checkpoint


def prepare_nextgen_checkpoint(
    *,
    store: StateStorePort,
    key: str,
    intent: ExecutionIntent,
    policy: SessionAdmissionPolicy,
    admission: SessionAdmissionDecision,
    pre_guard: SessionAdmissionGuardCheckpoint,
    protection: BrokerExecutionProtectionVerdict,
    requested_at: datetime,
) -> NextgenPreparedCheckpoint:
    """Single-key atomic write; exact retry returns original evidence without save."""
    existing = store.load(key)
    if existing is not None:
        checkpoint = nextgen_prepared_checkpoint_from_bytes(existing)
        if (
            checkpoint.intent,
            checkpoint.policy,
            checkpoint.admission,
            checkpoint.pre_guard,
            checkpoint.protection,
            checkpoint.broker.lifecycle.last_event_time,
        ) != (
            intent,
            policy,
            admission,
            pre_guard,
            protection,
            requested_at,
        ):
            raise ValueError("prepared store-key attempt/provenance collision")
        return checkpoint
    checkpoint = build_nextgen_prepared_checkpoint(
        intent=intent,
        policy=policy,
        admission=admission,
        pre_guard=pre_guard,
        protection=protection,
        requested_at=requested_at,
    )
    store.save(key, nextgen_prepared_checkpoint_to_bytes(checkpoint))
    return checkpoint


def _payload(checkpoint: NextgenPreparedCheckpoint) -> dict[str, Any]:
    intent = asdict(checkpoint.intent)
    intent.update(
        created_at=checkpoint.intent.created_at.isoformat(),
        instrument_id=checkpoint.intent.instrument_id.value,
        side=checkpoint.intent.side.value,
    )
    return {
        "schema_version": checkpoint.schema_version,
        "status": checkpoint.status,
        "intent": intent,
        "policy": asdict(checkpoint.policy),
        "admission": asdict(checkpoint.admission),
        "pre_guard": checkpoint.pre_guard.to_dict(),
        "post_guard": checkpoint.post_guard.to_dict(),
        "broker": broker_execution_checkpoint_payload(checkpoint.broker),
        "protection": asdict(checkpoint.protection),
        "execution_capability": checkpoint.execution_capability,
        "order_execution_enabled": checkpoint.order_execution_enabled,
    }


def _bytes(payload: object) -> bytes:
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("utf-8")


def _fingerprint(payload: Mapping[str, Any]) -> str:
    return sha256(_bytes(payload)).hexdigest()


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate prepared JSON field")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite prepared JSON value: {value}")
