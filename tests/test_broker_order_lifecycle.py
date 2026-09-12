from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from daxlab.runtime.broker_order_lifecycle import (
    BrokerOrderState,
    apply_order_event,
    begin_order_lifecycle,
)
from daxlab.runtime.paper_contracts import ExecutionIntent, Side


UTC = timezone.utc
T0 = datetime(2026, 9, 11, 9, 15, tzinfo=UTC)


def _intent(*, quantity: float = 2.0) -> ExecutionIntent:
    return ExecutionIntent.build(
        decision_id="1" * 64,
        run_manifest_fingerprint="2" * 64,
        created_at=T0,
        symbol="DE40",
        side=Side.BUY,
        quantity=quantity,
        requested_price=24000.0,
        stop_price=23980.0,
        target_price=24030.0,
    )


def test_begin_lifecycle_is_deterministic_and_execution_disabled() -> None:
    intent = _intent()
    one, event_one = begin_order_lifecycle(intent=intent, requested_at=T0 + timedelta(seconds=1))
    two, event_two = begin_order_lifecycle(intent=intent, requested_at=T0 + timedelta(seconds=1))

    assert one == two
    assert event_one == event_two
    assert one.fingerprint == two.fingerprint
    assert one.client_order_id == intent.client_order_id
    assert one.state is BrokerOrderState.REQUESTED
    assert one.execution_capability == "NONE"
    assert one.order_execution_enabled is False
    assert event_one.execution_capability == "NONE"
    assert event_one.order_execution_enabled is False


def test_ack_partial_filled_tracks_weighted_average_price() -> None:
    lifecycle, _ = begin_order_lifecycle(intent=_intent(), requested_at=T0 + timedelta(seconds=1))
    lifecycle, ack = apply_order_event(
        lifecycle=lifecycle,
        state=BrokerOrderState.ACK,
        venue_event_time=T0 + timedelta(seconds=2),
        venue_order_id="venue-42",
    )
    assert ack.previous_state is BrokerOrderState.REQUESTED
    assert lifecycle.state is BrokerOrderState.ACK

    lifecycle, partial = apply_order_event(
        lifecycle=lifecycle,
        state=BrokerOrderState.PARTIAL,
        venue_event_time=T0 + timedelta(seconds=3),
        cumulative_filled_quantity=0.5,
        last_fill_price=24001.0,
        venue_order_id="venue-42",
    )
    assert partial.last_fill_quantity == 0.5
    assert lifecycle.cumulative_filled_quantity == 0.5
    assert lifecycle.average_fill_price == 24001.0

    lifecycle, filled = apply_order_event(
        lifecycle=lifecycle,
        state=BrokerOrderState.FILLED,
        venue_event_time=T0 + timedelta(seconds=4),
        cumulative_filled_quantity=2.0,
        last_fill_price=24003.0,
        venue_order_id="venue-42",
    )
    assert filled.last_fill_quantity == 1.5
    assert lifecycle.state is BrokerOrderState.FILLED
    assert lifecycle.terminal is True
    assert lifecycle.cumulative_filled_quantity == 2.0
    assert lifecycle.average_fill_price == pytest.approx(24002.5)


def test_direct_fill_is_allowed_when_venue_has_no_separate_ack() -> None:
    lifecycle, _ = begin_order_lifecycle(intent=_intent(quantity=1.0), requested_at=T0)
    lifecycle, event = apply_order_event(
        lifecycle=lifecycle,
        state=BrokerOrderState.FILLED,
        venue_event_time=T0 + timedelta(milliseconds=50),
        cumulative_filled_quantity=1.0,
        last_fill_price=24000.5,
        venue_order_id="venue-direct",
    )
    assert event.previous_state is BrokerOrderState.REQUESTED
    assert lifecycle.state is BrokerOrderState.FILLED
    assert lifecycle.average_fill_price == 24000.5


def test_reject_requires_reason_and_is_terminal() -> None:
    lifecycle, _ = begin_order_lifecycle(intent=_intent(), requested_at=T0)
    with pytest.raises(ValueError, match="REJECT requires a reason"):
        apply_order_event(
            lifecycle=lifecycle,
            state=BrokerOrderState.REJECT,
            venue_event_time=T0 + timedelta(seconds=1),
        )

    lifecycle, _ = apply_order_event(
        lifecycle=lifecycle,
        state=BrokerOrderState.REJECT,
        venue_event_time=T0 + timedelta(seconds=1),
        reason="VENUE_REJECTED",
    )
    assert lifecycle.terminal is True
    with pytest.raises(ValueError, match="terminal"):
        apply_order_event(
            lifecycle=lifecycle,
            state=BrokerOrderState.ACK,
            venue_event_time=T0 + timedelta(seconds=2),
            venue_order_id="late-ack",
        )


def test_overfill_and_invalid_partial_fail_closed() -> None:
    lifecycle, _ = begin_order_lifecycle(intent=_intent(quantity=1.0), requested_at=T0)
    with pytest.raises(ValueError, match="cannot exceed requested"):
        apply_order_event(
            lifecycle=lifecycle,
            state=BrokerOrderState.FILLED,
            venue_event_time=T0 + timedelta(seconds=1),
            cumulative_filled_quantity=1.01,
            last_fill_price=24000.0,
            venue_order_id="venue-1",
        )
    with pytest.raises(ValueError, match="PARTIAL requires"):
        apply_order_event(
            lifecycle=lifecycle,
            state=BrokerOrderState.PARTIAL,
            venue_event_time=T0 + timedelta(seconds=1),
            cumulative_filled_quantity=1.0,
            last_fill_price=24000.0,
            venue_order_id="venue-1",
        )


def test_positive_fill_delta_requires_fill_price() -> None:
    lifecycle, _ = begin_order_lifecycle(intent=_intent(), requested_at=T0)
    with pytest.raises(ValueError, match="requires positive last_fill_price"):
        apply_order_event(
            lifecycle=lifecycle,
            state=BrokerOrderState.PARTIAL,
            venue_event_time=T0 + timedelta(seconds=1),
            cumulative_filled_quantity=0.5,
            venue_order_id="venue-1",
        )


def test_event_time_cannot_move_backwards() -> None:
    lifecycle, _ = begin_order_lifecycle(intent=_intent(), requested_at=T0 + timedelta(seconds=2))
    with pytest.raises(ValueError, match="cannot move backwards"):
        apply_order_event(
            lifecycle=lifecycle,
            state=BrokerOrderState.ACK,
            venue_event_time=T0 + timedelta(seconds=1),
            venue_order_id="venue-1",
        )


def test_venue_order_id_cannot_drift_after_binding() -> None:
    lifecycle, _ = begin_order_lifecycle(intent=_intent(), requested_at=T0)
    lifecycle, _ = apply_order_event(
        lifecycle=lifecycle,
        state=BrokerOrderState.ACK,
        venue_event_time=T0 + timedelta(seconds=1),
        venue_order_id="venue-a",
    )
    with pytest.raises(ValueError, match="cannot change"):
        apply_order_event(
            lifecycle=lifecycle,
            state=BrokerOrderState.CANCELLED,
            venue_event_time=T0 + timedelta(seconds=2),
            venue_order_id="venue-b",
            reason="OPERATOR_CANCEL",
        )


def test_request_cannot_precede_intent_creation() -> None:
    with pytest.raises(ValueError, match="cannot precede"):
        begin_order_lifecycle(intent=_intent(), requested_at=T0 - timedelta(microseconds=1))
