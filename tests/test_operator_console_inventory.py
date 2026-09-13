"""Reuse actual export/strict codecs with offline SDK fixtures."""
from copy import deepcopy
import json

import pytest

import test_mt5_demo_evidence_transport as e
from test_mt5_demo_open_inventory import InventoryMt5, row
from test_mt5_demo_evidence_lookup_script import _load_script
from test_demo_transport_query_request import FixedClock
from daxlab.runtime import mt5_demo_evidence_transport as owner
from daxlab.runtime.candidate_operator_query import build_operator_console_projection
import test_demo_transport_attempt_reservation as r

prepared_attempt = e.prepared_attempt


def sources(prepared_attempt, external=True):
    store, _, reservation, _, request = e._lookup(prepared_attempt)
    bundle = r._raw_bundle(account_fingerprint=e.ACCOUNT_FINGERPRINT)
    mt5 = InventoryMt5()
    if external:
        mt5.open_orders = (row(),)
        mt5.positions = (row(ticket=456),)
    envelope = _load_script().execute_reserved_readonly_lookup(
        mt5=mt5, store=store, attempt_key='attempt',
        expected_reservation_fingerprint=reservation.fingerprint,
        request_payload=owner.demo_mt5_lookup_request_to_payload(request), bundle_payload=bundle,
        observed_at=request.query_evaluated_at, inventory_clock=FixedClock(request.query_evaluated_at),
    )
    return reservation, bundle, request, envelope


def project(reservation, bundle, request, envelope):
    return build_operator_console_projection(
        snapshot_payload=None, heartbeat_payload=None, bundle_payload=bundle,
        queried_at=request.query_evaluated_at,
        reservation=reservation, expected_reservation_fingerprint=reservation.fingerprint,
        broker_evidence_payload=envelope, expected_broker_evidence_fingerprint=envelope['sha256'],
    )


def test_account_wide_manual_inventory_visible_without_local_state_mutation(prepared_attempt):
    reservation, bundle, request, envelope = sources(prepared_attempt)
    original = reservation.fingerprint
    view = project(reservation, bundle, request, envelope)
    assert len(view['broker_inventory']['rows']) == 2
    assert view['system']['INVENTORY']['state'] == 'BLOCKED'
    assert 'ACCOUNT_HAS_OPEN_ORDERS' in view['blockers']
    assert 'ACCOUNT_HAS_OPEN_POSITIONS' in view['blockers']
    assert view['broker_lifecycle']['local_order_state'] == 'REQUESTED'
    assert view['reconciliation']['state'] == 'QUERY_REQUIRED'
    assert reservation.fingerprint == original
    assert str(e.LOGIN) not in json.dumps(view)
    assert view['reconciliation']['account_inventory_complete'] is False


def test_empty_observed_inventory_never_green_without_reviewed_freshness(prepared_attempt):
    reservation, bundle, request, envelope = sources(prepared_attempt, False)
    view = project(reservation, bundle, request, envelope)
    assert view['broker_inventory']['rows'] == []
    assert view['broker_inventory']['open_queries_completed'] is True
    assert view['broker_inventory']['state'] == 'UNKNOWN'
    assert view['broker_inventory']['freshness_threshold'] == 'UNVERIFIED_THRESHOLD'


@pytest.mark.parametrize('field,value', [('reservation_fingerprint','a'*64), ('execution_capability','DEMO'), ('order_execution_enabled',True), ('request_fingerprint','b'*64), ('extra',{'password':'SENTINEL'})])
def test_rehashed_malicious_envelope_still_fails_closed(prepared_attempt, field, value):
    reservation, bundle, request, envelope = sources(prepared_attempt)
    envelope[field] = value
    envelope.pop('sha256')
    envelope['sha256'] = owner._fingerprint(envelope)
    with pytest.raises(ValueError):
        project(reservation, bundle, request, envelope)


def test_inventory_from_other_observation_cycle_is_stale(prepared_attempt):
    reservation, bundle, request, envelope = sources(prepared_attempt)
    envelope['current_windows_bundle_fingerprint'] = 'a'*64
    envelope.pop('sha256')
    envelope['sha256'] = owner._fingerprint(envelope)
    view = project(reservation, bundle, request, envelope)
    assert view['broker_inventory']['state'] == 'STALE'
    assert view['reconciliation']['state'] == 'STALE'


def test_lookup_result_codec_rejects_missing_report_fields_and_unsafe_flags(prepared_attempt):
    _, _, _, envelope = sources(prepared_attempt)
    assert owner.demo_mt5_lookup_result_from_payload(envelope['result']).to_payload() == envelope['result']
    for field in ('observed_at', 'status', 'venue_observation'):
        raw = deepcopy(envelope['result'])
        raw.pop(field)
        with pytest.raises(ValueError):
            owner.demo_mt5_lookup_result_from_payload(raw)
    raw = deepcopy(envelope['result'])
    raw['resubmit_allowed'] = 0
    with pytest.raises(ValueError):
        owner.demo_mt5_lookup_result_from_payload(raw)
