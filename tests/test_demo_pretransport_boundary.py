"""Fixture-only end-to-end proof; never represents Windows or venue evidence."""

import ast
from pathlib import Path

import pytest

from daxlab.runtime import demo_transport_attempt_reservation as owner
from daxlab.runtime.broker_execution_telemetry import telemetry_from_reconciliation
from daxlab.runtime.broker_execution_telemetry_journal import admit_broker_execution_telemetry
import test_demo_transport_attempt_reservation as evidence
import test_demo_transport_query as query_evidence
from test_demo_transport_query_request import FixedClock

prepared_attempt = evidence.prepared_attempt


@pytest.mark.parametrize(
    "case", ["consistent", "missing", "unknown", "accepted", "filled", "stale", "wrong_pin"]
)
def test_restart_query_reconcile_telemetry_replay_never_advances_transport(prepared_attempt, case):
    from datetime import timedelta

    store, prepared = prepared_attempt
    original = evidence._reserve(store, prepared)
    before = store.load("attempt")
    pin = original.fingerprint if case != "wrong_pin" else "d" * 64
    clock = FixedClock(original.evaluated_at)
    if case == "stale":
        clock.value += timedelta(seconds=31)
    args = dict(
        store=store,
        key="attempt",
        expected_reservation_fingerprint=pin,
        bundle_payload=evidence._raw_bundle(),
        clock=clock,
    )
    query_calls = []
    if case in {"stale", "wrong_pin"}:
        with pytest.raises(ValueError):
            owner.build_reserved_demo_transport_query_request(**args)
    else:
        request = owner.build_reserved_demo_transport_query_request(**args)
        assert request["client_order_id"] == prepared.intent.intent_id
        assert request["account_context_fingerprint"] == original.account_context_fingerprint
        # Stand-in supplied observation only; no MT5/venue SDK is imported or called.
        query_calls.append(request["client_order_id"])
        venue = query_evidence._venue(original)
        if case == "missing":
            venue = None
        elif case == "unknown":
            venue = query_evidence._venue(original, venue_state="UNKNOWN")
        elif case == "accepted":
            venue = query_evidence._venue(
                original, venue_state="ACKNOWLEDGED", venue_order_id="V-1"
            )
        elif case == "filled":
            venue = query_evidence._venue(
                original,
                venue_state="FILLED",
                venue_order_id="V-1",
                cumulative_filled_quantity=prepared.intent.quantity,
                average_fill_price=25001.0,
            )
        verdict = owner.reconcile_reserved_demo_transport_query(
            reservation=original,
            bundle_payload=evidence._raw_bundle(),
            venue=venue,
            evaluated_at=clock.now(),
        )
        assert verdict.consistent is (case == "consistent")
        record = telemetry_from_reconciliation(verdict, observed_at=clock.now())
        first = admit_broker_execution_telemetry(prepared.broker.telemetry_journal, record)
        replay = admit_broker_execution_telemetry(first.journal, record)
        assert first.accepted and not replay.accepted
        assert record.order_execution_enabled is False
        assert record.execution_capability == "NONE"
    assert len(query_calls) == (0 if case in {"stale", "wrong_pin"} else 1)
    assert store.saves == 2
    assert store.load("attempt") == before
    assert list(store.values) == ["attempt"]
    restarted = owner.load_reserved_demo_transport_attempt(
        store=store,
        key="attempt",
        expected_reservation_fingerprint=original.fingerprint,
    )
    assert restarted == original
    assert restarted.prepared.post_guard == prepared.post_guard
    assert restarted.prepared.broker == prepared.broker
    assert restarted.prepared.broker.lifecycle.venue_order_id is None
    assert restarted.prepared.broker.lifecycle.cumulative_filled_quantity == 0
    status = owner.demo_transport_restart_status(restarted)
    assert status["venue_state"] == "UNKNOWN"
    assert not status["resubmit_allowed"] and not status["session_slot_release_allowed"]


def test_local_reservation_owner_has_no_sdk_submission_or_execution_activation():
    source = Path(owner.__file__).read_text()
    tree = ast.parse(source)
    forbidden_calls = {"order_send", "submit_order", "send_order", "place_order", "accept_intent"}
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            modules = (
                [node.module or ""]
                if isinstance(node, ast.ImportFrom)
                else [alias.name for alias in node.names]
            )
            assert all(
                name.split(".")[0] not in {"MetaTrader5", "ccxt", "alpaca", "ib_insync"}
                for name in modules
            )
        if isinstance(node, ast.Call):
            name = (
                node.func.attr
                if isinstance(node.func, ast.Attribute)
                else node.func.id
                if isinstance(node.func, ast.Name)
                else ""
            )
            assert name not in forbidden_calls
        if isinstance(node, ast.keyword) and node.arg == "order_execution_enabled":
            assert not (isinstance(node.value, ast.Constant) and node.value.value is True)
