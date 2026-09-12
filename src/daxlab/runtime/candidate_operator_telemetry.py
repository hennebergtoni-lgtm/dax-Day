"""Pure validation contract for read-only CAND-001 operator telemetry.

This module contains no database, network, MT5 or execution capability. It
validates the already-built ``OperatorSnapshot.as_dict()`` payload before an
outer exporter may persist it as observation-only telemetry.
"""
from __future__ import annotations

from typing import Any, Mapping

OPERATOR_SCHEMA = "DAX_BOT_OPERATOR_SNAPSHOT_V3"
_FORBIDDEN_KEYS = frozenset(
    {
        "login",
        "password",
        "token",
        "secret",
        "email",
        "phone",
        "account_id",
        "account_number",
        "api_key",
        "otp",
    }
)


def validate_candidate_operator_snapshot(payload: Mapping[str, Any]) -> None:
    """Fail closed unless payload is credential-free, coherent and order-disabled."""
    _assert_credential_free(payload)
    if payload.get("schema_version") != OPERATOR_SCHEMA:
        raise ValueError("unsupported Candidate operator snapshot schema")
    if not isinstance(payload.get("generated_at"), str) or not payload["generated_at"]:
        raise ValueError("Candidate operator generated_at must be non-empty")
    if not isinstance(payload.get("core_version"), str) or not payload["core_version"].strip():
        raise ValueError("Candidate operator core_version must be non-empty")
    if not isinstance(payload.get("candidate_id"), str) or not payload["candidate_id"].strip():
        raise ValueError("Candidate operator candidate_id must be non-empty")
    _assert_sha256(payload.get("config_fingerprint"), field="config_fingerprint")
    _assert_sha256(payload.get("snapshot_fingerprint"), field="snapshot_fingerprint")

    decision = _section(payload, "decision")
    runtime = _section(payload, "runtime")
    outcome = _section(payload, "outcome")
    safety = _section(payload, "safety")
    _section(payload, "virtual_position")

    _assert_sha256(decision.get("decision_id"), field="decision.decision_id")
    if decision.get("action") not in {"TRADE", "NO_TRADE"}:
        raise ValueError("Candidate operator decision action invalid")

    last_bar_id = runtime.get("last_bar_id")
    last_bar_close_time = runtime.get("last_bar_close_time")
    freshness_seconds = runtime.get("freshness_seconds")
    if last_bar_id is not None:
        _assert_sha256(last_bar_id, field="runtime.last_bar_id")
        if not isinstance(last_bar_close_time, str) or not last_bar_close_time:
            raise ValueError("Candidate operator last_bar_close_time missing")
        if not isinstance(freshness_seconds, (int, float)) or freshness_seconds < 0:
            raise ValueError("Candidate operator freshness_seconds invalid")
    elif last_bar_close_time is not None or freshness_seconds is not None:
        raise ValueError("Candidate operator runtime bar context incomplete")

    outcome_id = outcome.get("outcome_id")
    if outcome_id is not None:
        _assert_sha256(outcome_id, field="outcome.outcome_id")

    if safety.get("execution_capability") != "NONE":
        raise ValueError("Candidate operator execution capability must be NONE")
    if safety.get("order_execution_enabled") is not False:
        raise ValueError("Candidate operator order execution must be disabled")


def _section(payload: Mapping[str, Any], name: str) -> Mapping[str, Any]:
    section = payload.get(name)
    if not isinstance(section, Mapping):
        raise ValueError(f"Candidate operator {name} section must be an object")
    return section


def _assert_credential_free(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key).lower() in _FORBIDDEN_KEYS:
                raise ValueError(f"forbidden Candidate telemetry field: {key}")
            _assert_credential_free(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_credential_free(item)


def _assert_sha256(value: Any, *, field: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{field} must be sha256 hex")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field} must be sha256 hex") from exc
