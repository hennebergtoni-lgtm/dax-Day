from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path

import pytest

from daxlab.runtime.atomic_json import atomic_write_json, read_json_object
from daxlab.runtime.broker_execution_checkpoint import (
    BROKER_EXECUTION_CHECKPOINT_SCHEMA,
    BrokerExecutionCheckpointState,
    broker_execution_checkpoint_payload,
    parse_broker_execution_checkpoint_payload,
)
from daxlab.runtime.broker_execution_telemetry_journal import (
    BrokerExecutionTelemetryJournal,
)
from daxlab.runtime.broker_order_lifecycle import (
    BrokerOrderState,
    apply_order_event,
    begin_order_lifecycle,
)
from daxlab.runtime.paper_contracts import ExecutionIntent, Side


UTC = timezone.utc
T0 = datetime(2026, 9, 11, 9, 0, tzinfo=UTC)


def _intent() -> ExecutionIntent:
    return ExecutionIntent.build(
        decision_id="1" * 64,
        run_manifest_fingerprint="2" * 64,
        created_at=T0,
        symbol="DE40",
        side=Side.BUY,
        quantity=1.0,
        requested_price=23000.0,
        stop_price=22990.0,
        target_price=23015.0,
    )


def _partial_lifecycle():
    requested, _ = begin_order_lifecycle(
        intent=_intent(),
        requested_at=T0 + timedelta(seconds=1),
    )
    ack, _ = apply_order_event(
        lifecycle=requested,
        state=BrokerOrderState.ACK,
        venue_event_time=T0 + timedelta(seconds=2),
        venue_order_id="venue-123",
    )
    partial, _ = apply_order_event(
        lifecycle=ack,
        state=BrokerOrderState.PARTIAL,
        venue_event_time=T0 + timedelta(seconds=3),
        cumulative_filled_quantity=0.4,
        last_fill_price=23000.5,
    )
    return partial


def _journal() -> BrokerExecutionTelemetryJournal:
    return BrokerExecutionTelemetryJournal(
        record_fingerprints=("a" * 64, "b" * 64),
    )


def _state() -> BrokerExecutionCheckpointState:
    return BrokerExecutionCheckpointState(
        lifecycle=_partial_lifecycle(),
        telemetry_journal=_journal(),
    )


def _outer_fingerprint(payload: dict[str, object]) -> str:
    unhashed = dict(payload)
    unhashed.pop("payload_fingerprint", None)
    canonical = json.dumps(
        unhashed,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def test_checkpoint_roundtrip_preserves_partial_and_journal() -> None:
    state = _state()
    payload = broker_execution_checkpoint_payload(state)
    restored = parse_broker_execution_checkpoint_payload(payload)

    assert payload["schema_version"] == BROKER_EXECUTION_CHECKPOINT_SCHEMA
    assert restored == state
    assert restored.lifecycle is not None
    assert restored.lifecycle.state is BrokerOrderState.PARTIAL
    assert restored.telemetry_journal == state.telemetry_journal
    assert restored.execution_capability == "NONE"
    assert restored.order_execution_enabled is False
    assert broker_execution_checkpoint_payload(restored) == payload


def test_atomic_restart_partial_to_filled_matches_continuous_execution(tmp_path) -> None:
    state = _state()
    assert state.lifecycle is not None

    continuous_final, continuous_event = apply_order_event(
        lifecycle=state.lifecycle,
        state=BrokerOrderState.FILLED,
        venue_event_time=T0 + timedelta(seconds=4),
        cumulative_filled_quantity=1.0,
        last_fill_price=23001.0,
    )

    path = tmp_path / "broker_execution_checkpoint.json"
    atomic_write_json(path, broker_execution_checkpoint_payload(state))
    restored = parse_broker_execution_checkpoint_payload(read_json_object(path))
    assert restored.lifecycle is not None

    restarted_final, restarted_event = apply_order_event(
        lifecycle=restored.lifecycle,
        state=BrokerOrderState.FILLED,
        venue_event_time=T0 + timedelta(seconds=4),
        cumulative_filled_quantity=1.0,
        last_fill_price=23001.0,
    )

    assert restarted_final == continuous_final
    assert restarted_final.fingerprint == continuous_final.fingerprint
    assert restarted_event == continuous_event
    assert restored.telemetry_journal == state.telemetry_journal


def test_checkpoint_supports_no_active_lifecycle() -> None:
    state = BrokerExecutionCheckpointState(
        lifecycle=None,
        telemetry_journal=_journal(),
    )
    restored = parse_broker_execution_checkpoint_payload(
        broker_execution_checkpoint_payload(state)
    )
    assert restored == state
    assert restored.lifecycle is None


def test_outer_payload_tamper_fails_closed() -> None:
    payload = broker_execution_checkpoint_payload(_state())
    tampered = deepcopy(payload)
    tampered["telemetry_journal"]["record_fingerprints"] = ["c" * 64]

    with pytest.raises(ValueError, match="payload fingerprint mismatch"):
        parse_broker_execution_checkpoint_payload(tampered)


def test_nested_lifecycle_tamper_fails_closed_even_after_outer_rehash() -> None:
    payload = broker_execution_checkpoint_payload(_state())
    tampered = deepcopy(payload)
    assert isinstance(tampered["lifecycle_state"], dict)
    tampered["lifecycle_state"]["cumulative_filled_quantity"] = 0.5
    tampered["payload_fingerprint"] = _outer_fingerprint(tampered)

    with pytest.raises(ValueError, match="payload fingerprint mismatch"):
        parse_broker_execution_checkpoint_payload(tampered)


def test_nested_journal_tamper_fails_closed_even_after_outer_rehash() -> None:
    payload = broker_execution_checkpoint_payload(_state())
    tampered = deepcopy(payload)
    assert isinstance(tampered["telemetry_journal"], dict)
    tampered["telemetry_journal"]["record_fingerprints"] = []
    tampered["payload_fingerprint"] = _outer_fingerprint(tampered)

    with pytest.raises(ValueError, match="fingerprint mismatch"):
        parse_broker_execution_checkpoint_payload(tampered)


def test_outer_and_nested_safety_escalation_fail_closed() -> None:
    outer = broker_execution_checkpoint_payload(_state())
    outer["order_execution_enabled"] = True
    with pytest.raises(ValueError, match="cannot enable order execution"):
        parse_broker_execution_checkpoint_payload(outer)

    nested = broker_execution_checkpoint_payload(_state())
    assert isinstance(nested["lifecycle_state"], dict)
    nested["lifecycle_state"]["execution_capability"] = "BROKER"
    nested["payload_fingerprint"] = _outer_fingerprint(nested)
    with pytest.raises(ValueError, match="execution capability"):
        parse_broker_execution_checkpoint_payload(nested)


def test_unknown_checkpoint_fields_fail_closed() -> None:
    payload = broker_execution_checkpoint_payload(_state())
    payload["password"] = "must-not-cross-boundary"
    with pytest.raises(ValueError, match="unknown broker execution checkpoint fields"):
        parse_broker_execution_checkpoint_payload(payload)


def test_checkpoint_owner_contains_no_broker_or_persistence_api() -> None:
    root = Path(__file__).resolve().parents[1]
    source = (
        root / "src/daxlab/runtime/broker_execution_checkpoint.py"
    ).read_text(encoding="utf-8")
    assert "order_send(" not in source
    assert "import MetaTrader5" not in source
    assert "from daxlab.runtime.atomic_json import" not in source
    assert "atomic_write_json(" not in source
    assert "open(" not in source
