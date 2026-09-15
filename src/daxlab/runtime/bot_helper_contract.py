"""Closed immutable observation envelopes; no I/O, policy or execution authority.

Only a trusted source adapter assigns scope. Parsing proves structural/integrity
properties, never authenticity. IDs identify observations; hashes identify content.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
import json
import re

from daxlab.domain.market import InstrumentId

SCHEMA = "DAXLAB_BOT_HELPER_EVENT_V1"
ROLES = ("H", "D", "B", "S", "O")
OWNERS = {
    "H": "WINDOWS_HOST_RUNTIME", "D": "CANONICAL_DATA_QUALITY",
    "B": "BROKER_RECOVERY_OBSERVATION", "S": "INDEPENDENT_PRETRADE_CONTROLS",
    "O": "CANONICAL_EVIDENCE_PUBLISHER",
}
SCOPES = frozenset({"SYNTHETIC", "REPLAY", "REAL_HOST", "REAL_BROKER_READ"})
STATUSES = frozenset({"PASS", "FAIL", "BLOCKED", "UNKNOWN"})
REASONS = frozenset({
    "HOST_UNKNOWN", "HOST_BLOCKED", "BROKER_UNKNOWN", "INVENTORY_CONFLICT",
    "BROKER_READ_FAILED", "READINESS_BLOCKED",
    "UNRESOLVED_STATE", "ACK_NOT_FILL", "HISTORY_INCOMPLETE", "QUERY_REQUIRED",
    "PROTECTION_UNKNOWN", "PERSISTENCE_BLOCKED", "PUBLICATION_FAILED",
    "READBACK_FAILED", "HELPER_FAILED", "DEPENDENCY_MISSING", "IDENTITY_MISMATCH",
    "CONTRADICTION", "EVENT_OVERFLOW", "DEPENDENCY_CYCLE", "ROUTING_DEPTH",
    "CLOCK_ROLLBACK", "SOURCE_FUTURE", "SOURCE_STALE", "FRESHNESS_UNKNOWN",
    "SOURCE_ORDER", "PRODUCER_EPOCH_CHANGED", "DATA_INVALID", "DATA_REVISION",
    "DATA_STALE", "DATA_GAP", "DATA_DUPLICATE", "DATA_OUT_OF_ORDER",
    "DATA_CLOCK_SKEW", "DATA_SOURCE_DISAGREEMENT", "DATA_UNSAFE",
    "PTC_HARD_LIVE_OR_UNKNOWN_ENVIRONMENT_BLOCK", "PTC_ACCOUNT_VETO",
    "PTC_INSTRUMENT_VETO", "PTC_EXISTING_PROTECTION_BLOCKED",
    "PTC_QUANTITY_BOUND_VETO", "PTC_NATIVE_QUANTITY_GRID_VETO",
    "PTC_NATIVE_PRICE_GRID_VETO", "PTC_PRICE_COLLAR_VETO",
    "PTC_NOTIONAL_BOUND_VETO", "PTC_STALE_PRICE_VETO", "PTC_ATTEMPT_BOUND_VETO",
    "PTC_DUPLICATE_VETO", "PTC_INVENTORY_VETO", "PTC_SESSION_VETO",
    "PTC_UNKNOWN_RESERVATION_QUERY_REQUIRED", "PTC_EMERGENCY_AUTHORITY_LATCHED",
})


def digest(value: object) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=True, allow_nan=False).encode("utf-8")).hexdigest()


def require_sha(value: object, size: int = 64) -> None:
    if type(value) is not str or re.fullmatch(r"[0-9a-f]{%d}" % size, value) is None:
        raise ValueError("HELPER_INVALID_FINGERPRINT")


def utc(value: datetime) -> str:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("HELPER_INVALID_CLOCK")
    return value.astimezone(timezone.utc).isoformat()


def read_utc(value: object) -> datetime:
    if type(value) is not str:
        raise ValueError("HELPER_INVALID_CLOCK")
    try:
        parsed = datetime.fromisoformat(value)
        if parsed.utcoffset() != timedelta(0):
            raise ValueError
        return parsed
    except (ValueError, TypeError):
        raise ValueError("HELPER_INVALID_CLOCK") from None


@dataclass(frozen=True, slots=True)
class HelperSubject:
    run_id: str
    provider: str
    environment: str
    account_fingerprint: str | None
    instrument_id: InstrumentId
    market_contract_fingerprint: str | None
    session_id: str | None
    code_head: str | None
    config_fingerprint: str | None
    instrument_identity_fingerprint: str | None = None
    risk_policy_fingerprint: str | None = None

    def __post_init__(self) -> None:
        for value in (self.run_id, self.market_contract_fingerprint, self.config_fingerprint,
                      self.instrument_identity_fingerprint, self.risk_policy_fingerprint):
            if value is not None:
                require_sha(value)
        require_sha(self.run_id)
        if self.code_head is not None:
            require_sha(self.code_head, 40)
        if self.account_fingerprint is not None:
            require_sha(self.account_fingerprint)
        if self.provider not in {"IG", "MT5", "SYNTHETIC", "REPLAY"}:
            raise ValueError("HELPER_INVALID_PROVIDER")
        if self.environment not in {"DEMO", "SHADOW", "REPLAY"}:
            raise ValueError("HELPER_INVALID_ENVIRONMENT")
        if not isinstance(self.instrument_id, InstrumentId):
            raise ValueError("HELPER_INVALID_INSTRUMENT")
        # Identity remains opaque. Transport only safe bounded identifiers, never URLs.
        if re.fullmatch(r"[A-Za-z0-9_.-]{1,80}", self.instrument_id.value) is None:
            raise ValueError("HELPER_INVALID_INSTRUMENT")
        try:
            if self.session_id is not None and date.fromisoformat(self.session_id).isoformat() != self.session_id:
                raise ValueError
        except (TypeError, ValueError):
            raise ValueError("HELPER_INVALID_SESSION") from None

    def as_dict(self) -> dict:
        return {**asdict(self), "instrument_id": self.instrument_id.value}


@dataclass(frozen=True, slots=True)
class HelperEvent:
    subject: HelperSubject
    source_role: str
    status: str
    source_time: str
    observed_at: str
    valid_until: str | None
    evidence_scope: str
    reason_codes: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    dependency_event_ids: tuple[str, ...] = ()
    source_sequence: int = 0
    producer_epoch: str = "0" * 64
    truth_status: str = "UNKNOWN"
    verification_method: str | None = None
    evidence_schema: str | None = None
    correlation_id: str | None = None
    causation_id: str | None = None
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        if type(self.subject) is not HelperSubject or self.source_role not in ROLES:
            raise ValueError("HELPER_INVALID_OWNER")
        if self.status not in STATUSES or self.evidence_scope not in SCOPES:
            raise ValueError("HELPER_INVALID_STATUS_OR_SCOPE")
        if self.evidence_scope in {"REAL_HOST", "REAL_BROKER_READ"} and self.subject.provider in {"SYNTHETIC", "REPLAY"}:
            raise ValueError("HELPER_SCOPE_CONTRADICTION")
        if self.truth_status not in {"VERIFIED", "UNVERIFIED", "UNKNOWN"}:
            raise ValueError("HELPER_INVALID_TRUTH")
        if self.execution_capability != "NONE" or self.order_execution_enabled is not False:
            raise ValueError("HELPER_EXECUTION_FORBIDDEN")
        if type(self.execution_capability) is not str:
            raise ValueError("HELPER_EXECUTION_FORBIDDEN")
        start, observed = read_utc(self.source_time), read_utc(self.observed_at)
        if start > observed:
            raise ValueError("HELPER_SOURCE_FUTURE")
        if self.valid_until is not None and read_utc(self.valid_until) < start:
            raise ValueError("HELPER_INVALID_VALIDITY")
        require_sha(self.producer_epoch)
        if type(self.source_sequence) is not int or not 0 <= self.source_sequence < 2**63:
            raise ValueError("HELPER_INVALID_SEQUENCE")
        for values in (self.reason_codes, self.evidence_refs, self.dependency_event_ids):
            if type(values) is not tuple:
                raise ValueError("HELPER_MUTABLE_COLLECTION")
        if len(self.dependency_event_ids) > 32 or len(self.evidence_refs) > 32:
            raise ValueError("HELPER_DEPENDENCY_OVERFLOW")
        if len(self.reason_codes) > 64 or any(code not in REASONS for code in self.reason_codes):
            raise ValueError("HELPER_UNKNOWN_REASON")
        for ref in (*self.evidence_refs, *self.dependency_event_ids):
            require_sha(ref)
        for ref in (self.correlation_id, self.causation_id):
            if ref is not None:
                require_sha(ref)
        if self.verification_method not in {None, "CANONICAL_OWNER_VALIDATION", "STRUCTURAL_VALIDATION"}:
            raise ValueError("HELPER_INVALID_VERIFICATION_METHOD")
        if self.evidence_schema not in {None, "CLOSED_CANDLE_V1", "DAXLAB_IG_PREDEMO_READINESS_V3",
                                        "DAX_INDEPENDENT_PTC_DIAGNOSTIC_V1", "SYNTHETIC_FIXTURE_V1"}:
            raise ValueError("HELPER_INVALID_EVIDENCE_SCHEMA")
        if self.truth_status == "VERIFIED" and (not self.evidence_refs
                or self.verification_method is None or self.subject.code_head is None
                or self.subject.market_contract_fingerprint is None or self.evidence_schema is None):
            raise ValueError("HELPER_VERIFIED_REQUIRES_EVIDENCE")
        if self.status == "PASS" and self.reason_codes:
            raise ValueError("HELPER_PASS_WITH_BLOCKER")
        if len(json.dumps(self._body(), ensure_ascii=True).encode()) > 64 * 1024:
            raise ValueError("HELPER_ENVELOPE_OVERFLOW")

    @property
    def event_id(self) -> str:
        return digest({"subject": self.subject.as_dict(), "owner": OWNERS[self.source_role],
                       "source_time": self.source_time, "epoch": self.producer_epoch,
                       "sequence": self.source_sequence})

    def _body(self) -> dict:
        return {**asdict(self), "subject": self.subject.as_dict(), "schema_version": SCHEMA,
                "event_type": "OWNER_OBSERVATION", "source_owner": OWNERS[self.source_role]}

    @property
    def payload_hash(self) -> str:
        return digest(self._body())

    def as_dict(self) -> dict:
        return json.loads(json.dumps({**self._body(), "event_id": self.event_id,
                                      "payload_hash": self.payload_hash}))


def observation(subject: HelperSubject, role: str, status: str, *, source_time: datetime,
                observed_at: datetime, valid_until: datetime | None,
                evidence_scope: str, **kwargs) -> HelperEvent:
    """Trusted owner adapter factory, not an untrusted provenance assertion."""
    return HelperEvent(subject, role, status, utc(source_time), utc(observed_at),
                       utc(valid_until) if valid_until is not None else None,
                       evidence_scope, **kwargs)


def parse_event(raw: str, *, evidence_scope: str) -> HelperEvent:
    """Read an immutable event with caller-owned scope; reject unknown/duplicate keys."""
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("HELPER_DUPLICATE_KEY")
            result[key] = value
        return result

    try:
        if type(raw) is not str or len(raw.encode()) > 64 * 1024:
            raise ValueError
        data = json.loads(raw, object_pairs_hook=pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
        if not isinstance(data, dict) or data.get("evidence_scope") != evidence_scope:
            raise ValueError
        subject = data["subject"]
        if type(subject) is not dict or type(subject.get("instrument_id")) is not str:
            raise ValueError
        event_subject = HelperSubject(**{**subject, "instrument_id": InstrumentId(subject["instrument_id"])})
        body = {k: v for k, v in data.items() if k not in {
            "subject", "schema_version", "event_type", "source_owner", "event_id", "payload_hash"}}
        for name in ("reason_codes", "evidence_refs", "dependency_event_ids"):
            if type(body[name]) is not list:
                raise ValueError
            body[name] = tuple(body[name])
        result = HelperEvent(subject=event_subject, **body)
        if data != result.as_dict():
            raise ValueError
        return result
    except (KeyError, ValueError, TypeError, OverflowError, RecursionError):
        raise ValueError("HELPER_EVENT_REJECTED") from None
