"""Fail-closed scope contract for separately authorized DEMO evidence acquisition.

This module does not submit broker orders and does not create PAPER/LIVE authority.
A positive verdict only proves that one requested evidence action matches an explicit
demo-only scope grant and the currently observed account context.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from hashlib import sha256
import json
from typing import Any


DEMO_EVIDENCE_AUTHORIZATION_SCHEMA = "DAXLAB_DEMO_EVIDENCE_AUTHORIZATION_V1"
DEMO_EVIDENCE_PURPOSE = "DEMO_EVIDENCE_ACQUISITION_ONLY"


class DemoAccountMode(StrEnum):
    DEMO = "DEMO"
    CONTEST = "CONTEST"
    REAL = "REAL"
    UNKNOWN = "UNKNOWN"


class DemoEvidenceAction(StrEnum):
    SUBMIT_EVIDENCE_ORDER = "SUBMIT_EVIDENCE_ORDER"
    QUERY_EVIDENCE_ORDER = "QUERY_EVIDENCE_ORDER"
    CANCEL_EVIDENCE_ORDER = "CANCEL_EVIDENCE_ORDER"


class DemoEvidenceAuthorizationStatus(StrEnum):
    SCOPE_VALID = "SCOPE_VALID"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True, slots=True)
class DemoEvidenceAuthorization:
    schema_version: str
    authorization_id: str
    account_id: str
    server: str
    symbol: str
    valid_from: datetime
    expires_at: datetime
    allowed_actions: tuple[DemoEvidenceAction, ...]
    max_submissions: int
    purpose: str = DEMO_EVIDENCE_PURPOSE
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != DEMO_EVIDENCE_AUTHORIZATION_SCHEMA:
            raise ValueError("demo evidence authorization schema mismatch")
        _nonempty(self.authorization_id, "authorization_id")
        _nonempty(self.account_id, "account_id")
        _nonempty(self.server, "server")
        _nonempty(self.symbol, "symbol")
        _aware(self.valid_from, "valid_from")
        _aware(self.expires_at, "expires_at")
        if self.expires_at <= self.valid_from:
            raise ValueError("expires_at must be after valid_from")
        if not self.allowed_actions:
            raise ValueError("allowed_actions must not be empty")
        if any(not isinstance(action, DemoEvidenceAction) for action in self.allowed_actions):
            raise ValueError("allowed_actions must contain DemoEvidenceAction values")
        if len(set(self.allowed_actions)) != len(self.allowed_actions):
            raise ValueError("allowed_actions must not contain duplicates")
        if (
            not isinstance(self.max_submissions, int)
            or isinstance(self.max_submissions, bool)
            or self.max_submissions < 1
        ):
            raise ValueError("max_submissions must be an integer >= 1")
        if self.purpose != DEMO_EVIDENCE_PURPOSE:
            raise ValueError("demo evidence authorization purpose mismatch")
        if self.execution_capability != "NONE" or self.order_execution_enabled:
            raise ValueError("demo evidence authorization cannot grant execution")

    @property
    def fingerprint(self) -> str:
        return _fingerprint(
            {
                "schema_version": self.schema_version,
                "authorization_id": self.authorization_id,
                "account_id": self.account_id,
                "server": self.server,
                "symbol": self.symbol,
                "valid_from": _iso(self.valid_from),
                "expires_at": _iso(self.expires_at),
                "allowed_actions": [action.value for action in self.allowed_actions],
                "max_submissions": self.max_submissions,
                "purpose": self.purpose,
                "execution_capability": self.execution_capability,
                "order_execution_enabled": self.order_execution_enabled,
            }
        )


@dataclass(frozen=True, slots=True)
class DemoEvidenceObservedContext:
    account_id: str
    server: str
    symbol: str
    account_mode: DemoAccountMode
    trade_allowed: bool

    def __post_init__(self) -> None:
        _nonempty(self.account_id, "account_id")
        _nonempty(self.server, "server")
        _nonempty(self.symbol, "symbol")
        if not isinstance(self.account_mode, DemoAccountMode):
            raise ValueError("account_mode must be DemoAccountMode")
        if not isinstance(self.trade_allowed, bool):
            raise ValueError("trade_allowed must be bool")


@dataclass(frozen=True, slots=True)
class DemoEvidenceAuthorizationVerdict:
    status: DemoEvidenceAuthorizationStatus
    blockers: tuple[str, ...]
    authorization_fingerprint: str | None
    requested_action: DemoEvidenceAction
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.execution_capability != "NONE" or self.order_execution_enabled:
            raise ValueError("demo evidence verdict cannot grant execution")
        if self.status is DemoEvidenceAuthorizationStatus.SCOPE_VALID and self.blockers:
            raise ValueError("scope-valid verdict cannot carry blockers")
        if self.status is DemoEvidenceAuthorizationStatus.BLOCKED and not self.blockers:
            raise ValueError("blocked verdict requires blockers")

    @property
    def scope_valid(self) -> bool:
        return self.status is DemoEvidenceAuthorizationStatus.SCOPE_VALID


def evaluate_demo_evidence_authorization(
    *,
    authorization: DemoEvidenceAuthorization | object,
    observed: DemoEvidenceObservedContext,
    requested_action: DemoEvidenceAction,
    evaluated_at: datetime,
    submissions_already_attempted: int,
) -> DemoEvidenceAuthorizationVerdict:
    """Validate one demo-evidence scope without creating execution authority."""

    _aware(evaluated_at, "evaluated_at")
    if submissions_already_attempted < 0:
        raise ValueError("submissions_already_attempted must be >= 0")

    if not isinstance(authorization, DemoEvidenceAuthorization):
        return _blocked(
            requested_action,
            None,
            "DEMO_EVIDENCE_AUTHORIZATION_TYPE_INVALID",
        )

    blockers: list[str] = []

    if observed.account_mode is not DemoAccountMode.DEMO:
        blockers.append(f"ACCOUNT_MODE_{observed.account_mode.value}_BLOCKED")
    if not observed.trade_allowed:
        blockers.append("ACCOUNT_TRADE_NOT_ALLOWED")

    if authorization.account_id != observed.account_id:
        blockers.append("ACCOUNT_ID_MISMATCH")
    if authorization.server != observed.server:
        blockers.append("SERVER_MISMATCH")
    if authorization.symbol != observed.symbol:
        blockers.append("SYMBOL_MISMATCH")

    if evaluated_at < authorization.valid_from:
        blockers.append("AUTHORIZATION_NOT_YET_VALID")
    if evaluated_at >= authorization.expires_at:
        blockers.append("AUTHORIZATION_EXPIRED")

    if requested_action not in authorization.allowed_actions:
        blockers.append("ACTION_OUT_OF_SCOPE")

    if (
        requested_action is DemoEvidenceAction.SUBMIT_EVIDENCE_ORDER
        and submissions_already_attempted >= authorization.max_submissions
    ):
        blockers.append("SUBMISSION_LIMIT_REACHED")

    if blockers:
        return _blocked(
            requested_action,
            authorization.fingerprint,
            *blockers,
        )

    return DemoEvidenceAuthorizationVerdict(
        status=DemoEvidenceAuthorizationStatus.SCOPE_VALID,
        blockers=(),
        authorization_fingerprint=authorization.fingerprint,
        requested_action=requested_action,
    )


def _blocked(
    requested_action: DemoEvidenceAction,
    authorization_fingerprint: str | None,
    *blockers: str,
) -> DemoEvidenceAuthorizationVerdict:
    return DemoEvidenceAuthorizationVerdict(
        status=DemoEvidenceAuthorizationStatus.BLOCKED,
        blockers=tuple(blockers),
        authorization_fingerprint=authorization_fingerprint,
        requested_action=requested_action,
    )


def _nonempty(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be non-empty")


def _aware(value: datetime, field: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _fingerprint(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()
