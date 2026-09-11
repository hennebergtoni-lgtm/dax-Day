"""Hashed persistence envelope for the pure CAND-001 pipeline state.

File I/O deliberately stays in the existing atomic_json helper. This module only
serializes, validates and reconstructs candidate state.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

from daxlab.runtime.candidate_admission import Cand001AdmissionState
from daxlab.runtime.candidate_config import Cand001Config
from daxlab.runtime.candidate_pipeline import Cand001PipelineState
from daxlab.runtime.candidate_signal import Cand001SignalState
from daxlab.runtime.decision import stable_fingerprint


SCHEMA_VERSION = "DAX_BOT_CANDIDATE_STATE_V1"
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
    if payload.get("execution_capability") != "NONE":
        raise ValueError("candidate-state execution capability invalid")
    if payload.get("order_execution_enabled") is not False:
        raise ValueError("candidate-state cannot enable order execution")

    observed_fingerprint = payload.get("payload_fingerprint")
    if not isinstance(observed_fingerprint, str) or len(observed_fingerprint) != 64:
        raise ValueError("candidate-state payload fingerprint invalid")
    try:
        int(observed_fingerprint, 16)
    except ValueError as exc:
        raise ValueError("candidate-state payload fingerprint invalid") from exc
    unhashed = dict(payload)
    unhashed.pop("payload_fingerprint", None)
    if stable_fingerprint(unhashed) != observed_fingerprint:
        raise ValueError("candidate-state payload fingerprint mismatch")

    raw_state = payload.get("state")
    if not isinstance(raw_state, Mapping):
        raise ValueError("candidate-state state object missing")
    return _state_from_json(raw_state)


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
    last_close = datetime.fromisoformat(raw_last_close) if raw_last_close is not None else None
    if last_close is not None and last_close.tzinfo is None:
        raise ValueError("candidate signal-state last_close_time must be timezone-aware")

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


def _optional_str(value: Any, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field} must be string or null")
    return value


def _optional_number(value: Any, field: str) -> float | None:
    if value is None:
        return None
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{field} must be numeric or null")
    return float(value)
