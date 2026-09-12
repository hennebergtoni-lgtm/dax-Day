"""Deterministic broker-neutral checkpoint artifact for DAX-BOT NextGen.

The checkpoint binds replay/product provenance and opaque strategy-owned state.
Persistence is delegated only through ``StateStorePort``.  This module contains
no broker, MT5, order, candidate or host-runtime capability.
"""
from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any

from daxlab.domain.ports import StateStorePort


CHECKPOINT_SCHEMA = "DAXLAB_PRODUCT_CHECKPOINT_V1"


class CheckpointCompatibilityError(RuntimeError):
    """Raised when persisted state belongs to a different deterministic run identity."""


@dataclass(frozen=True, slots=True)
class ProductCheckpointV1:
    schema_version: str
    engine_version: str
    run_fingerprint: str
    strategy_id: str
    strategy_version: str
    strategy_fingerprint: str
    config_fingerprint: str
    source_commit: str
    instrument_id: str
    timeframe: str
    total_event_count: int
    input_fingerprint: str
    processed_event_count: int
    last_event_time: datetime | None
    last_decision_id: str | None
    decision_ids_fingerprint: str
    state_codec_id: str
    strategy_state_sha256: str
    strategy_state_b64: str
    checkpoint_fingerprint: str
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != CHECKPOINT_SCHEMA:
            raise ValueError("unsupported product checkpoint schema")
        for field_name, value in (
            ("engine_version", self.engine_version),
            ("strategy_id", self.strategy_id),
            ("strategy_version", self.strategy_version),
            ("instrument_id", self.instrument_id),
            ("timeframe", self.timeframe),
            ("state_codec_id", self.state_codec_id),
        ):
            _require_text(value, field_name)
        for field_name, value in (
            ("run_fingerprint", self.run_fingerprint),
            ("strategy_fingerprint", self.strategy_fingerprint),
            ("config_fingerprint", self.config_fingerprint),
            ("input_fingerprint", self.input_fingerprint),
            ("decision_ids_fingerprint", self.decision_ids_fingerprint),
            ("strategy_state_sha256", self.strategy_state_sha256),
            ("checkpoint_fingerprint", self.checkpoint_fingerprint),
        ):
            _require_sha256(value, field_name)
        _require_commit(self.source_commit)

        if self.total_event_count <= 0:
            raise ValueError("total_event_count must be positive")
        if not 0 <= self.processed_event_count <= self.total_event_count:
            raise ValueError("processed_event_count outside run bounds")
        if self.processed_event_count == 0:
            if self.last_event_time is not None or self.last_decision_id is not None:
                raise ValueError("zero-progress checkpoint cannot carry last-event identity")
        else:
            if self.last_event_time is None or self.last_decision_id is None:
                raise ValueError("processed checkpoint requires last-event and decision identity")
            _require_aware(self.last_event_time, "last_event_time")
            _require_sha256(self.last_decision_id, "last_decision_id")

        state_bytes = _decode_state(self.strategy_state_b64)
        if sha256(state_bytes).hexdigest() != self.strategy_state_sha256:
            raise ValueError("strategy state sha256 mismatch")
        if self.execution_capability != "NONE" or self.order_execution_enabled:
            raise ValueError("product checkpoint cannot authorize execution")
        if self.checkpoint_fingerprint != _fingerprint(_identity_payload(self)):
            raise ValueError("product checkpoint fingerprint mismatch")

    @property
    def strategy_state_bytes(self) -> bytes:
        return _decode_state(self.strategy_state_b64)

    def to_dict(self) -> dict[str, object]:
        return _identity_payload(self) | {"checkpoint_fingerprint": self.checkpoint_fingerprint}


def build_product_checkpoint(
    *,
    engine_version: str,
    run_fingerprint: str,
    strategy_id: str,
    strategy_version: str,
    strategy_fingerprint: str,
    config_fingerprint: str,
    source_commit: str,
    instrument_id: str,
    timeframe: str,
    total_event_count: int,
    input_fingerprint: str,
    processed_event_count: int,
    last_event_time: datetime | None,
    last_decision_id: str | None,
    decision_ids_fingerprint: str,
    state_codec_id: str,
    strategy_state: bytes,
) -> ProductCheckpointV1:
    """Build a deterministic checkpoint while keeping strategy-state bytes opaque."""

    if not isinstance(strategy_state, bytes):
        raise TypeError("strategy_state must be bytes")
    values = dict(
        schema_version=CHECKPOINT_SCHEMA,
        engine_version=engine_version,
        run_fingerprint=run_fingerprint,
        strategy_id=strategy_id,
        strategy_version=strategy_version,
        strategy_fingerprint=strategy_fingerprint,
        config_fingerprint=config_fingerprint,
        source_commit=source_commit,
        instrument_id=instrument_id,
        timeframe=timeframe,
        total_event_count=total_event_count,
        input_fingerprint=input_fingerprint,
        processed_event_count=processed_event_count,
        last_event_time=(
            last_event_time.astimezone(timezone.utc)
            if last_event_time is not None
            else None
        ),
        last_decision_id=last_decision_id,
        decision_ids_fingerprint=decision_ids_fingerprint,
        state_codec_id=state_codec_id,
        strategy_state_sha256=sha256(strategy_state).hexdigest(),
        strategy_state_b64=base64.b64encode(strategy_state).decode("ascii"),
    )
    return ProductCheckpointV1(
        **values,
        checkpoint_fingerprint=_fingerprint(_values_payload(**values)),
    )


def checkpoint_to_bytes(checkpoint: ProductCheckpointV1) -> bytes:
    """Return canonical UTF-8 bytes suitable for any ``StateStorePort`` backend."""

    text = json.dumps(
        checkpoint.to_dict(),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return (text + "\n").encode("utf-8")


def checkpoint_from_bytes(payload: bytes) -> ProductCheckpointV1:
    """Strictly parse and revalidate one persisted checkpoint payload."""

    if not isinstance(payload, bytes):
        raise TypeError("checkpoint payload must be bytes")
    try:
        decoded = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("checkpoint payload must be valid UTF-8 JSON") from exc
    if not isinstance(decoded, dict):
        raise ValueError("checkpoint payload must be a JSON object")
    expected_keys = {
        "schema_version",
        "engine_version",
        "run_fingerprint",
        "strategy_id",
        "strategy_version",
        "strategy_fingerprint",
        "config_fingerprint",
        "source_commit",
        "instrument_id",
        "timeframe",
        "total_event_count",
        "input_fingerprint",
        "processed_event_count",
        "last_event_time_utc",
        "last_decision_id",
        "decision_ids_fingerprint",
        "state_codec_id",
        "strategy_state_sha256",
        "strategy_state_b64",
        "execution_capability",
        "order_execution_enabled",
        "checkpoint_fingerprint",
    }
    if set(decoded) != expected_keys:
        raise ValueError("checkpoint payload field set mismatch")

    last_event_raw = decoded["last_event_time_utc"]
    last_event_time: datetime | None = None
    if last_event_raw is not None:
        if not isinstance(last_event_raw, str):
            raise ValueError("last_event_time_utc must be ISO datetime or null")
        try:
            last_event_time = datetime.fromisoformat(last_event_raw)
        except ValueError as exc:
            raise ValueError("last_event_time_utc must be ISO datetime or null") from exc

    return ProductCheckpointV1(
        schema_version=_text(decoded, "schema_version"),
        engine_version=_text(decoded, "engine_version"),
        run_fingerprint=_text(decoded, "run_fingerprint"),
        strategy_id=_text(decoded, "strategy_id"),
        strategy_version=_text(decoded, "strategy_version"),
        strategy_fingerprint=_text(decoded, "strategy_fingerprint"),
        config_fingerprint=_text(decoded, "config_fingerprint"),
        source_commit=_text(decoded, "source_commit"),
        instrument_id=_text(decoded, "instrument_id"),
        timeframe=_text(decoded, "timeframe"),
        total_event_count=_int(decoded, "total_event_count"),
        input_fingerprint=_text(decoded, "input_fingerprint"),
        processed_event_count=_int(decoded, "processed_event_count"),
        last_event_time=last_event_time,
        last_decision_id=_optional_text(decoded, "last_decision_id"),
        decision_ids_fingerprint=_text(decoded, "decision_ids_fingerprint"),
        state_codec_id=_text(decoded, "state_codec_id"),
        strategy_state_sha256=_text(decoded, "strategy_state_sha256"),
        strategy_state_b64=_text(decoded, "strategy_state_b64", allow_empty=True),
        checkpoint_fingerprint=_text(decoded, "checkpoint_fingerprint"),
        execution_capability=_text(decoded, "execution_capability"),
        order_execution_enabled=_bool(decoded, "order_execution_enabled"),
    )


def save_checkpoint(store: StateStorePort, key: str, checkpoint: ProductCheckpointV1) -> None:
    store.save(key, checkpoint_to_bytes(checkpoint))


def load_checkpoint(store: StateStorePort, key: str) -> ProductCheckpointV1 | None:
    payload = store.load(key)
    if payload is None:
        return None
    return checkpoint_from_bytes(payload)


def assert_checkpoint_compatible(
    checkpoint: ProductCheckpointV1,
    *,
    engine_version: str,
    run_fingerprint: str,
    strategy_id: str,
    strategy_version: str,
    strategy_fingerprint: str,
    config_fingerprint: str,
    source_commit: str,
    input_fingerprint: str,
) -> None:
    """Fail closed before a caller trusts checkpoint state for deterministic resume."""

    expected = {
        "engine_version": engine_version,
        "run_fingerprint": run_fingerprint,
        "strategy_id": strategy_id,
        "strategy_version": strategy_version,
        "strategy_fingerprint": strategy_fingerprint,
        "config_fingerprint": config_fingerprint,
        "source_commit": source_commit,
        "input_fingerprint": input_fingerprint,
    }
    for field_name, expected_value in expected.items():
        if getattr(checkpoint, field_name) != expected_value:
            raise CheckpointCompatibilityError(f"checkpoint {field_name} mismatch")


def _identity_payload(checkpoint: ProductCheckpointV1) -> dict[str, object]:
    return _values_payload(
        schema_version=checkpoint.schema_version,
        engine_version=checkpoint.engine_version,
        run_fingerprint=checkpoint.run_fingerprint,
        strategy_id=checkpoint.strategy_id,
        strategy_version=checkpoint.strategy_version,
        strategy_fingerprint=checkpoint.strategy_fingerprint,
        config_fingerprint=checkpoint.config_fingerprint,
        source_commit=checkpoint.source_commit,
        instrument_id=checkpoint.instrument_id,
        timeframe=checkpoint.timeframe,
        total_event_count=checkpoint.total_event_count,
        input_fingerprint=checkpoint.input_fingerprint,
        processed_event_count=checkpoint.processed_event_count,
        last_event_time=checkpoint.last_event_time,
        last_decision_id=checkpoint.last_decision_id,
        decision_ids_fingerprint=checkpoint.decision_ids_fingerprint,
        state_codec_id=checkpoint.state_codec_id,
        strategy_state_sha256=checkpoint.strategy_state_sha256,
        strategy_state_b64=checkpoint.strategy_state_b64,
    )


def _values_payload(
    *,
    schema_version: str,
    engine_version: str,
    run_fingerprint: str,
    strategy_id: str,
    strategy_version: str,
    strategy_fingerprint: str,
    config_fingerprint: str,
    source_commit: str,
    instrument_id: str,
    timeframe: str,
    total_event_count: int,
    input_fingerprint: str,
    processed_event_count: int,
    last_event_time: datetime | None,
    last_decision_id: str | None,
    decision_ids_fingerprint: str,
    state_codec_id: str,
    strategy_state_sha256: str,
    strategy_state_b64: str,
) -> dict[str, object]:
    return {
        "schema_version": schema_version,
        "engine_version": engine_version,
        "run_fingerprint": run_fingerprint,
        "strategy_id": strategy_id,
        "strategy_version": strategy_version,
        "strategy_fingerprint": strategy_fingerprint,
        "config_fingerprint": config_fingerprint,
        "source_commit": source_commit,
        "instrument_id": instrument_id,
        "timeframe": timeframe,
        "total_event_count": total_event_count,
        "input_fingerprint": input_fingerprint,
        "processed_event_count": processed_event_count,
        "last_event_time_utc": (
            last_event_time.astimezone(timezone.utc).isoformat()
            if last_event_time is not None
            else None
        ),
        "last_decision_id": last_decision_id,
        "decision_ids_fingerprint": decision_ids_fingerprint,
        "state_codec_id": state_codec_id,
        "strategy_state_sha256": strategy_state_sha256,
        "strategy_state_b64": strategy_state_b64,
        "execution_capability": "NONE",
        "order_execution_enabled": False,
    }


def _decode_state(value: str) -> bytes:
    if not isinstance(value, str):
        raise ValueError("strategy_state_b64 must be text")
    try:
        return base64.b64decode(value.encode("ascii"), validate=True)
    except (UnicodeEncodeError, binascii.Error) as exc:
        raise ValueError("strategy_state_b64 must be canonical base64") from exc


def _fingerprint(value: object) -> str:
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256(canonical.encode("utf-8")).hexdigest()


def _require_text(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"{field_name} must be normalized non-empty text")


def _require_sha256(value: str, field_name: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{field_name} must be sha256 hex")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be sha256 hex") from exc


def _require_commit(value: str) -> None:
    if not isinstance(value, str) or len(value) != 40:
        raise ValueError("source_commit must be a full 40-character Git SHA")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError("source_commit must be hex") from exc


def _require_aware(value: datetime, field_name: str) -> None:
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")


def _text(payload: dict[str, Any], field_name: str, *, allow_empty: bool = False) -> str:
    value = payload[field_name]
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be text")
    if not allow_empty and not value:
        raise ValueError(f"{field_name} must be non-empty")
    return value


def _optional_text(payload: dict[str, Any], field_name: str) -> str | None:
    value = payload[field_name]
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be text or null")
    return value


def _int(payload: dict[str, Any], field_name: str) -> int:
    value = payload[field_name]
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be integer")
    return value


def _bool(payload: dict[str, Any], field_name: str) -> bool:
    value = payload[field_name]
    if not isinstance(value, bool):
        raise ValueError(f"{field_name} must be boolean")
    return value
