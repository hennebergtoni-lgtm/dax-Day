"""Canonical broker-neutral session-admission evidence.

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


class SessionAdmissionAction(StrEnum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"


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
