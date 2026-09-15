"""Canonical broker-neutral session-admission evidence and consumption state.

This module consumes an already-derived session key and admitted-trade count. It
does not derive dates, timezones, session boundaries, calendars or reset events,
and it grants no broker execution capability.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
import json


SESSION_ADMISSION_POLICY_SCHEMA = "DAXLAB_SESSION_ADMISSION_POLICY_V1"
SESSION_ADMISSION_OBSERVATION_SCHEMA = "DAXLAB_SESSION_ADMISSION_OBSERVATION_V1"
SESSION_ADMISSION_DECISION_SCHEMA = "DAXLAB_SESSION_ADMISSION_DECISION_V1"
SESSION_ADMISSION_CONSUMPTION_RECORD_SCHEMA = (
    "DAXLAB_SESSION_ADMISSION_CONSUMPTION_RECORD_V1"
)
SESSION_ADMISSION_CONSUMPTION_STATE_SCHEMA = (
    "DAXLAB_SESSION_ADMISSION_CONSUMPTION_STATE_V1"
)
SESSION_ADMISSION_CONSUMPTION_TRANSITION_SCHEMA = (
    "DAXLAB_SESSION_ADMISSION_CONSUMPTION_TRANSITION_V1"
)


class SessionAdmissionAction(StrEnum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"


class SessionAdmissionConsumptionAction(StrEnum):
    CONSUMED = "CONSUMED"
    IDEMPOTENT_REPLAY = "IDEMPOTENT_REPLAY"


@dataclass(frozen=True, slots=True)
class SessionAdmissionPolicy:
    max_trades_per_session: int
    policy_fingerprint: str
    schema_version: str = SESSION_ADMISSION_POLICY_SCHEMA

    @classmethod
    def build(cls, *, max_trades_per_session: int) -> "SessionAdmissionPolicy":
        _require_positive_int(max_trades_per_session, "max_trades_per_session")
        payload = {
            "schema_version": SESSION_ADMISSION_POLICY_SCHEMA,
            "max_trades_per_session": max_trades_per_session,
        }
        return cls(
            max_trades_per_session=max_trades_per_session,
            policy_fingerprint=_fingerprint(payload),
        )

    def __post_init__(self) -> None:
        if self.schema_version != SESSION_ADMISSION_POLICY_SCHEMA:
            raise ValueError("session admission policy schema mismatch")
        _require_positive_int(self.max_trades_per_session, "max_trades_per_session")
        expected = _fingerprint(
            {
                "schema_version": self.schema_version,
                "max_trades_per_session": self.max_trades_per_session,
            }
        )
        if self.policy_fingerprint != expected:
            raise ValueError("session admission policy fingerprint mismatch")


@dataclass(frozen=True, slots=True)
class SessionAdmissionObservation:
    session_key: str
    trades_admitted: int
    observation_fingerprint: str
    schema_version: str = SESSION_ADMISSION_OBSERVATION_SCHEMA

    @classmethod
    def build(
        cls,
        *,
        session_key: str,
        trades_admitted: int,
    ) -> "SessionAdmissionObservation":
        _require_token(session_key, "session_key")
        _require_non_negative_int(trades_admitted, "trades_admitted")
        payload = {
            "schema_version": SESSION_ADMISSION_OBSERVATION_SCHEMA,
            "session_key": session_key,
            "trades_admitted": trades_admitted,
        }
        return cls(
            session_key=session_key,
            trades_admitted=trades_admitted,
            observation_fingerprint=_fingerprint(payload),
        )

    def __post_init__(self) -> None:
        if self.schema_version != SESSION_ADMISSION_OBSERVATION_SCHEMA:
            raise ValueError("session admission observation schema mismatch")
        _require_token(self.session_key, "session_key")
        _require_non_negative_int(self.trades_admitted, "trades_admitted")
        expected = _fingerprint(
            {
                "schema_version": self.schema_version,
                "session_key": self.session_key,
                "trades_admitted": self.trades_admitted,
            }
        )
        if self.observation_fingerprint != expected:
            raise ValueError("session admission observation fingerprint mismatch")


@dataclass(frozen=True, slots=True)
class SessionAdmissionDecision:
    action: SessionAdmissionAction
    policy_fingerprint: str
    observation_fingerprint: str
    reason_codes: tuple[str, ...]
    decision_fingerprint: str
    schema_version: str = SESSION_ADMISSION_DECISION_SCHEMA

    def __post_init__(self) -> None:
        if self.schema_version != SESSION_ADMISSION_DECISION_SCHEMA:
            raise ValueError("session admission decision schema mismatch")
        _require_sha256(self.policy_fingerprint, "policy_fingerprint")
        _require_sha256(self.observation_fingerprint, "observation_fingerprint")
        expected_reasons = (
            ("WITHIN_SESSION_TRADE_LIMIT",)
            if self.action is SessionAdmissionAction.ALLOW
            else ("MAX_TRADES_PER_SESSION",)
        )
        if self.reason_codes != expected_reasons:
            raise ValueError("session admission decision reason mismatch")
        expected = _fingerprint(
            {
                "schema_version": self.schema_version,
                "action": self.action.value,
                "policy_fingerprint": self.policy_fingerprint,
                "observation_fingerprint": self.observation_fingerprint,
                "reason_codes": list(self.reason_codes),
            }
        )
        if self.decision_fingerprint != expected:
            raise ValueError("session admission decision fingerprint mismatch")

    @property
    def allowed(self) -> bool:
        return self.action is SessionAdmissionAction.ALLOW


@dataclass(frozen=True, slots=True)
class SessionAdmissionConsumptionRecord:
    consumption_id: str
    admission_decision_fingerprint: str
    record_fingerprint: str
    schema_version: str = SESSION_ADMISSION_CONSUMPTION_RECORD_SCHEMA

    @classmethod
    def build(
        cls,
        *,
        consumption_id: str,
        admission_decision_fingerprint: str,
    ) -> "SessionAdmissionConsumptionRecord":
        _require_sha256(consumption_id, "consumption_id")
        _require_sha256(
            admission_decision_fingerprint,
            "admission_decision_fingerprint",
        )
        payload = {
            "schema_version": SESSION_ADMISSION_CONSUMPTION_RECORD_SCHEMA,
            "consumption_id": consumption_id,
            "admission_decision_fingerprint": admission_decision_fingerprint,
        }
        return cls(
            consumption_id=consumption_id,
            admission_decision_fingerprint=admission_decision_fingerprint,
            record_fingerprint=_fingerprint(payload),
        )

    def __post_init__(self) -> None:
        if self.schema_version != SESSION_ADMISSION_CONSUMPTION_RECORD_SCHEMA:
            raise ValueError("session admission consumption record schema mismatch")
        _require_sha256(self.consumption_id, "consumption_id")
        _require_sha256(
            self.admission_decision_fingerprint,
            "admission_decision_fingerprint",
        )
        expected = _fingerprint(
            {
                "schema_version": self.schema_version,
                "consumption_id": self.consumption_id,
                "admission_decision_fingerprint": self.admission_decision_fingerprint,
            }
        )
        if self.record_fingerprint != expected:
            raise ValueError("session admission consumption record fingerprint mismatch")


@dataclass(frozen=True, slots=True)
class SessionAdmissionConsumptionState:
    session_key: str
    records: tuple[SessionAdmissionConsumptionRecord, ...]
    state_fingerprint: str
    schema_version: str = SESSION_ADMISSION_CONSUMPTION_STATE_SCHEMA

    @classmethod
    def build(
        cls,
        *,
        session_key: str,
        records: tuple[SessionAdmissionConsumptionRecord, ...] = (),
    ) -> "SessionAdmissionConsumptionState":
        _require_token(session_key, "session_key")
        _validate_consumption_records(records)
        payload = _consumption_state_payload(
            schema_version=SESSION_ADMISSION_CONSUMPTION_STATE_SCHEMA,
            session_key=session_key,
            records=records,
        )
        return cls(
            session_key=session_key,
            records=records,
            state_fingerprint=_fingerprint(payload),
        )

    def __post_init__(self) -> None:
        if self.schema_version != SESSION_ADMISSION_CONSUMPTION_STATE_SCHEMA:
            raise ValueError("session admission consumption state schema mismatch")
        _require_token(self.session_key, "session_key")
        _validate_consumption_records(self.records)
        expected = _fingerprint(
            _consumption_state_payload(
                schema_version=self.schema_version,
                session_key=self.session_key,
                records=self.records,
            )
        )
        if self.state_fingerprint != expected:
            raise ValueError("session admission consumption state fingerprint mismatch")

    @property
    def trades_admitted(self) -> int:
        return len(self.records)

    @property
    def observation(self) -> SessionAdmissionObservation:
        return SessionAdmissionObservation.build(
            session_key=self.session_key,
            trades_admitted=self.trades_admitted,
        )


@dataclass(frozen=True, slots=True)
class SessionAdmissionConsumptionTransition:
    action: SessionAdmissionConsumptionAction
    state: SessionAdmissionConsumptionState
    observation: SessionAdmissionObservation
    consumption_id: str
    admission_decision_fingerprint: str
    transition_fingerprint: str
    schema_version: str = SESSION_ADMISSION_CONSUMPTION_TRANSITION_SCHEMA
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != SESSION_ADMISSION_CONSUMPTION_TRANSITION_SCHEMA:
            raise ValueError("session admission consumption transition schema mismatch")
        _require_sha256(self.consumption_id, "consumption_id")
        _require_sha256(
            self.admission_decision_fingerprint,
            "admission_decision_fingerprint",
        )
        if self.observation != self.state.observation:
            raise ValueError("session admission transition observation mismatch")
        if self.execution_capability != "NONE" or self.order_execution_enabled:
            raise ValueError("session admission consumption cannot authorize execution")
        expected = _fingerprint(
            _consumption_transition_payload(
                schema_version=self.schema_version,
                action=self.action,
                state=self.state,
                observation=self.observation,
                consumption_id=self.consumption_id,
                admission_decision_fingerprint=self.admission_decision_fingerprint,
            )
        )
        if self.transition_fingerprint != expected:
            raise ValueError("session admission consumption transition fingerprint mismatch")

    @property
    def consumed(self) -> bool:
        return self.action is SessionAdmissionConsumptionAction.CONSUMED

    @property
    def idempotent_replay(self) -> bool:
        return self.action is SessionAdmissionConsumptionAction.IDEMPOTENT_REPLAY


def evaluate_session_admission(
    *,
    policy: SessionAdmissionPolicy,
    observation: SessionAdmissionObservation,
) -> SessionAdmissionDecision:
    action = (
        SessionAdmissionAction.BLOCK
        if observation.trades_admitted >= policy.max_trades_per_session
        else SessionAdmissionAction.ALLOW
    )
    reasons = (
        ("MAX_TRADES_PER_SESSION",)
        if action is SessionAdmissionAction.BLOCK
        else ("WITHIN_SESSION_TRADE_LIMIT",)
    )
    payload = {
        "schema_version": SESSION_ADMISSION_DECISION_SCHEMA,
        "action": action.value,
        "policy_fingerprint": policy.policy_fingerprint,
        "observation_fingerprint": observation.observation_fingerprint,
        "reason_codes": list(reasons),
    }
    return SessionAdmissionDecision(
        action=action,
        policy_fingerprint=policy.policy_fingerprint,
        observation_fingerprint=observation.observation_fingerprint,
        reason_codes=reasons,
        decision_fingerprint=_fingerprint(payload),
    )


def consume_session_admission(
    *,
    state: SessionAdmissionConsumptionState,
    policy: SessionAdmissionPolicy,
    decision: SessionAdmissionDecision,
    session_key: str,
    consumption_id: str,
) -> SessionAdmissionConsumptionTransition:
    """Consume one explicit trade slot exactly once; infer no session boundary."""
    _require_token(session_key, "session_key")
    _require_sha256(consumption_id, "consumption_id")
    if session_key != state.session_key:
        raise ValueError("session admission consumption session key mismatch")
    if decision.policy_fingerprint != policy.policy_fingerprint:
        raise ValueError("session admission consumption decision policy mismatch")
    if not decision.allowed:
        raise ValueError("blocked session admission cannot be consumed")

    existing = next(
        (record for record in state.records if record.consumption_id == consumption_id),
        None,
    )
    if existing is not None:
        if existing.admission_decision_fingerprint != decision.decision_fingerprint:
            raise ValueError("session admission consumption provenance conflict")
        return _build_consumption_transition(
            action=SessionAdmissionConsumptionAction.IDEMPOTENT_REPLAY,
            state=state,
            consumption_id=consumption_id,
            decision=decision,
        )

    current_observation = state.observation
    expected_decision = evaluate_session_admission(
        policy=policy,
        observation=current_observation,
    )
    if decision != expected_decision:
        raise ValueError(
            "session admission decision does not match current consumption state"
        )

    record = SessionAdmissionConsumptionRecord.build(
        consumption_id=consumption_id,
        admission_decision_fingerprint=decision.decision_fingerprint,
    )
    next_state = SessionAdmissionConsumptionState.build(
        session_key=state.session_key,
        records=state.records + (record,),
    )
    return _build_consumption_transition(
        action=SessionAdmissionConsumptionAction.CONSUMED,
        state=next_state,
        consumption_id=consumption_id,
        decision=decision,
    )


def _build_consumption_transition(
    *,
    action: SessionAdmissionConsumptionAction,
    state: SessionAdmissionConsumptionState,
    consumption_id: str,
    decision: SessionAdmissionDecision,
) -> SessionAdmissionConsumptionTransition:
    observation = state.observation
    payload = _consumption_transition_payload(
        schema_version=SESSION_ADMISSION_CONSUMPTION_TRANSITION_SCHEMA,
        action=action,
        state=state,
        observation=observation,
        consumption_id=consumption_id,
        admission_decision_fingerprint=decision.decision_fingerprint,
    )
    return SessionAdmissionConsumptionTransition(
        action=action,
        state=state,
        observation=observation,
        consumption_id=consumption_id,
        admission_decision_fingerprint=decision.decision_fingerprint,
        transition_fingerprint=_fingerprint(payload),
    )


def _validate_consumption_records(
    records: tuple[SessionAdmissionConsumptionRecord, ...],
) -> None:
    if not isinstance(records, tuple):
        raise ValueError("session admission consumption records must be tuple")
    if not all(isinstance(record, SessionAdmissionConsumptionRecord) for record in records):
        raise ValueError("session admission consumption records contain invalid value")
    ids = tuple(record.consumption_id for record in records)
    if len(ids) != len(set(ids)):
        raise ValueError("session admission consumption IDs must be unique")


def _consumption_state_payload(
    *,
    schema_version: str,
    session_key: str,
    records: tuple[SessionAdmissionConsumptionRecord, ...],
) -> dict[str, object]:
    return {
        "schema_version": schema_version,
        "session_key": session_key,
        "record_fingerprints": [record.record_fingerprint for record in records],
    }


def _consumption_transition_payload(
    *,
    schema_version: str,
    action: SessionAdmissionConsumptionAction,
    state: SessionAdmissionConsumptionState,
    observation: SessionAdmissionObservation,
    consumption_id: str,
    admission_decision_fingerprint: str,
) -> dict[str, object]:
    return {
        "schema_version": schema_version,
        "action": action.value,
        "state_fingerprint": state.state_fingerprint,
        "observation_fingerprint": observation.observation_fingerprint,
        "consumption_id": consumption_id,
        "admission_decision_fingerprint": admission_decision_fingerprint,
        "execution_capability": "NONE",
        "order_execution_enabled": False,
    }


def _require_positive_int(value: int, field_name: str) -> None:
    if type(value) is not int or value < 1:
        raise ValueError(f"{field_name} must be an integer >= 1")


def _require_non_negative_int(value: int, field_name: str) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field_name} must be a non-negative integer")


def _require_token(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty normalized token")


def _require_sha256(value: str, field_name: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{field_name} must be sha256 hex")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be sha256 hex") from exc


def _fingerprint(payload: object) -> str:
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()
