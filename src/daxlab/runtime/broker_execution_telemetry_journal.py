"""Restart-safe idempotency journal for broker-neutral execution telemetry.

Canonical telemetry records remain owned by ``broker_execution_telemetry``. This
module stores only which deterministic telemetry fingerprints have already crossed
an append-only persistence/publication boundary, so retry/restart cannot admit the
same evidence twice. Persistence is delegated to the existing ``atomic_json``
helper; no broker API, order submission capability or recovery framework exists
here.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Mapping

from daxlab.runtime.broker_execution_telemetry import BrokerExecutionTelemetryRecord


BROKER_EXECUTION_TELEMETRY_JOURNAL_SCHEMA = (
    "DAXLAB_BROKER_EXECUTION_TELEMETRY_JOURNAL_V1"
)
_ALLOWED_FIELDS = {
    "schema_version",
    "record_fingerprints",
    "execution_capability",
    "order_execution_enabled",
    "payload_fingerprint",
}


@dataclass(frozen=True, slots=True)
class BrokerExecutionTelemetryJournal:
    record_fingerprints: tuple[str, ...] = ()
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        _validate_fingerprints(self.record_fingerprints)
        if self.execution_capability != "NONE" or self.order_execution_enabled:
            raise ValueError("broker telemetry journal cannot authorize execution")


@dataclass(frozen=True, slots=True)
class BrokerTelemetryAdmission:
    journal: BrokerExecutionTelemetryJournal
    accepted: bool
    telemetry_fingerprint: str


def admit_broker_execution_telemetry(
    journal: BrokerExecutionTelemetryJournal,
    record: BrokerExecutionTelemetryRecord,
) -> BrokerTelemetryAdmission:
    """Admit one canonical telemetry identity exactly once across restarts."""
    if record.execution_capability != "NONE" or record.order_execution_enabled:
        raise ValueError("broker telemetry record cannot authorize execution")
    fingerprint = _sha(record.telemetry_fingerprint, "telemetry_fingerprint")
    if fingerprint in journal.record_fingerprints:
        return BrokerTelemetryAdmission(
            journal=journal,
            accepted=False,
            telemetry_fingerprint=fingerprint,
        )
    return BrokerTelemetryAdmission(
        journal=BrokerExecutionTelemetryJournal(
            record_fingerprints=tuple(sorted((*journal.record_fingerprints, fingerprint)))
        ),
        accepted=True,
        telemetry_fingerprint=fingerprint,
    )


def broker_execution_telemetry_journal_payload(
    journal: BrokerExecutionTelemetryJournal,
) -> dict[str, Any]:
    """Return a strict JSON-safe tamper-evident journal envelope."""
    payload: dict[str, Any] = {
        "schema_version": BROKER_EXECUTION_TELEMETRY_JOURNAL_SCHEMA,
        "record_fingerprints": list(journal.record_fingerprints),
        "execution_capability": journal.execution_capability,
        "order_execution_enabled": journal.order_execution_enabled,
    }
    payload["payload_fingerprint"] = _fingerprint(payload)
    return payload


def parse_broker_execution_telemetry_journal_payload(
    payload: Mapping[str, Any],
) -> BrokerExecutionTelemetryJournal:
    """Fail closed on schema, shape, tamper or execution-safety drift."""
    unknown = payload.keys() - _ALLOWED_FIELDS
    missing = _ALLOWED_FIELDS - payload.keys()
    if unknown:
        raise ValueError(f"unknown broker telemetry journal fields: {sorted(unknown)}")
    if missing:
        raise ValueError(f"missing broker telemetry journal fields: {sorted(missing)}")
    if payload.get("schema_version") != BROKER_EXECUTION_TELEMETRY_JOURNAL_SCHEMA:
        raise ValueError("broker telemetry journal schema mismatch")
    if payload.get("execution_capability") != "NONE":
        raise ValueError("broker telemetry journal execution capability invalid")
    if payload.get("order_execution_enabled") is not False:
        raise ValueError("broker telemetry journal cannot enable order execution")

    observed = payload.get("payload_fingerprint")
    _sha(observed, "payload_fingerprint")
    unhashed = dict(payload)
    unhashed.pop("payload_fingerprint", None)
    if _fingerprint(unhashed) != observed:
        raise ValueError("broker telemetry journal payload fingerprint mismatch")

    raw = payload.get("record_fingerprints")
    if not isinstance(raw, list) or not all(isinstance(item, str) for item in raw):
        raise ValueError("record_fingerprints must be a list of strings")
    fingerprints = tuple(raw)
    _validate_fingerprints(fingerprints)
    return BrokerExecutionTelemetryJournal(record_fingerprints=fingerprints)


def _validate_fingerprints(values: tuple[str, ...]) -> None:
    if values != tuple(sorted(values)):
        raise ValueError("record_fingerprints must be sorted")
    if len(set(values)) != len(values):
        raise ValueError("record_fingerprints must be unique")
    for value in values:
        _sha(value, "record_fingerprint")


def _sha(value: Any, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{field} must be sha256 hex")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field} must be sha256 hex") from exc
    return value


def _fingerprint(value: Mapping[str, Any]) -> str:
    canonical = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()
