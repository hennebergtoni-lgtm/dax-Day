"""Canonical deterministic codec for CAND-001 Strategy Plugin state.

Only the causal ``Cand001PipelineState`` fields are serialized. The format is
explicit JSON, not pickle or implementation-detail object serialization.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from typing import Any

from daxlab.runtime.candidate_admission import Cand001AdmissionState
from daxlab.runtime.candidate_pipeline import Cand001PipelineState
from daxlab.runtime.candidate_signal import Cand001SignalState


CAND001_STATE_SCHEMA = "DAXLAB_CAND001_PIPELINE_STATE_V1"
CAND001_STATE_CODEC_ID = "cand001-pipeline-state-json-v1"


class Cand001PipelineStateCodec:
    """Strict canonical JSON codec for ``Cand001PipelineState``."""

    codec_id = CAND001_STATE_CODEC_ID

    def encode(self, state: Cand001PipelineState) -> bytes:
        if not isinstance(state, Cand001PipelineState):
            raise TypeError("CAND-001 state codec requires Cand001PipelineState")
        payload = {
            "schema_version": CAND001_STATE_SCHEMA,
            "signal": {
                "session_date": state.signal.session_date,
                "or_high": state.signal.or_high,
                "or_low": state.signal.or_low,
                "or_slots": list(state.signal.or_slots),
                "last_close_time_utc": _encode_datetime(state.signal.last_close_time),
            },
            "admission": {
                "session_date": state.admission.session_date,
                "trades_admitted": state.admission.trades_admitted,
            },
        }
        text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return text.encode("utf-8")

    def decode(self, payload: bytes) -> Cand001PipelineState:
        if not isinstance(payload, bytes):
            raise TypeError("CAND-001 state payload must be bytes")
        try:
            value = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("CAND-001 state payload must be valid UTF-8 JSON") from exc
        if not isinstance(value, dict):
            raise ValueError("CAND-001 state payload must be a JSON object")
        _require_keys(value, {"schema_version", "signal", "admission"}, "root")
        if value["schema_version"] != CAND001_STATE_SCHEMA:
            raise ValueError("unsupported CAND-001 state schema")

        signal = _object(value["signal"], "signal")
        _require_keys(
            signal,
            {"session_date", "or_high", "or_low", "or_slots", "last_close_time_utc"},
            "signal",
        )
        admission = _object(value["admission"], "admission")
        _require_keys(admission, {"session_date", "trades_admitted"}, "admission")

        slots_raw = signal["or_slots"]
        if not isinstance(slots_raw, list) or any(not isinstance(item, str) for item in slots_raw):
            raise ValueError("signal.or_slots must be a string list")

        state = Cand001PipelineState(
            signal=Cand001SignalState(
                session_date=_optional_text(signal["session_date"], "signal.session_date"),
                or_high=_optional_number(signal["or_high"], "signal.or_high"),
                or_low=_optional_number(signal["or_low"], "signal.or_low"),
                or_slots=tuple(slots_raw),
                last_close_time=_decode_datetime(
                    signal["last_close_time_utc"],
                    "signal.last_close_time_utc",
                ),
            ),
            admission=Cand001AdmissionState(
                session_date=_optional_text(
                    admission["session_date"],
                    "admission.session_date",
                ),
                trades_admitted=_integer(
                    admission["trades_admitted"],
                    "admission.trades_admitted",
                ),
            ),
        )
        if self.encode(state) != payload:
            raise ValueError("CAND-001 state payload is not canonical")
        return state


def _encode_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        raise ValueError("CAND-001 last_close_time must be timezone-aware")
    return value.astimezone(timezone.utc).isoformat()


def _decode_datetime(value: Any, field_name: str) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be ISO UTC datetime or null")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be ISO UTC datetime or null") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise ValueError(f"{field_name} must be explicit UTC")
    canonical = parsed.astimezone(timezone.utc).isoformat()
    if value != canonical:
        raise ValueError(f"{field_name} must use canonical UTC ISO format")
    return parsed.astimezone(timezone.utc)


def _object(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be an object")
    return value


def _require_keys(value: dict[str, Any], expected: set[str], field_name: str) -> None:
    if set(value) != expected:
        raise ValueError(f"{field_name} field set mismatch")


def _optional_text(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"{field_name} must be normalized text or null")
    return value


def _optional_number(value: Any, field_name: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be numeric or null")
    return float(value)


def _integer(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be integer")
    return value
