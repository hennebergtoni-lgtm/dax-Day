from dataclasses import replace
from datetime import timedelta
import inspect
import json
from unittest.mock import Mock

import pytest

from daxlab.adapters.file_state_store import AtomicFileStateStore
from daxlab.domain.execution import ExecutionIntent, OrderSide
from daxlab.domain.market import InstrumentId
from daxlab.domain.session_admission import (
    SessionAdmissionConsumptionRecord,
    SessionAdmissionConsumptionState,
)
from daxlab.runtime.broker_execution_checkpoint import broker_execution_checkpoint_payload
from daxlab.runtime.broker_execution_protection import ExecutionProtectionStatus
from daxlab.runtime.broker_order_lifecycle import BrokerOrderState, apply_order_event
from daxlab.runtime import nextgen_prepared_checkpoint as owner
from daxlab.state.session_admission import build_session_admission_guard_checkpoint
import test_nextgen_execution_protection_binding as evidence


class MemoryStore:
    def __init__(self):
        self.values = {}
        self.saves = 0

    def load(self, key):
        return self.values.get(key)

    def save(self, key, payload):
        self.values[key] = payload
        self.saves += 1


@pytest.fixture
def attempt(monkeypatch):
    intent = ExecutionIntent.build(
        decision_id="a" * 64,
        provenance_fingerprint="b" * 64,
        created_at=evidence.EVALUATED_AT,
        instrument_id=InstrumentId("DAX40.CFD"),
        side=OrderSide.BUY,
        quantity=2.5,
        requested_price=25000.0,
        stop_price=24900.0,
        target_price=25200.0,
    )
    policy, state, admission = evidence._session_chain()
    guard = evidence._session_guard(policy, state)
    monkeypatch.setattr(evidence, "CLIENT_ID", intent.intent_id)
    protection = evidence._evaluate(session=(policy, state, admission), session_guard=guard)
    assert protection.allow_evidence
    return dict(
        intent=intent,
        policy=policy,
        admission=admission,
        pre_guard=guard,
        protection=protection,
        requested_at=intent.created_at + timedelta(seconds=1),
    )


def test_deterministic_identity_consumption_requested_and_restart(attempt):
    first = owner.build_nextgen_prepared_checkpoint(**attempt)
    second = owner.build_nextgen_prepared_checkpoint(**attempt)
    assert first == second and first.fingerprint == second.fingerprint
    assert (
        first.intent.intent_id
        == first.broker.lifecycle.client_order_id
        == first.post_guard.state.records[-1].consumption_id
    )
    assert first.post_guard.state.trades_admitted == first.pre_guard.state.trades_admitted + 1
    assert first.pre_guard.state.trades_admitted == 0
    assert first.broker.lifecycle.state is BrokerOrderState.REQUESTED
    assert first.broker.lifecycle.event_count == 1
    assert first.broker.lifecycle.venue_order_id is None
    assert first.broker.lifecycle.average_fill_price is None
    assert first.broker.lifecycle.cumulative_filled_quantity == 0
    assert first.post_guard.observed_at == first.pre_guard.observed_at
    payload = owner.nextgen_prepared_checkpoint_to_bytes(first)
    restored = owner.nextgen_prepared_checkpoint_from_bytes(payload)
    assert restored == first
    assert restored.protection == attempt["protection"]
    assert owner.nextgen_prepared_checkpoint_to_bytes(restored) == payload
    assert restored.execution_capability == "NONE"
    assert restored.order_execution_enabled is False


def test_retry_stores_once_and_calls_no_consumption_or_lifecycle(attempt, monkeypatch):
    store = MemoryStore()
    first = owner.prepare_nextgen_checkpoint(store=store, key="prepared", **attempt)
    no_consume = Mock(side_effect=AssertionError("retry consumed another slot"))
    no_lifecycle = Mock(side_effect=AssertionError("retry began another lifecycle"))
    monkeypatch.setattr(owner, "consume_session_admission", no_consume)
    monkeypatch.setattr(owner, "begin_nextgen_order_lifecycle", no_lifecycle)
    assert owner.prepare_nextgen_checkpoint(store=store, key="prepared", **attempt) == first
    assert owner.prepare_nextgen_checkpoint(store=store, key="prepared", **attempt) == first
    assert store.saves == 1 and list(store.values) == ["prepared"]
    no_consume.assert_not_called()
    no_lifecycle.assert_not_called()


def test_atomic_file_store_uses_exactly_one_payload(attempt, tmp_path):
    store = AtomicFileStateStore(tmp_path)
    checkpoint = owner.prepare_nextgen_checkpoint(store=store, key="prepared", **attempt)
    assert len(list(tmp_path.iterdir())) == 1
    assert owner.nextgen_prepared_checkpoint_from_bytes(store.load("prepared")) == checkpoint


@pytest.mark.parametrize("change", ["identity", "protection", "requested_at", "guard"])
def test_key_collision_fails_without_save(attempt, change):
    store = MemoryStore()
    owner.prepare_nextgen_checkpoint(store=store, key="prepared", **attempt)
    altered = dict(attempt)
    if change == "identity":
        altered["intent"] = replace(attempt["intent"], intent_id="c" * 64)
    elif change == "protection":
        altered["protection"] = replace(attempt["protection"], feed_age_seconds=0.3)
    elif change == "requested_at":
        altered["requested_at"] += timedelta(seconds=1)
    else:
        altered["pre_guard"] = build_session_admission_guard_checkpoint(
            policy_fingerprint=attempt["policy"].policy_fingerprint,
            state=attempt["pre_guard"].state,
            observed_at=attempt["pre_guard"].observed_at + timedelta(seconds=1),
        )
    with pytest.raises(ValueError, match="collision"):
        owner.prepare_nextgen_checkpoint(store=store, key="prepared", **altered)
    assert store.saves == 1


def test_blocked_never_consumes_starts_or_saves(attempt, monkeypatch):
    blocked = dict(
        attempt,
        protection=replace(
            attempt["protection"], status=ExecutionProtectionStatus.BLOCKED, blockers=("HOST_RED",)
        ),
    )
    store = MemoryStore()
    consume = Mock(side_effect=AssertionError("blocked consumed"))
    start = Mock(side_effect=AssertionError("blocked began lifecycle"))
    monkeypatch.setattr(owner, "consume_session_admission", consume)
    monkeypatch.setattr(owner, "begin_nextgen_order_lifecycle", start)
    with pytest.raises(ValueError, match="ALLOW_EVIDENCE"):
        owner.prepare_nextgen_checkpoint(store=store, key="prepared", **blocked)
    assert store.saves == 0
    consume.assert_not_called()
    start.assert_not_called()


def _rehash(payload):
    payload.pop("prepared_fingerprint", None)
    payload["prepared_fingerprint"] = owner._fingerprint(payload)
    return owner._bytes(payload)


def test_outer_fingerprint_rejects_tampering(attempt):
    raw = json.loads(
        owner.nextgen_prepared_checkpoint_to_bytes(
            owner.build_nextgen_prepared_checkpoint(**attempt)
        )
    )
    raw["protection"]["feed_age_seconds"] = 0.4
    with pytest.raises(ValueError, match="fingerprint"):
        owner.nextgen_prepared_checkpoint_from_bytes(owner._bytes(raw))


@pytest.mark.parametrize(
    "change",
    [
        "intent_client",
        "intent_consumption",
        "lifecycle_intent",
        "protection_client",
        "guard_policy",
        "protection_policy",
        "protection_observation",
        "protection_guard",
        "protection_admission",
        "record_identity",
        "record_admission",
        "lifecycle_not_requested",
        "venue_evidence",
        "fill_evidence",
        "event_identity",
        "post_freshness",
        "status",
        "capability",
        "execution",
    ],
)
def test_rehashed_cross_wiring_fails_closed(attempt, change):
    checkpoint = owner.build_nextgen_prepared_checkpoint(**attempt)
    raw = json.loads(owner.nextgen_prepared_checkpoint_to_bytes(checkpoint))
    lifecycle = checkpoint.broker.lifecycle
    if change in (
        "intent_client",
        "lifecycle_intent",
        "event_identity",
        "venue_evidence",
        "fill_evidence",
    ):
        updates = {
            "intent_client": {"client_order_id": "c" * 64},
            "lifecycle_intent": {"intent_fingerprint": "c" * 64},
            "event_identity": {"last_event_fingerprint": "c" * 64},
            "venue_evidence": {"venue_order_id": "VENUE-1"},
            "fill_evidence": {"average_fill_price": 25000.0},
        }[change]
        raw["broker"] = broker_execution_checkpoint_payload(
            replace(checkpoint.broker, lifecycle=replace(lifecycle, **updates))
        )
    elif change == "lifecycle_not_requested":
        ack, _ = apply_order_event(
            lifecycle=lifecycle,
            state=BrokerOrderState.ACK,
            venue_event_time=lifecycle.last_event_time,
            venue_order_id="VENUE-1",
        )
        raw["broker"] = broker_execution_checkpoint_payload(
            replace(checkpoint.broker, lifecycle=ack)
        )
    elif change in ("intent_consumption", "record_identity", "record_admission"):
        record = SessionAdmissionConsumptionRecord.build(
            consumption_id="c" * 64
            if change != "record_admission"
            else checkpoint.intent.intent_id,
            admission_decision_fingerprint="d" * 64
            if change == "record_admission"
            else checkpoint.admission.decision_fingerprint,
        )
        state = SessionAdmissionConsumptionState.build(
            session_key=checkpoint.post_guard.state.session_key, records=(record,)
        )
        raw["post_guard"] = build_session_admission_guard_checkpoint(
            policy_fingerprint=checkpoint.policy.policy_fingerprint,
            state=state,
            observed_at=checkpoint.pre_guard.observed_at,
        ).to_dict()
    elif change == "guard_policy":
        raw["post_guard"] = build_session_admission_guard_checkpoint(
            policy_fingerprint="c" * 64,
            state=checkpoint.post_guard.state,
            observed_at=checkpoint.pre_guard.observed_at,
        ).to_dict()
    elif change.startswith("protection_"):
        field = {
            "protection_policy": "session_policy_fingerprint",
            "protection_client": "client_order_id",
            "protection_observation": "session_observation_fingerprint",
            "protection_guard": "session_guard_checkpoint_fingerprint",
            "protection_admission": "session_admission_evidence_fingerprint",
        }[change]
        raw["protection"][field] = "c" * 64
    elif change == "post_freshness":
        raw["post_guard"] = build_session_admission_guard_checkpoint(
            policy_fingerprint=checkpoint.policy.policy_fingerprint,
            state=checkpoint.post_guard.state,
            observed_at=checkpoint.pre_guard.observed_at + timedelta(seconds=1),
        ).to_dict()
    else:
        field, value = {
            "status": ("status", "ACCEPTED"),
            "capability": ("execution_capability", "LIVE"),
            "execution": ("order_execution_enabled", True),
        }[change]
        raw[field] = value
    with pytest.raises(ValueError):
        owner.nextgen_prepared_checkpoint_from_bytes(_rehash(raw))


def test_failed_store_does_not_change_caller_state(attempt):
    class FailedStore(MemoryStore):
        def save(self, key, payload):
            raise OSError("disk unavailable")

    with pytest.raises(OSError):
        owner.prepare_nextgen_checkpoint(store=FailedStore(), key="prepared", **attempt)
    assert attempt["pre_guard"].state.trades_admitted == 0


def test_no_broker_or_mt5_submission_api():
    source = inspect.getsource(owner)
    for prohibited in ("order_send", "MetaTrader5", "submit_order", "place_order"):
        assert prohibited not in source
