from dataclasses import replace
from datetime import timedelta

import pytest

from daxlab.runtime import demo_transport_attempt_reservation as owner
from daxlab.runtime.broker_execution_telemetry import telemetry_from_reconciliation
from daxlab.runtime.broker_execution_telemetry_journal import admit_broker_execution_telemetry
from daxlab.runtime.broker_reconciliation import (
    VENUE_ORDER_OBSERVATION_SCHEMA,
    VenueOrderObservation,
)
from daxlab.runtime.demo_evidence_authorization import DemoEvidenceAction
import test_demo_transport_attempt_reservation as evidence

prepared_attempt = evidence.prepared_attempt


def _venue(reservation, **changes):
    fields = dict(
        schema_version=VENUE_ORDER_OBSERVATION_SCHEMA,
        observed_at=reservation.evaluated_at,
        client_order_id=reservation.prepared.intent.intent_id,
        venue_order_id=None,
        venue_state="REQUESTED",
        requested_quantity=reservation.prepared.intent.quantity,
        cumulative_filled_quantity=0.0,
        average_fill_price=None,
    )
    fields.update(changes)
    return VenueOrderObservation(**fields)


def _query(reservation, venue, **changes):
    args = dict(
        reservation=reservation,
        bundle_payload=evidence._raw_bundle(),
        venue=venue,
        evaluated_at=reservation.evaluated_at,
    )
    args.update(changes)
    return owner.reconcile_reserved_demo_transport_query(**args)


def test_query_reuses_reconciliation_telemetry_and_existing_journal(prepared_attempt):
    store, prepared = prepared_attempt
    reservation = evidence._reserve(store, prepared)
    before = store.load("attempt")
    venue = _venue(reservation)
    verdict = _query(reservation, venue)
    assert verdict.consistent
    assert verdict.local_lifecycle_fingerprint == prepared.broker.lifecycle.fingerprint
    assert verdict.venue_observation_fingerprint == venue.fingerprint
    assert verdict.execution_capability == "NONE"
    assert verdict.order_execution_enabled is False
    record = telemetry_from_reconciliation(verdict, observed_at=venue.observed_at)
    first = admit_broker_execution_telemetry(prepared.broker.telemetry_journal, record)
    replay = admit_broker_execution_telemetry(first.journal, record)
    assert first.accepted and not replay.accepted
    assert replay.journal == first.journal
    assert record.venue_order_id is None
    assert record.cumulative_filled_quantity is None
    assert store.load("attempt") == before
    assert store.saves == 2
    assert owner.demo_transport_restart_status(reservation)["resubmit_allowed"] is False


@pytest.mark.parametrize("change", ["missing", "unknown", "identity", "accepted", "fill"])
def test_missing_unknown_or_contradictory_venue_truth_never_allows_retry(prepared_attempt, change):
    store, prepared = prepared_attempt
    reservation = evidence._reserve(store, prepared)
    venue = {
        "missing": None,
        "unknown": _venue(reservation, venue_state="UNKNOWN"),
        "identity": _venue(reservation, client_order_id="d" * 64),
        "accepted": _venue(reservation, venue_state="ACKNOWLEDGED", venue_order_id="VENUE-1"),
        "fill": _venue(
            reservation,
            venue_state="FILLED",
            venue_order_id="VENUE-1",
            cumulative_filled_quantity=prepared.intent.quantity,
            average_fill_price=25001.0,
        ),
    }[change]
    verdict = _query(reservation, venue)
    assert not verdict.consistent and verdict.blockers
    assert prepared.broker.lifecycle.state.value == "REQUESTED"
    assert store.saves == 2
    assert not owner.demo_transport_restart_status(reservation)["resubmit_allowed"]


@pytest.mark.parametrize(
    "change",
    [
        "account",
        "server",
        "symbol",
        "real",
        "unknown",
        "clock",
        "feed",
        "context_missing",
        "trade_disallowed",
        "tamper",
    ],
)
def test_current_bundle_cross_wiring_and_host_feed_vetoes_fail_closed(prepared_attempt, change):
    store, prepared = prepared_attempt
    reservation = evidence._reserve(store, prepared)
    raw = evidence._raw_bundle()
    context = raw["host_probe"]["demo_account_context"]
    if change == "account":
        context["account_fingerprint"] = "d" * 64
    elif change == "server":
        context["server"] = "OTHER"
    elif change == "symbol":
        context["symbol"] = "OTHER"
    elif change == "real":
        context["account_mode"] = "REAL"
    elif change == "unknown":
        context["account_mode"] = "UNKNOWN"
    elif change == "clock":
        raw["host_probe"]["clock_ok"] = False
    elif change == "feed":
        raw["closed_m5_feed"]["bars"] = []
    elif change == "context_missing":
        del raw["host_probe"]["demo_account_context"]
    elif change == "trade_disallowed":
        context["trade_allowed"] = False
    if change != "tamper":
        raw = evidence._seal(raw)
    else:
        raw["host_probe"]["clock_ok"] = False
    with pytest.raises(ValueError):
        _query(reservation, _venue(reservation), bundle_payload=raw)
    assert store.saves == 2


@pytest.mark.parametrize(
    "change",
    [
        "host_stale",
        "host_future",
        "venue_stale",
        "venue_future",
        "before_reservation",
        "feed_stale_at_evaluation",
    ],
)
def test_query_time_vetoes_fail_before_reconciliation(prepared_attempt, monkeypatch, change):
    store, prepared = prepared_attempt
    reservation = evidence._reserve(store, prepared)
    raw = evidence._raw_bundle()
    evaluated = reservation.evaluated_at
    venue = _venue(reservation)
    if change == "host_stale":
        evaluated += timedelta(seconds=31)
    elif change == "host_future":
        raw["host_probe"]["observed_at"] = (evaluated + timedelta(seconds=1)).isoformat()
        raw["closed_m5_feed"]["observed_at"] = raw["host_probe"]["observed_at"]
    elif change == "venue_stale":
        venue = replace(venue, observed_at=evaluated - timedelta(seconds=1))
    elif change == "venue_future":
        venue = replace(venue, observed_at=evaluated + timedelta(seconds=1))
    elif change == "before_reservation":
        evaluated -= timedelta(seconds=1)
    else:
        raw["closed_m5_feed"]["max_age_seconds"] = 0
        evaluated += timedelta(seconds=1)
    raw = evidence._seal(raw)

    def forbidden(**kwargs):
        raise AssertionError("invalid current evidence must not reach reconciliation")

    monkeypatch.setattr(owner, "reconcile_broker_order", forbidden)
    with pytest.raises(ValueError):
        _query(reservation, venue, bundle_payload=raw, evaluated_at=evaluated)
    assert store.saves == 2


def test_submit_scope_does_not_imply_query_scope(prepared_attempt):
    store, prepared = prepared_attempt
    authorization = replace(
        evidence._authorization(), allowed_actions=(DemoEvidenceAction.SUBMIT_EVIDENCE_ORDER,)
    )
    reservation = evidence._reserve(store, prepared, authorization=authorization)
    with pytest.raises(ValueError, match="ACTION_OUT_OF_SCOPE"):
        _query(reservation, _venue(reservation))
    assert store.saves == 2


def test_historical_reservation_load_does_not_renew_expired_query_scope(prepared_attempt):
    store, prepared = prepared_attempt
    reservation = evidence._reserve(store, prepared)
    restored = owner.load_reserved_demo_transport_attempt(
        store=store,
        key="attempt",
        expected_reservation_fingerprint=reservation.fingerprint,
    )
    evaluated = reservation.authorization.expires_at
    raw = evidence._raw_bundle()
    raw["host_probe"]["observed_at"] = evaluated.isoformat()
    raw["closed_m5_feed"]["observed_at"] = evaluated.isoformat()
    with pytest.raises(ValueError, match="AUTHORIZATION_EXPIRED"):
        _query(
            restored,
            _venue(restored, observed_at=evaluated),
            bundle_payload=evidence._seal(raw),
            evaluated_at=evaluated,
        )
    assert restored == reservation
    assert store.saves == 2
