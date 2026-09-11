from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

import pytest

from daxlab.runtime.atomic_json import atomic_write_json, read_json_object
from daxlab.runtime.broker_execution_protection import evaluate_execution_protection
from daxlab.runtime.broker_execution_telemetry import telemetry_from_protection
from daxlab.runtime.broker_execution_telemetry_journal import (
    BrokerExecutionTelemetryJournal,
    admit_broker_execution_telemetry,
    broker_execution_telemetry_journal_payload,
    parse_broker_execution_telemetry_journal_payload,
)


UTC = timezone.utc
CLIENT_ID = "a" * 64
SIZING_FP = "b" * 64
RISK_FP = "c" * 64


def _record(*, feed_age_seconds: float = 1.0):
    verdict = evaluate_execution_protection(
        client_order_id=CLIENT_ID,
        host_health_green=True,
        broker_account_trade_allowed=True,
        feed_age_seconds=feed_age_seconds,
        max_feed_age_seconds=10.0,
        observed_spread_points=0.2,
        max_spread_points=0.5,
        reconciliation_inventory_complete=True,
        reconciliations=(),
        duplicate_client_order_id=False,
        sizing_allowed=True,
        sizing_evidence_fingerprint=SIZING_FP,
        loss_cap_allowed=True,
        risk_policy_fingerprint=RISK_FP,
        session_admission_allowed=True,
    )
    return telemetry_from_protection(
        verdict,
        evaluated_at=datetime(2026, 9, 11, 10, 0, tzinfo=UTC),
    )


def test_record_is_admitted_once_and_duplicate_is_rejected() -> None:
    record = _record()
    first = admit_broker_execution_telemetry(BrokerExecutionTelemetryJournal(), record)
    duplicate = admit_broker_execution_telemetry(first.journal, record)

    assert first.accepted is True
    assert duplicate.accepted is False
    assert duplicate.journal == first.journal
    assert first.telemetry_fingerprint == record.telemetry_fingerprint
    assert first.journal.record_fingerprints == (record.telemetry_fingerprint,)
    assert first.journal.execution_capability == "NONE"
    assert first.journal.order_execution_enabled is False


def test_duplicate_remains_rejected_after_atomic_restart(tmp_path) -> None:
    record = _record()
    first = admit_broker_execution_telemetry(BrokerExecutionTelemetryJournal(), record)
    path = tmp_path / "broker_execution_telemetry_journal.json"
    atomic_write_json(path, broker_execution_telemetry_journal_payload(first.journal))

    restored = parse_broker_execution_telemetry_journal_payload(read_json_object(path))
    duplicate = admit_broker_execution_telemetry(restored, record)

    assert restored == first.journal
    assert duplicate.accepted is False
    assert duplicate.journal == restored


def test_distinct_records_are_admitted_and_sorted_deterministically() -> None:
    first_record = _record(feed_age_seconds=1.0)
    second_record = _record(feed_age_seconds=2.0)
    first = admit_broker_execution_telemetry(
        BrokerExecutionTelemetryJournal(),
        first_record,
    )
    second = admit_broker_execution_telemetry(first.journal, second_record)

    assert first.accepted is True
    assert second.accepted is True
    assert second.journal.record_fingerprints == tuple(
        sorted((first_record.telemetry_fingerprint, second_record.telemetry_fingerprint))
    )


def test_payload_roundtrip_is_deterministic() -> None:
    record = _record()
    admitted = admit_broker_execution_telemetry(BrokerExecutionTelemetryJournal(), record)
    payload = broker_execution_telemetry_journal_payload(admitted.journal)
    restored = parse_broker_execution_telemetry_journal_payload(payload)

    assert restored == admitted.journal
    assert broker_execution_telemetry_journal_payload(restored) == payload


def test_tampered_persisted_journal_fails_closed() -> None:
    record = _record()
    admitted = admit_broker_execution_telemetry(BrokerExecutionTelemetryJournal(), record)
    payload = broker_execution_telemetry_journal_payload(admitted.journal)
    tampered = deepcopy(payload)
    tampered["record_fingerprints"] = []

    with pytest.raises(ValueError, match="fingerprint mismatch"):
        parse_broker_execution_telemetry_journal_payload(tampered)


def test_execution_escalation_fails_closed() -> None:
    payload = broker_execution_telemetry_journal_payload(BrokerExecutionTelemetryJournal())
    tampered = deepcopy(payload)
    tampered["execution_capability"] = "BROKER"

    with pytest.raises(ValueError, match="execution capability"):
        parse_broker_execution_telemetry_journal_payload(tampered)


def test_order_execution_escalation_fails_closed() -> None:
    payload = broker_execution_telemetry_journal_payload(BrokerExecutionTelemetryJournal())
    tampered = deepcopy(payload)
    tampered["order_execution_enabled"] = True

    with pytest.raises(ValueError, match="cannot enable order execution"):
        parse_broker_execution_telemetry_journal_payload(tampered)


def test_unsorted_duplicate_and_invalid_fingerprints_are_rejected() -> None:
    a = "a" * 64
    b = "b" * 64
    with pytest.raises(ValueError, match="must be sorted"):
        BrokerExecutionTelemetryJournal(record_fingerprints=(b, a))
    with pytest.raises(ValueError, match="must be unique"):
        BrokerExecutionTelemetryJournal(record_fingerprints=(a, a))
    with pytest.raises(ValueError, match="sha256 hex"):
        BrokerExecutionTelemetryJournal(record_fingerprints=("not-a-sha",))


def test_unknown_persisted_fields_fail_closed() -> None:
    payload = broker_execution_telemetry_journal_payload(BrokerExecutionTelemetryJournal())
    payload["password"] = "must-not-cross-boundary"

    with pytest.raises(ValueError, match="unknown broker telemetry journal fields"):
        parse_broker_execution_telemetry_journal_payload(payload)


def test_journal_owner_contains_no_broker_submission_or_new_persistence_api() -> None:
    root = Path(__file__).resolve().parents[1]
    source = (
        root / "src/daxlab/runtime/broker_execution_telemetry_journal.py"
    ).read_text(encoding="utf-8")
    assert "order_send(" not in source
    assert "import MetaTrader5" not in source
    assert "open(" not in source
    assert "atomic_write_json" not in source
