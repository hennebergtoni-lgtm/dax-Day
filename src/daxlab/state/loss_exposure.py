"""Restart-safe persistence for explicit canonical loss/exposure observations.

This module persists caller-supplied observation evidence only. It does not
calculate PnL, infer account state, choose reset boundaries, or access a broker.
Storage mechanics remain owned by ``StateStorePort`` implementations.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any

from daxlab.domain.loss_admission import LossExposureObservation
from daxlab.domain.ports import StateStorePort


LOSS_EXPOSURE_OBSERVATION_CHECKPOINT_SCHEMA = (
    "DAXLAB_LOSS_EXPOSURE_OBSERVATION_CHECKPOINT_V1"
)


class LossExposureCheckpointCompatibilityError(RuntimeError):
    """Raised when persisted observation state belongs to another policy."""


@dataclass(frozen=True, slots=True)
class LossExposureObservationCheckpoint:
    policy_fingerprint: str
    observation: LossExposureObservation
    observed_at: datetime
    checkpoint_fingerprint: str
    schema_version: str = LOSS_EXPOSURE_OBSERVATION_CHECKPOINT_SCHEMA
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != LOSS_EXPOSURE_OBSERVATION_CHECKPOINT_SCHEMA:
            raise ValueError("loss/exposure checkpoint schema mismatch")
        _require_sha256(self.policy_fingerprint, "policy_fingerprint")
        _require_aware(self.observed_at, "observed_at")
        _require_sha256(self.checkpoint_fingerprint, "checkpoint_fingerprint")
        if self.execution_capability != "NONE" or self.order_execution_enabled:
            raise ValueError("loss/exposure checkpoint cannot authorize execution")
        if self.checkpoint_fingerprint != _fingerprint(_identity_payload(self)):
            raise ValueError("loss/exposure checkpoint fingerprint mismatch")

    def to_dict(self) -> dict[str, object]:
        return _identity_payload(self) | {
            "checkpoint_fingerprint": self.checkpoint_fingerprint
        }


def build_loss_exposure_observation_checkpoint(
    *,
    policy_fingerprint: str,
    observation: LossExposureObservation,
    observed_at: datetime,
) -> LossExposureObservationCheckpoint:
    _require_sha256(policy_fingerprint, "policy_fingerprint")
    _require_aware(observed_at, "observed_at")
    observed_at_utc = observed_at.astimezone(timezone.utc)
    identity = _identity_values(
        schema_version=LOSS_EXPOSURE_OBSERVATION_CHECKPOINT_SCHEMA,
        policy_fingerprint=policy_fingerprint,
        observation=observation,
        observed_at=observed_at_utc,
        execution_capability="NONE",
        order_execution_enabled=False,
    )
    return LossExposureObservationCheckpoint(
        policy_fingerprint=policy_fingerprint,
        observation=observation,
        observed_at=observed_at_utc,
        checkpoint_fingerprint=_fingerprint(identity),
    )


def loss_exposure_checkpoint_to_bytes(
    checkpoint: LossExposureObservationCheckpoint,
) -> bytes:
    text = json.dumps(
        checkpoint.to_dict(),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return (text + "\n").encode("utf-8")


def loss_exposure_checkpoint_from_bytes(
    payload: bytes,
) -> LossExposureObservationCheckpoint:
    if not isinstance(payload, bytes):
        raise TypeError("loss/exposure checkpoint payload must be bytes")
    try:
        decoded = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("loss/exposure checkpoint must be valid UTF-8 JSON") from exc
    if not isinstance(decoded, dict):
        raise ValueError("loss/exposure checkpoint must be a JSON object")

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
        raise ValueError("loss/exposure checkpoint field set mismatch")

    raw_observation = decoded["observation"]
    if not isinstance(raw_observation, dict):
        raise ValueError("loss/exposure checkpoint observation must be object")
    observation_keys = {
        "schema_version",
        "currency",
        "daily_drawdown_cash",
        "weekly_drawdown_cash",
        "consecutive_losses",
        "open_positions",
        "observation_fingerprint",
    }
    if set(raw_observation) != observation_keys:
        raise ValueError("loss/exposure observation field set mismatch")

    observed_at_raw = decoded["observed_at_utc"]
    if not isinstance(observed_at_raw, str):
        raise ValueError("observed_at_utc must be ISO-8601 text")
    try:
        observed_at = datetime.fromisoformat(observed_at_raw)
    except ValueError as exc:
        raise ValueError("observed_at_utc must be ISO-8601 text") from exc
    _require_aware(observed_at, "observed_at_utc")

    observation = LossExposureObservation(
        currency=_text(raw_observation, "currency"),
        daily_drawdown_cash=_float(raw_observation, "daily_drawdown_cash"),
        weekly_drawdown_cash=_float(raw_observation, "weekly_drawdown_cash"),
        consecutive_losses=_int(raw_observation, "consecutive_losses"),
        open_positions=_int(raw_observation, "open_positions"),
        observation_fingerprint=_text(
            raw_observation,
            "observation_fingerprint",
        ),
        schema_version=_text(raw_observation, "schema_version"),
    )
    return LossExposureObservationCheckpoint(
        policy_fingerprint=_text(decoded, "policy_fingerprint"),
        observation=observation,
        observed_at=observed_at.astimezone(timezone.utc),
        checkpoint_fingerprint=_text(decoded, "checkpoint_fingerprint"),
        schema_version=_text(decoded, "schema_version"),
        execution_capability=_text(decoded, "execution_capability"),
        order_execution_enabled=_bool(decoded, "order_execution_enabled"),
    )


def save_loss_exposure_checkpoint(
    store: StateStorePort,
    key: str,
    checkpoint: LossExposureObservationCheckpoint,
) -> None:
    store.save(key, loss_exposure_checkpoint_to_bytes(checkpoint))


def load_loss_exposure_checkpoint(
    store: StateStorePort,
    key: str,
) -> LossExposureObservationCheckpoint | None:
    payload = store.load(key)
    if payload is None:
        return None
    return loss_exposure_checkpoint_from_bytes(payload)


def assert_loss_exposure_checkpoint_compatible(
    checkpoint: LossExposureObservationCheckpoint,
    *,
    policy_fingerprint: str,
) -> None:
    _require_sha256(policy_fingerprint, "policy_fingerprint")
    if checkpoint.policy_fingerprint != policy_fingerprint:
        raise LossExposureCheckpointCompatibilityError(
            "loss/exposure checkpoint policy fingerprint mismatch"
        )


def _identity_payload(
    checkpoint: LossExposureObservationCheckpoint,
) -> dict[str, object]:
    return _identity_values(
        schema_version=checkpoint.schema_version,
        policy_fingerprint=checkpoint.policy_fingerprint,
        observation=checkpoint.observation,
        observed_at=checkpoint.observed_at,
        execution_capability=checkpoint.execution_capability,
        order_execution_enabled=checkpoint.order_execution_enabled,
    )


def _identity_values(
    *,
    schema_version: str,
    policy_fingerprint: str,
    observation: LossExposureObservation,
    observed_at: datetime,
    execution_capability: str,
    order_execution_enabled: bool,
) -> dict[str, object]:
    return {
        "schema_version": schema_version,
        "policy_fingerprint": policy_fingerprint,
        "observation": {
            "schema_version": observation.schema_version,
            "currency": observation.currency,
            "daily_drawdown_cash": float(observation.daily_drawdown_cash),
            "weekly_drawdown_cash": float(observation.weekly_drawdown_cash),
            "consecutive_losses": observation.consecutive_losses,
            "open_positions": observation.open_positions,
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


def _text(payload: dict[str, Any], field_name: str) -> str:
    value = payload[field_name]
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field_name} must be non-empty text")
    return value


def _float(payload: dict[str, Any], field_name: str) -> float:
    value = payload[field_name]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be numeric")
    return float(value)


def _int(payload: dict[str, Any], field_name: str) -> int:
    value = payload[field_name]
    if type(value) is not int:
        raise ValueError(f"{field_name} must be integer")
    return value


def _bool(payload: dict[str, Any], field_name: str) -> bool:
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
