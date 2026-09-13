from dataclasses import dataclass
from datetime import datetime, timedelta
import json

import pytest

from daxlab.runtime import demo_transport_attempt_reservation as owner
import test_demo_transport_attempt_reservation as evidence

prepared_attempt = evidence.prepared_attempt


@dataclass
class FixedClock:
    value: datetime
    calls: int = 0

    def now(self):
        self.calls += 1
        return self.value


def _request(store, reservation, **changes):
    args = dict(
        store=store,
        key="attempt",
        expected_reservation_fingerprint=reservation.fingerprint,
        bundle_payload=evidence._raw_bundle(),
        clock=FixedClock(reservation.evaluated_at),
    )
    args.update(changes)
    return owner.build_reserved_demo_transport_query_request(**args)


def test_deterministic_query_projection_binds_same_attempt_without_save(prepared_attempt):
    store, prepared = prepared_attempt
    reservation = evidence._reserve(store, prepared)
    original = store.load("attempt")
    first = _request(store, reservation)
    assert _request(store, reservation) == first
    assert json.loads(json.dumps(first)) == first
    assert first["attempt_key"] == "attempt"
    assert first["client_order_id"] == prepared.intent.intent_id
    assert first["requested_action"] == "QUERY_EVIDENCE_ORDER"
    assert first["reservation_fingerprint"] == reservation.fingerprint
    assert first["prepared_fingerprint"] == prepared.fingerprint
    assert first["authorization_fingerprint"] == reservation.authorization_fingerprint
    assert first["account_context_fingerprint"] == reservation.account_context_fingerprint
    assert first["account_context"] == reservation.account_context.to_payload()
    assert first["bundle_fingerprint"] == reservation.bundle_fingerprint
    assert first["submission_ordinal"] == 1
    assert first["venue_state"] == "UNKNOWN"
    assert first["execution_capability"] == "NONE"
    assert first["order_execution_enabled"] is False
    assert not first["resubmit_allowed"] and not first["session_slot_release_allowed"]
    raw = dict(first)
    observed = raw.pop("query_request_fingerprint")
    assert owner._fingerprint(raw) == observed
    raw["client_order_id"] = "d" * 64
    assert owner._fingerprint(raw) != observed
    assert store.load("attempt") == original
    assert store.saves == 2


def test_explicit_query_clock_does_not_refresh_original_host_or_reservation(prepared_attempt):
    store, prepared = prepared_attempt
    reservation = evidence._reserve(store, prepared)
    clock = FixedClock(reservation.evaluated_at + timedelta(seconds=1))
    first = _request(store, reservation)
    later = _request(store, reservation, clock=clock)
    assert clock.calls == 1
    assert later["query_request_fingerprint"] != first["query_request_fingerprint"]
    assert later["host_observed_at"] == first["host_observed_at"]
    assert later["original_reservation_evaluated_at"] == first["original_reservation_evaluated_at"]
    assert later["reservation_fingerprint"] == first["reservation_fingerprint"]
    assert store.saves == 2


@pytest.mark.parametrize(
    "case", ["missing", "prepared", "wrong_pin", "other_key", "stale", "naive_clock"]
)
def test_query_projection_fails_closed_before_any_adapter(prepared_attempt, case):
    store, prepared = prepared_attempt
    reservation = evidence._reserve(store, prepared)
    changes = {}
    if case == "missing":
        del store.values["attempt"]
    elif case == "prepared":
        store.values["attempt"] = owner.nextgen_prepared_checkpoint_to_bytes(prepared)
    elif case == "wrong_pin":
        changes["expected_reservation_fingerprint"] = "d" * 64
    elif case == "other_key":
        changes["key"] = "other-attempt"
    elif case == "stale":
        changes["clock"] = FixedClock(reservation.evaluated_at + timedelta(seconds=31))
    else:
        changes["clock"] = FixedClock(reservation.evaluated_at.replace(tzinfo=None))
    snapshot = dict(store.values)
    with pytest.raises(ValueError):
        _request(store, reservation, **changes)
    assert store.values == snapshot
    assert store.saves == 2
