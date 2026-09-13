"""Startup/reconnect without any repair, SDK initialization or state write."""
from dataclasses import replace
from datetime import timedelta
import pytest
from daxlab.runtime import mt5_demo_evidence_transport as owner
from daxlab.runtime.candidate_operator_query import build_operator_console_projection
from test_operator_console_inventory import sources, project
from test_mt5_demo_evidence_transport import prepared_attempt as prepared_attempt
import test_mt5_demo_evidence_transport as e
from test_mt5_demo_open_inventory import InventoryMt5


def replace_result(envelope, result):
    envelope['result'] = result.to_payload()
    envelope['result_fingerprint'] = result.fingerprint
    envelope.pop('sha256')
    envelope['sha256'] = owner._fingerprint(envelope)
    return envelope


@pytest.mark.parametrize('partial', [False, True])
def test_reconnect_fill_observed_but_unapplied_local_checkpoint_is_contradiction(prepared_attempt, partial):
    reservation, bundle, request, envelope = sources(prepared_attempt, False)
    mt5 = InventoryMt5()
    volume = request.requested_quantity / 2 if partial else request.requested_quantity
    mt5.history_orders = (e._order(request, mt5, state=mt5.ORDER_STATE_PARTIAL if partial else mt5.ORDER_STATE_FILLED,
                                  volume_current=request.requested_quantity-volume),)
    mt5.history_deals = (e._deal(request, volume=volume),)
    result = owner.query_mt5_demo_evidence(mt5=mt5, request=request, observed_at=request.query_evaluated_at)
    assert result.status is owner.DemoMt5LookupStatus.MATCHED
    v = project(reservation, bundle, request, replace_result(envelope, result))
    assert v['broker_lifecycle']['local_order_state'] == 'REQUESTED'
    assert v['broker_lifecycle']['fill_evidence']['cumulative_filled_quantity'] == volume
    assert v['reconciliation']['state'] == 'CONTRADICTION'
    assert v['system']['RECONCILIATION']['state'] == 'BLOCKED'
    assert 'CUMULATIVE_FILL_MISMATCH' in v['blockers']
    assert v['reserved_attempt']['resubmit_allowed'] is False


def test_expired_query_does_not_renew_original_inventory_or_grant_retry(prepared_attempt):
    reservation, bundle, request, envelope = sources(prepared_attempt, False)
    v = build_operator_console_projection(snapshot_payload=None, heartbeat_payload=None, bundle_payload=bundle,
        queried_at=request.query_evaluated_at+timedelta(seconds=360), reservation=reservation,
        expected_reservation_fingerprint=reservation.fingerprint, broker_evidence_payload=envelope,
        expected_broker_evidence_fingerprint=envelope['sha256'])
    assert v['reconciliation']['current_query_preflight'] == 'QUERY_REQUIRED'
    assert v['broker_inventory']['observed_at'] == owner.parse_demo_mt5_open_inventory(envelope['account_open_inventory']).collection_completed_at.isoformat()
    assert 'CURRENT_QUERY_SCOPE_OR_HOST_EVIDENCE_UNAVAILABLE' in v['blockers']
    assert v['order_execution_enabled'] is False


@pytest.mark.parametrize('field,value', [('native_volume',0.15), ('observed_open_price',25000.001)])
def test_native_inventory_precision_mismatch_blocks_without_rounding(prepared_attempt, field, value):
    reservation, bundle, request, envelope = sources(prepared_attempt)
    inventory = owner.parse_demo_mt5_open_inventory(envelope['account_open_inventory'])
    row = replace(inventory.rows[0], symbol=reservation.account_context.symbol, **{field:value})
    inventory = replace(inventory, rows=(row, inventory.rows[1]))
    envelope['account_open_inventory'] = inventory.to_payload()
    envelope.pop('sha256')
    envelope['sha256'] = owner._fingerprint(envelope)
    v = project(reservation, bundle, request, envelope)
    assert 'BROKER_INVENTORY_NATIVE_PRECISION_MISMATCH' in v['blockers']
    assert v['reconciliation']['state'] == 'CONTRADICTION'


def test_short_history_and_empty_inventory_never_assume_flat(prepared_attempt):
    reservation, bundle, request, envelope = sources(prepared_attempt, False)
    v = project(reservation, bundle, request, envelope)
    assert v['broker_lifecycle']['observed_lookup']['status'] == 'NOT_FOUND'
    assert v['reconciliation']['history_completeness'] == 'UNKNOWN'
    assert v['reconciliation']['state'] == 'QUERY_REQUIRED'
    assert v['reserved_attempt']['session_slot_release_allowed'] is False
