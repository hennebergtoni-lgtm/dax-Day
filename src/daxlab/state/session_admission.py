"""Restart-safe persistence for explicit canonical session-admission observations.

This module persists caller-supplied session evidence only. It does not derive
session keys, timezones, calendars or reset transitions. Storage mechanics remain
owned by ``StateStorePort`` implementations.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any, Mapping

from daxlab.domain.ports import StateStorePort
from daxlab.domain.session_admission import SessionAdmissionObservation


SESSION_ADMISSION_OBSERVATION_CHECKPOINT_SCHEMA = (
    "DAXLAB_SESSION_ADMISSION_OBSERVATION_CHECKPOINT_V1"
)


class SessionAdmissionCheckpointCompatibilityError(RuntimeError):
    """Raised when persisted session observation state belongs to another policy."""


@dataclass(frozen=True, slots=True)
class SessionAdmissionObservationCheckpoint:
    policy_fingerprint: str
    observation: SessionAdmissionObservation
    observed_at: datetime
    checkpoint_fingerprint: str
    schema_version: str = SESSION_ADMISSION_OBSERVATION_CHECKPOINT_SCHEMA
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != SESSION_ADMISSION_OBSERVATION_CHECKPOINT_SCHEMA:
            raise ValueError("session admission checkpoint schema mismatch")
        _require_sha256(self.policy_fingerprint, "policy_fingerprint")
        _require_aware(self.observed_at, "observed_at")
        _require_sha256(self.checkpoint_fingerprint, "checkpoint_fingerprint")
        if self.execution_capability != "NONE" or self.order_execution_enabled:
            raise ValueError("session admission checkpoint cannot authorize execution")
        if self.checkpoint_fingerprint != _fingerprint(_identity_payload(self)):
            raise ValueError("session admission checkpoint fingerprint mismatch")

    def to_dict(self) -> dict[str, object]:
        return _identity_payload(self) | {
            "checkpoint_fingerprint": self.checkpoint_fingerprint,
        }


def build_session_admission_observation_checkpoint(
    *,
    policy_fingerprint: str,
    observation: SessionAdmissionObservation,
    observed_at: datetime,
) -> SessionAdmissionObservationCheckpoint:
    _require_sha256(policy_fingerprint, "policy_fingerprint")
    _require_aware(observed_at, "observed_at")
    observed_at_utc = observed_at.astimezone(timezone.utc)
    identity = _values_payload(
        policy_fingerprint=policy_fingerprint,
        observation=observation,
        observed_at=observed_at_utc,
    )
    return SessionAdmissionObservationCheckpoint(
        policy_fingerprint=policy_fingerprint,
        observation=observation,
        observed_at=observed_at_utc,
        checkpoint_fingerprint=_fingerprint(identity),
    )


def session_admission_checkpoint_to_bytes(
    checkpoint: SessionAdmissionObservationCheckpoint,
) -> bytes:
    text = json.dumps(
        checkpoint.to_dict(),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return (text + "\n").encode("utf-8")


def session_admission_checkpoint_from_bytes(
    payload: bytes,
) -> SessionAdmissionObservationCheckpoint:
    if not isinstance(payload, bytes):
        raise TypeError("session admission checkpoint payload must be bytes")
    try:
        decoded = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("session admission checkpoint must be valid UTF-8 JSON") from exc
    if not isinstance(decoded, dict):
        raise ValueError("session admission checkpoint must be a JSON object")

    expected_keys = {
        "schema_version",
        "policy_fingerprint",
        "observation",
        "observed_at_utc",
        "execution_capability",
        "order_execution_enabled",
        "checkpoint_fingerprint",
    }
    if set(decoded) != expected_keys:
        raise ValueError("session admission checkpoint field set mismatch")

    raw_observation = decoded["observation"]
    if not isinstance(raw_observation, dict):
        raise ValueError("session admission checkpoint observation must be object")
    observation_keys = {
        "schema_version",
        "session_key",
        "trades_admitted",
        "observation_fingerprint",
    }
    if set(raw_observation) != observation_keys:
        raise ValueError("session admission observation field set mismatch")

    observed_at_raw = decoded["observed_at_utc"]
    if not isinstance(observed_at_raw, str):
        raise ValueError("observed_at_utc must be ISO-8601 text")
    try:
        observed_at = datetime.fromisoformat(observed_at_raw)
    except ValueError as exc:
        raise ValueError("observed_at_utc must be ISO-8601 text") from exc
    _require_aware(observed_at, "observed_at_utc")

    observation = SessionAdmissionObservation(
        session_key=_text(raw_observation, "session_key"),
        trades_admitted=_int(raw_observation, "trades_admitted"),
        observation_fingerprint=_text(raw_observation, "observation_fingerprint"),
        schema_version=_text(raw_observation, "schema_version"),
    )
    return SessionAdmissionObservationCheckpoint(
        policy_fingerprint=_text(decoded, "policy_fingerprint"),
        observation=observation,
        observed_at=observed_at.astimezone(timezone.utc),
        checkpoint_fingerprint=_text(decoded, "checkpoint_fingerprint"),
        schema_version=_text(decoded, "schema_version"),
        execution_capability=_text(decoded, "execution_capability"),
        order_execution_enabled=_bool(decoded, "order_execution_enabled"),
    )


def save_session_admission_checkpoint(
    store: StateStorePort,
    key: str,
    checkpoint: SessionAdmissionObservationCheckpoint,
) -> None:
    store.save(key, session_admission_checkpoint_to_bytes(checkpoint))


def load_session_admission_checkpoint(
    store: StateStorePort,
    key: str,
) -> SessionAdmissionObservationCheckpoint | None:
    payload = store.load(key)
    if payload is None:
        return None
    return session_admission_checkpoint_from_bytes(payload)


def assert_session_admission_checkpoint_compatible(
    checkpoint: SessionAdmissionObservationCheckpoint,
    *,
    policy_fingerprint: str,
) -> None:
    _require_sha256(policy_fingerprint, "policy_fingerprint")
    if checkpoint.policy_fingerprint != policy_fingerprint:
        raise SessionAdmissionCheckpointCompatibilityError(
            "session admission checkpoint policy fingerprint mismatch"
        )


def _identity_payload(
    checkpoint: SessionAdmissionObservationCheckpoint,
) -> dict[str, object]:
    return _values_payload(
        policy_fingerprint=checkpoint.policy_fingerprint,
        observation=checkpoint.observation,
        observed_at=checkpoint.observed_at,
        schema_version=checkpoint.schema_version,
        execution_capability=checkpoint.execution_capability,
        order_execution_enabled=checkpoint.order_execution_enabled,
    )


def _values_payload(
    *,
    policy_fingerprint: str,
    observation: SessionAdmissionObservation,
    observed_at: datetime,
    schema_version: str = SESSION_ADMISSION_OBSERVATION_CHECKPOINT_SCHEMA,
    execution_capability: str = "NONE",
    order_execution_enabled: bool = False,
) -> dict[str, object]:
    return {
        "schema_version": schema_version,
        "policy_fingerprint": policy_fingerprint,
        "observation": {
            "schema_version": observation.schema_version,
            "session_key": observation.session_key,
            "trades_admitted": observation.trades_admitted,
            "observation_fingerprint": observation.observation_fingerprint,
        },
        "observed_at_utc": observed_at.astimezone(timezone.utc).isoformat(),
        "execution_capability": execution_capability,
        "order_execution_enabled": order_execution_enabled,
    }


def _require_sha256(value: str, field_name: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{field_name} must be sha256 hex")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be sha256 hex") from exc


def _require_aware(value: datetime, field_name: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")


def _text(payload: Mapping[str, Any], field_name: str) -> str:
    value = payload[field_name]
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field_name} must be non-empty text")
    return value


def _int(payload: Mapping[str, Any], field_name: str) -> int:
    value = payload[field_name]
    if type(value) is not int:
        raise ValueError(f"{field_name} must be integer")
    return value


def _bool(payload: Mapping[str, Any], field_name: str) -> bool:
    value = payload[field_name]
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be boolean")
    return value


def _fingerprint(value: object) -> str:
    canonical = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()
