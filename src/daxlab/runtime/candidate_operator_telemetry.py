"""Pure validation contract for read-only CAND-001 operator telemetry.

This module contains no database, network, MT5 or execution capability. It
validates the already-built ``OperatorSnapshot.as_dict()`` payload before an
outer exporter may persist it as observation-only telemetry.
"""
from __future__ import annotations

from datetime import datetime
from math import isfinite
import re
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
        "database_url",
        "neon_database_url",
        "dsn",
        "connection_string",
        "authorization",
        "access_token",
        "refresh_token",
        "client_secret",
    }
)


def validate_candidate_operator_snapshot(payload: Mapping[str, Any]) -> None:
    """Fail closed unless payload is credential-free, coherent and order-disabled."""
    _assert_credential_free(payload)
    if payload.get("schema_version") != OPERATOR_SCHEMA:
        raise ValueError("unsupported Candidate operator snapshot schema")
    generated_at = operator_timestamp(payload.get("generated_at"), "generated_at")
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
        close_time = operator_timestamp(last_bar_close_time, "last_bar_close_time")
        if close_time > generated_at:
            raise ValueError("Candidate operator snapshot precedes last_bar_close_time")
        if type(freshness_seconds) not in (int, float) or not isfinite(freshness_seconds) or freshness_seconds < 0:
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


class CredentialEvidenceError(ValueError):
    """Bounded failure category; consumers must never publish raw evidence."""


def _assert_credential_free(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            normalized = re.sub(r"[^a-z0-9]", "", str(key).casefold())
            forbidden = {re.sub(r"[^a-z0-9]", "", k) for k in _FORBIDDEN_KEYS}
            if normalized in forbidden or normalized in {"apitoken", "privatekey", "secretkey"}:
                raise CredentialEvidenceError("forbidden Candidate telemetry field")
            _assert_credential_free(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_credential_free(item)
    elif isinstance(value, str) and re.search(
        r"(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?):\/\/"
        r"|https?:\/\/[^\s/]*@"
        r"|\bbearer\s+\S+"
        r"|(?:password|api[\s_-]?(?:key|token)|(?:access|refresh)[\s_-]?token|secret)\s*[:=]"
        r"|-----BEGIN [A-Z ]*PRIVATE KEY-----",
        value, re.IGNORECASE,
    ):
        raise CredentialEvidenceError("credential-bearing Candidate telemetry value")
    elif type(value) in (int, float) and not isfinite(value):
        raise ValueError("Candidate telemetry numbers must be finite")


def _assert_sha256(value: Any, *, field: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{field} must be sha256 hex")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field} must be sha256 hex") from exc


def operator_timestamp(value: Any, field: str) -> datetime:
    """Shared aware timestamp parser at the existing telemetry input boundary."""
    if not isinstance(value, str) or not value:
        raise ValueError(f"Candidate operator {field} missing")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"Candidate operator {field} invalid timestamp") from exc
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError(f"Candidate operator {field} must be timezone-aware")
    return result


def browser_operator_snapshot(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Display a validated V3 snapshot without passing arbitrary source text.

    Original snapshot/fingerprint remain source evidence. This DTO is a redacted
    display, not a new strategy owner or a persisted snapshot. Unknown text is
    suppressed structurally even when it has no recognizable secret pattern.
    """
    from copy import deepcopy
    from daxlab.runtime.candidate_config import Cand001Config
    from daxlab.runtime.candidate_signal import SignalReason, SignalDirection
    from daxlab.runtime.candidate_admission import AdmissionStatus
    from daxlab.runtime.candidate_virtual_lifecycle import VirtualPositionStatus

    validate_candidate_operator_snapshot(payload)
    display = deepcopy(dict(payload))
    cfg = Cand001Config()
    closed = {
        "strategy": {"regime": {cfg.regime_policy.value},
                     "structure": {f"{cfg.structure_rule.value}/OR{cfg.or_minutes}"},
                     "setup": {v.value for v in SignalReason}},
        "signal": {"direction": {v.value for v in SignalDirection},
                   "reason": {v.value for v in SignalReason}},
        "admission": {"status": {v.value for v in AdmissionStatus}},
        "decision": {"action": {"TRADE", "NO_TRADE"},
                     "risk_result": {"ADMITTED", "SESSION_LIMIT", "NOT_APPLICABLE"}},
        "runtime": {"health_state": {"GREEN", "YELLOW", "RED"},
                    "health_source": {"MT5_SHADOW_HOST", "CANDIDATE_INPUT"},
                    "recovery_state": {"FRESH_START", "RESUME_ANCHOR_RECONCILED", "RESUME_ANCHOR_NOT_FOUND"},
                    "reconciliation_state": {"IN_SYNC", "REPLAY_GAP_SAFE_TO_RESUME", "REPLAY_GAP_BLOCKED"}},
        "virtual_position": {"status": {v.value for v in VirtualPositionStatus},
                             "side": {"BUY", "SELL", "LONG", "SHORT"},
                             "exit_reason": {"STOP", "TARGET", "SESSION_END", "STOP_LOSS", "TAKE_PROFIT"}},
    }
    for section, fields in closed.items():
        for name, allowed in fields.items():
            value = display[section][name]
            if value is not None and value not in allowed:
                display[section][name] = "REDACTED_UNRECOGNIZED_TEXT"
    if (display["candidate_id"] != cfg.candidate_id
            or display["core_version"] != cfg.product_identity().core_version):
        raise ValueError("unsupported browser Candidate identity")
    codes = {v.value for v in SignalReason} | {
        "SESSION_TRADE_LIMIT", "DATA_UNSAFE", "INTENT_PUBLICATION_ADMITTED",
        "OUTCOME_PUBLICATION_ADMITTED", "OUTCOME_PUBLICATION_DUPLICATE_SUPPRESSED",
        "RESTART_CATCHUP", "PRIOR_ANCHOR_BARS_FILTERED", "REPLAY_GAP_DETECTED",
    }
    for section, name in (("runtime", "events"), ("decision", "blockers")):
        display[section][name] = [v if v in codes else "REDACTED_UNRECOGNIZED_TEXT"
                                 for v in display[section][name]]
    return display
