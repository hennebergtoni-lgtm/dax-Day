from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from daxlab.runtime.atomic_json import atomic_write_json, read_json_object
from daxlab.runtime.broker_order_lifecycle import (
    BrokerOrderState,
    apply_order_event,
    begin_order_lifecycle,
    broker_order_lifecycle_state_payload,
    parse_broker_order_lifecycle_state_payload,
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


def _requested():
    return begin_order_lifecycle(intent=_intent(), requested_at=T0 + timedelta(seconds=1))[0]


def _ack():
    requested = _requested()
    return apply_order_event(
        lifecycle=requested,
        state=BrokerOrderState.ACK,
        venue_event_time=T0 + timedelta(seconds=2),
        venue_order_id="venue-123",
    )[0]


def _partial():
    ack = _ack()
    return apply_order_event(
        lifecycle=ack,
        state=BrokerOrderState.PARTIAL,
        venue_event_time=T0 + timedelta(seconds=3),
        cumulative_filled_quantity=0.4,
        last_fill_price=23000.5,
    )[0]


def _roundtrip(lifecycle):
    payload = broker_order_lifecycle_state_payload(lifecycle)
    restored = parse_broker_order_lifecycle_state_payload(payload)
    assert restored == lifecycle
    assert restored.fingerprint == lifecycle.fingerprint
    assert broker_order_lifecycle_state_payload(restored) == payload
    return restored


def test_requested_ack_and_partial_roundtrip_exactly() -> None:
    _roundtrip(_requested())
    _roundtrip(_ack())
    _roundtrip(_partial())


def test_requested_restore_can_continue_to_ack() -> None:
    restored = _roundtrip(_requested())
    continued, event = apply_order_event(
        lifecycle=restored,
        state=BrokerOrderState.ACK,
        venue_event_time=T0 + timedelta(seconds=2),
        venue_order_id="venue-123",
    )
    assert continued == _ack()
    assert event.sequence == 1
    assert event.previous_state is BrokerOrderState.REQUESTED


def test_ack_restore_can_continue_to_partial() -> None:
    restored = _roundtrip(_ack())
    continued, event = apply_order_event(
        lifecycle=restored,
        state=BrokerOrderState.PARTIAL,
        venue_event_time=T0 + timedelta(seconds=3),
        cumulative_filled_quantity=0.4,
        last_fill_price=23000.5,
    )
    assert continued == _partial()
    assert event.sequence == 2
    assert event.previous_state is BrokerOrderState.ACK


def test_partial_restore_then_fill_matches_continuous_execution() -> None:
    continuous_partial = _partial()
    continuous_final, continuous_event = apply_order_event(
        lifecycle=continuous_partial,
        state=BrokerOrderState.FILLED,
        venue_event_time=T0 + timedelta(seconds=4),
        cumulative_filled_quantity=1.0,
        last_fill_price=23001.0,
    )

    restored_partial = _roundtrip(_partial())
    restarted_final, restarted_event = apply_order_event(
        lifecycle=restored_partial,
        state=BrokerOrderState.FILLED,
        venue_event_time=T0 + timedelta(seconds=4),
        cumulative_filled_quantity=1.0,
        last_fill_price=23001.0,
    )

    assert restarted_final == continuous_final
    assert restarted_final.fingerprint == continuous_final.fingerprint
    assert restarted_event == continuous_event
    assert restarted_final.state is BrokerOrderState.FILLED
    assert restarted_final.cumulative_filled_quantity == 1.0


def test_atomic_save_restore_preserves_partial_state(tmp_path) -> None:
    lifecycle = _partial()
    path = tmp_path / "broker_order_lifecycle.json"
    atomic_write_json(path, broker_order_lifecycle_state_payload(lifecycle))
    restored = parse_broker_order_lifecycle_state_payload(read_json_object(path))

    assert restored == lifecycle
    assert restored.state is BrokerOrderState.PARTIAL
    assert restored.venue_order_id == "venue-123"
    assert restored.average_fill_price == 23000.5
    assert restored.event_count == 3


def test_payload_tamper_fails_closed() -> None:
    payload = broker_order_lifecycle_state_payload(_partial())
    tampered = deepcopy(payload)
    tampered["cumulative_filled_quantity"] = 0.5

    with pytest.raises(ValueError, match="payload fingerprint mismatch"):
        parse_broker_order_lifecycle_state_payload(tampered)


def test_lifecycle_fingerprint_drift_fails_closed_even_with_rehashed_payload() -> None:
    payload = broker_order_lifecycle_state_payload(_partial())
    tampered = deepcopy(payload)
    tampered["lifecycle_fingerprint"] = "0" * 64

    # First prove the outer envelope cannot simply be changed without detection.
    with pytest.raises(ValueError, match="payload fingerprint mismatch"):
        parse_broker_order_lifecycle_state_payload(tampered)


def test_execution_escalation_fails_closed() -> None:
    payload = broker_order_lifecycle_state_payload(_requested())
    tampered = deepcopy(payload)
    tampered["execution_capability"] = "BROKER"

    with pytest.raises(ValueError, match="execution capability"):
        parse_broker_order_lifecycle_state_payload(tampered)


def test_unknown_state_and_unknown_fields_fail_closed() -> None:
    payload = broker_order_lifecycle_state_payload(_requested())
    unknown = deepcopy(payload)
    unknown["password"] = "must-not-cross-boundary"
    with pytest.raises(ValueError, match="unknown broker lifecycle state fields"):
        parse_broker_order_lifecycle_state_payload(unknown)


def test_persistence_contract_contains_no_broker_api() -> None:
    root = Path(__file__).resolve().parents[1]
    source = (root / "src/daxlab/runtime/broker_order_lifecycle.py").read_text(
        encoding="utf-8"
    )
    assert "order_send(" not in source
    assert "import MetaTrader5" not in source
