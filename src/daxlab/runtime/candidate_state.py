"""Hashed persistence envelopes for CAND-001 strategy and virtual lifecycle state.

File I/O deliberately stays in the existing atomic_json helper. This module only
serializes, validates and reconstructs candidate state. Strategy-pipeline state
and SHADOW virtual-lifecycle state remain separate semantic domains even though
they share the same persistence owner.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

from daxlab.core.execution import ExitReason
from daxlab.runtime.candidate_admission import Cand001AdmissionState
from daxlab.runtime.candidate_config import Cand001Config
from daxlab.runtime.candidate_pipeline import Cand001PipelineState
from daxlab.runtime.candidate_signal import Cand001SignalState
from daxlab.runtime.candidate_virtual_lifecycle import (
    Cand001VirtualLifecycleState,
    VirtualPositionStatus,
)
from daxlab.runtime.decision import stable_fingerprint
from daxlab.runtime.paper_contracts import Side


SCHEMA_VERSION = "DAX_BOT_CANDIDATE_STATE_V1"
VIRTUAL_STATE_SCHEMA_VERSION = "DAX_BOT_CANDIDATE_VIRTUAL_STATE_V1"
_VIRTUAL_LIFECYCLE_SCHEMA_VERSION = "DAXLAB_CAND001_VIRTUAL_LIFECYCLE_V1"
_ALLOWED_FIELDS = {
    "schema_version",
    "candidate_id",
    "core_version",
    "config_fingerprint",
    "state",
    "execution_capability",
    "order_execution_enabled",
    "payload_fingerprint",
}
_ALLOWED_VIRTUAL_FIELDS = {
    "schema_version",
    "lifecycle",
    "execution_capability",
    "order_execution_enabled",
    "payload_fingerprint",
}
_VIRTUAL_LIFECYCLE_FIELDS = {
    "schema_version",
    "lifecycle_id",
    "client_order_id",
    "decision_id",
    "run_manifest_fingerprint",
    "fill_model_fingerprint",
    "symbol",
    "side",
    "quantity",
    "requested_price",
    "stop_price",
    "target_price",
    "requested_at",
    "status",
    "filled_at",
    "filled_price",
    "closed_at",
    "exit_price",
    "exit_reason",
    "last_bar_id",
    "last_close_time",
    "execution_capability",
    "order_execution_enabled",
}


def candidate_state_payload(
    state: Cand001PipelineState,
    *,
    config: Cand001Config | None = None,
) -> dict[str, Any]:
    """Return a JSON-safe, provenance-bound persistence payload."""
    cfg = config or Cand001Config()
    identity = cfg.product_identity()
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "candidate_id": cfg.candidate_id,
        "core_version": identity.core_version,
        "config_fingerprint": identity.config_fingerprint,
        "state": _state_to_json(state),
        "execution_capability": "NONE",
        "order_execution_enabled": False,
    }
    payload["payload_fingerprint"] = stable_fingerprint(payload)
    return payload


def parse_candidate_state_payload(
    payload: Mapping[str, Any],
    *,
    config: Cand001Config | None = None,
) -> Cand001PipelineState:
    """Fail closed on schema/config/tamper drift and reconstruct pipeline state."""
    unknown = payload.keys() - _ALLOWED_FIELDS
    missing = _ALLOWED_FIELDS - payload.keys()
    if unknown:
        raise ValueError(f"unknown candidate-state fields: {sorted(unknown)}")
    if missing:
        raise ValueError(f"missing candidate-state fields: {sorted(missing)}")

    cfg = config or Cand001Config()
    identity = cfg.product_identity()
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("candidate-state schema mismatch")
    if payload.get("candidate_id") != cfg.candidate_id:
        raise ValueError("candidate-state candidate mismatch")
    if payload.get("core_version") != identity.core_version:
        raise ValueError("candidate-state core-version mismatch")
    if payload.get("config_fingerprint") != identity.config_fingerprint:
        raise ValueError("candidate-state config fingerprint mismatch")
    _require_disabled_execution(payload, "candidate-state")
    _verify_payload_fingerprint(payload, "candidate-state")

    raw_state = payload.get("state")
    if not isinstance(raw_state, Mapping):
        raise ValueError("candidate-state state object missing")
    return _state_from_json(raw_state)


def candidate_virtual_lifecycle_payload(
    state: Cand001VirtualLifecycleState,
) -> dict[str, Any]:
    """Return a tamper-evident JSON-safe envelope for one SHADOW virtual position."""
    payload: dict[str, Any] = {
        "schema_version": VIRTUAL_STATE_SCHEMA_VERSION,
        "lifecycle": _virtual_lifecycle_to_json(state),
        "execution_capability": "NONE",
        "order_execution_enabled": False,
    }
    payload["payload_fingerprint"] = stable_fingerprint(payload)
    return payload


def parse_candidate_virtual_lifecycle_payload(
    payload: Mapping[str, Any],
) -> Cand001VirtualLifecycleState:
    """Fail closed on tamper/schema/safety drift and restore one virtual position."""
    unknown = payload.keys() - _ALLOWED_VIRTUAL_FIELDS
    missing = _ALLOWED_VIRTUAL_FIELDS - payload.keys()
    if unknown:
        raise ValueError(f"unknown candidate virtual-state fields: {sorted(unknown)}")
    if missing:
        raise ValueError(f"missing candidate virtual-state fields: {sorted(missing)}")
    if payload.get("schema_version") != VIRTUAL_STATE_SCHEMA_VERSION:
        raise ValueError("candidate virtual-state schema mismatch")
    _require_disabled_execution(payload, "candidate virtual-state")
    _verify_payload_fingerprint(payload, "candidate virtual-state")

    raw = payload.get("lifecycle")
    if not isinstance(raw, Mapping):
        raise ValueError("candidate virtual-state lifecycle object missing")
    return _virtual_lifecycle_from_json(raw)


def _state_to_json(state: Cand001PipelineState) -> dict[str, Any]:
    return {
        "signal": {
            "session_date": state.signal.session_date,
            "or_high": state.signal.or_high,
            "or_low": state.signal.or_low,
            "or_slots": list(state.signal.or_slots),
            "last_close_time": (
                state.signal.last_close_time.isoformat()
                if state.signal.last_close_time is not None
                else None
            ),
        },
        "admission": {
            "session_date": state.admission.session_date,
            "trades_admitted": state.admission.trades_admitted,
        },
    }


def _state_from_json(raw: Mapping[str, Any]) -> Cand001PipelineState:
    if set(raw) != {"signal", "admission"}:
        raise ValueError("candidate-state object shape invalid")
    signal_raw = raw.get("signal")
    admission_raw = raw.get("admission")
    if not isinstance(signal_raw, Mapping) or not isinstance(admission_raw, Mapping):
        raise ValueError("candidate-state nested objects invalid")
    if set(signal_raw) != {
        "session_date",
        "or_high",
        "or_low",
        "or_slots",
        "last_close_time",
    }:
        raise ValueError("candidate signal-state shape invalid")
    if set(admission_raw) != {"session_date", "trades_admitted"}:
        raise ValueError("candidate admission-state shape invalid")

    raw_slots = signal_raw.get("or_slots")
    if not isinstance(raw_slots, list) or not all(isinstance(item, str) for item in raw_slots):
        raise ValueError("candidate signal-state or_slots invalid")
    raw_last_close = signal_raw.get("last_close_time")
    if raw_last_close is not None and not isinstance(raw_last_close, str):
        raise ValueError("candidate signal-state last_close_time invalid")
    last_close = _optional_datetime(raw_last_close, "signal.last_close_time")

    trades_admitted = admission_raw.get("trades_admitted")
    if type(trades_admitted) is not int:
        raise ValueError("candidate admission-state trades_admitted must be integer")

    signal_state = Cand001SignalState(
        session_date=_optional_str(signal_raw.get("session_date"), "signal.session_date"),
        or_high=_optional_number(signal_raw.get("or_high"), "signal.or_high"),
        or_low=_optional_number(signal_raw.get("or_low"), "signal.or_low"),
        or_slots=tuple(raw_slots),
        last_close_time=last_close,
    )
    admission_state = Cand001AdmissionState(
        session_date=_optional_str(
            admission_raw.get("session_date"),
            "admission.session_date",
        ),
        trades_admitted=trades_admitted,
    )
    return Cand001PipelineState(signal=signal_state, admission=admission_state)


def _virtual_lifecycle_to_json(state: Cand001VirtualLifecycleState) -> dict[str, Any]:
    return {
        "schema_version": state.schema_version,
        "lifecycle_id": state.lifecycle_id,
        "client_order_id": state.client_order_id,
        "decision_id": state.decision_id,
        "run_manifest_fingerprint": state.run_manifest_fingerprint,
        "fill_model_fingerprint": state.fill_model_fingerprint,
        "symbol": state.symbol,
        "side": state.side.value,
        "quantity": state.quantity,
        "requested_price": state.requested_price,
        "stop_price": state.stop_price,
        "target_price": state.target_price,
        "requested_at": state.requested_at.isoformat(),
        "status": state.status.value,
        "filled_at": state.filled_at.isoformat() if state.filled_at is not None else None,
        "filled_price": state.filled_price,
        "closed_at": state.closed_at.isoformat() if state.closed_at is not None else None,
        "exit_price": state.exit_price,
        "exit_reason": state.exit_reason.value,
        "last_bar_id": state.last_bar_id,
        "last_close_time": (
            state.last_close_time.isoformat() if state.last_close_time is not None else None
        ),
        "execution_capability": state.execution_capability,
        "order_execution_enabled": state.order_execution_enabled,
    }


def _virtual_lifecycle_from_json(raw: Mapping[str, Any]) -> Cand001VirtualLifecycleState:
    if set(raw) != _VIRTUAL_LIFECYCLE_FIELDS:
        raise ValueError("candidate virtual lifecycle shape invalid")
    if raw.get("schema_version") != _VIRTUAL_LIFECYCLE_SCHEMA_VERSION:
        raise ValueError("candidate virtual lifecycle schema mismatch")
    if raw.get("execution_capability") != "NONE" or raw.get("order_execution_enabled") is not False:
        raise ValueError("candidate virtual lifecycle cannot enable execution")

    lifecycle_id = _sha256_str(raw.get("lifecycle_id"), "lifecycle_id")
    client_order_id = _sha256_str(raw.get("client_order_id"), "client_order_id")
    decision_id = _sha256_str(raw.get("decision_id"), "decision_id")
    run_manifest = _sha256_str(
        raw.get("run_manifest_fingerprint"), "run_manifest_fingerprint"
    )
    fill_model = _sha256_str(raw.get("fill_model_fingerprint"), "fill_model_fingerprint")
    last_bar_id = raw.get("last_bar_id")
    if last_bar_id is not None:
        last_bar_id = _sha256_str(last_bar_id, "last_bar_id")

    symbol = raw.get("symbol")
    if not isinstance(symbol, str) or not symbol.strip():
        raise ValueError("candidate virtual lifecycle symbol invalid")
    side_raw = raw.get("side")
    status_raw = raw.get("status")
    exit_reason_raw = raw.get("exit_reason")
    if not isinstance(side_raw, str) or not isinstance(status_raw, str) or not isinstance(exit_reason_raw, str):
        raise ValueError("candidate virtual lifecycle enum field invalid")
    try:
        side = Side(side_raw)
        status = VirtualPositionStatus(status_raw)
        exit_reason = ExitReason(exit_reason_raw)
    except ValueError as exc:
        raise ValueError("candidate virtual lifecycle enum value invalid") from exc

    quantity = _required_positive_number(raw.get("quantity"), "quantity")
    requested_price = _required_positive_number(raw.get("requested_price"), "requested_price")
    stop_price = _required_positive_number(raw.get("stop_price"), "stop_price")
    target_price = _required_positive_number(raw.get("target_price"), "target_price")
    requested_at = _required_datetime(raw.get("requested_at"), "requested_at")
    filled_at = _optional_datetime(raw.get("filled_at"), "filled_at")
    closed_at = _optional_datetime(raw.get("closed_at"), "closed_at")
    last_close_time = _optional_datetime(raw.get("last_close_time"), "last_close_time")
    filled_price = _optional_number(raw.get("filled_price"), "filled_price")
    exit_price = _optional_number(raw.get("exit_price"), "exit_price")

    return Cand001VirtualLifecycleState(
        schema_version=_VIRTUAL_LIFECYCLE_SCHEMA_VERSION,
        lifecycle_id=lifecycle_id,
        client_order_id=client_order_id,
        decision_id=decision_id,
        run_manifest_fingerprint=run_manifest,
        fill_model_fingerprint=fill_model,
        symbol=symbol,
        side=side,
        quantity=quantity,
        requested_price=requested_price,
        stop_price=stop_price,
        target_price=target_price,
        requested_at=requested_at,
        status=status,
        filled_at=filled_at,
        filled_price=filled_price,
        closed_at=closed_at,
        exit_price=exit_price,
        exit_reason=exit_reason,
        last_bar_id=last_bar_id,
        last_close_time=last_close_time,
        execution_capability="NONE",
        order_execution_enabled=False,
    )


def _require_disabled_execution(payload: Mapping[str, Any], label: str) -> None:
    if payload.get("execution_capability") != "NONE":
        raise ValueError(f"{label} execution capability invalid")
    if payload.get("order_execution_enabled") is not False:
        raise ValueError(f"{label} cannot enable order execution")


def _verify_payload_fingerprint(payload: Mapping[str, Any], label: str) -> None:
    observed = payload.get("payload_fingerprint")
    if not isinstance(observed, str) or len(observed) != 64:
        raise ValueError(f"{label} payload fingerprint invalid")
    try:
        int(observed, 16)
    except ValueError as exc:
        raise ValueError(f"{label} payload fingerprint invalid") from exc
    unhashed = dict(payload)
    unhashed.pop("payload_fingerprint", None)
    if stable_fingerprint(unhashed) != observed:
        raise ValueError(f"{label} payload fingerprint mismatch")


def _sha256_str(value: Any, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{field} must be sha256 hex")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field} must be sha256 hex") from exc
    return value


def _required_datetime(value: Any, field: str) -> datetime:
    parsed = _optional_datetime(value, field)
    if parsed is None:
        raise ValueError(f"{field} must be timezone-aware datetime string")
    return parsed


def _optional_datetime(value: Any, field: str) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field} must be datetime string or null")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field} datetime invalid") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must be timezone-aware")
    return parsed


def _optional_str(value: Any, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field} must be string or null")
    return value


def _required_positive_number(value: Any, field: str) -> float:
    parsed = _optional_number(value, field)
    if parsed is None or parsed <= 0:
        raise ValueError(f"{field} must be positive numeric")
    return parsed


def _optional_number(value: Any, field: str) -> float | None:
    if value is None:
        return None
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{field} must be numeric or null")
    return float(value)
