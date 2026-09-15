"""Offline SDK fixtures; no real broker inventory or execution evidence."""
from copy import deepcopy
from datetime import timedelta
import json
from types import SimpleNamespace

import pytest

from daxlab.runtime import mt5_demo_evidence_transport as owner
from test_demo_transport_query_request import FixedClock
import test_mt5_demo_evidence_transport as e
from test_mt5_demo_evidence_lookup_script import _load_script
import test_demo_transport_attempt_reservation as reservation_evidence

prepared_attempt = e.prepared_attempt


class InventoryMt5(e.FakeMt5):
    POSITION_TYPE_BUY = 0
    POSITION_TYPE_SELL = 1
    ORDER_TYPE_BUY = 0
    ORDER_TYPE_SELL = 1
    ORDER_TYPE_BUY_LIMIT = 2
    ORDER_TYPE_SELL_LIMIT = 3
    ORDER_TYPE_BUY_STOP = 4
    ORDER_TYPE_SELL_STOP = 5
    ORDER_TYPE_BUY_STOP_LIMIT = 6
    ORDER_TYPE_SELL_STOP_LIMIT = 7

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.positions = ()

    def orders_get(self, *, symbol=None):
        self.calls.append(('orders_get', symbol))
        return self.open_orders

    def positions_get(self):
        self.calls.append(('positions_get',))
        return self.positions


def row(**changes):
    return SimpleNamespace(**(dict(ticket=123, symbol='OTHER_SYMBOL', type=0, volume=1,
                                 volume_current=1, price_open=25000, magic=999,
                                 comment='password=never-export') | changes))


def query(mt5, request):
    return owner.query_mt5_demo_open_inventory(mt5=mt5, request=request, clock=FixedClock(request.query_evaluated_at))


def test_empty_success_is_open_queries_only_never_reconciliation_or_risk_zero(prepared_attempt):
    *_, request = e._lookup(prepared_attempt)
    mt5 = InventoryMt5()
    observation = query(mt5, request)
    payload = observation.to_payload()
    assert observation.status == 'OBSERVED'
    assert payload['open_queries_completed'] is True
    assert payload['broker_reconciliation_complete'] is False
    assert payload['history_completeness'] == 'UNKNOWN'
    assert payload['risk_loss_values'] is None
    assert payload['collection_is_atomic'] is False
    assert payload['time_source'] == 'LOCAL_OBSERVATION_CLOCK_NOT_BROKER_CLOCK'
    assert owner.parse_demo_mt5_open_inventory(payload) == observation
    assert mt5.calls == [('account_info',), ('orders_get', None), ('positions_get',), ('account_info',)]


def test_foreign_orders_and_existing_positions_are_visible_and_blocking_without_claiming(prepared_attempt):
    *_, request = e._lookup(prepared_attempt)
    mt5 = InventoryMt5()
    mt5.open_orders = (row(),)
    mt5.positions = (row(ticket=456),)
    observation = query(mt5, request)
    assert observation.blockers == ('ACCOUNT_HAS_OPEN_ORDERS', 'ACCOUNT_HAS_OPEN_POSITIONS')
    assert all(r.transport_tag_matches_attempt is False for r in observation.rows)
    text = json.dumps(observation.to_payload())
    assert str(e.LOGIN) not in text
    assert 'password' not in text
    assert 'profit' not in text and 'margin' not in text
    assert owner.parse_demo_mt5_open_inventory(observation.to_payload()) == observation


@pytest.mark.parametrize('method', ['orders_get', 'positions_get'])
def test_failed_inventory_leg_cannot_be_empty_account_truth(prepared_attempt, method):
    *_, request = e._lookup(prepared_attempt)
    mt5 = InventoryMt5()
    setattr(mt5, method, lambda **kwargs: None)
    result = query(mt5, request)
    assert result.status == 'BLOCKED'
    assert result.rows == ()
    assert result.to_payload()['open_queries_completed'] is False
    assert result.blockers == ('INVENTORY_OPEN_QUERY_FAILED',)


@pytest.mark.parametrize('field,value', [('volume', float('nan')), ('volume', float('inf')), ('volume', -1), ('price_open', 0), ('price_open', float('-inf')), ('ticket', True), ('type', 999)])
def test_invalid_position_is_blocked_instead_of_silently_dropped(prepared_attempt, field, value):
    *_, request = e._lookup(prepared_attempt)
    mt5 = InventoryMt5()
    mt5.positions = (row(**{field: value}),)
    result = query(mt5, request)
    assert result.status == 'BLOCKED' and result.rows == ()
    assert result.blockers == ('INVENTORY_OBJECT_INVALID',)


def test_duplicate_open_objects_are_idempotent_and_contradiction_is_blocked(prepared_attempt):
    *_, request = e._lookup(prepared_attempt)
    mt5 = InventoryMt5()
    mt5.positions = (row(), row())
    assert len(query(mt5, request).rows) == 1
    mt5.positions = (row(), row(volume=2))
    assert query(mt5, request).blockers == ('INVENTORY_DUPLICATE_OBJECT_CONTRADICTION',)


def test_account_switch_and_real_account_never_yield_demo_inventory(prepared_attempt):
    *_, request = e._lookup(prepared_attempt)
    mt5 = InventoryMt5(account_mode=e.FakeMt5.ACCOUNT_TRADE_MODE_REAL)
    assert query(mt5, request).status == 'BLOCKED'
    assert mt5.calls == [('account_info',)]

    class Switch(InventoryMt5):
        def positions_get(self):
            self.account.server = 'Other-Demo'
            return super().positions_get()

    assert query(Switch(), request).blockers == ('INVENTORY_ACCOUNT_CONTEXT_CHANGED_OR_UNAVAILABLE',)


@pytest.mark.parametrize('field,value', [('broker_reconciliation_complete', True), ('risk_loss_values', 0), ('collection_is_atomic', True), ('order_execution_enabled', True), ('schema_version', 'OTHER')])
def test_rehashed_inventory_cannot_promote_missing_evidence(prepared_attempt, field, value):
    *_, request = e._lookup(prepared_attempt)
    payload = deepcopy(query(InventoryMt5(), request).to_payload())
    payload[field] = value
    payload.pop('observation_fingerprint')
    payload['observation_fingerprint'] = owner._fingerprint(payload)
    with pytest.raises(ValueError):
        owner.parse_demo_mt5_open_inventory(payload)


def test_optional_inventory_uses_same_existing_export_and_never_saves_attempt(prepared_attempt):
    store, _, reservation, _, request = e._lookup(prepared_attempt)
    original = store.load('attempt')
    saves = store.saves
    args = dict(mt5=InventoryMt5(), store=store, attempt_key='attempt',
                expected_reservation_fingerprint=reservation.fingerprint,
                bundle_payload=reservation_evidence._raw_bundle(account_fingerprint=e.ACCOUNT_FINGERPRINT),
                request_payload=owner.demo_mt5_lookup_request_to_payload(request), observed_at=request.query_evaluated_at)
    script = _load_script()
    legacy = script.execute_reserved_readonly_lookup(**args)
    assert 'account_open_inventory' not in legacy
    enriched = script.execute_reserved_readonly_lookup(**args, inventory_clock=FixedClock(request.query_evaluated_at))
    assert enriched['result'] == legacy['result']
    assert enriched['result_fingerprint'] == legacy['result_fingerprint']
    assert owner.parse_demo_mt5_open_inventory(enriched['account_open_inventory']).status == 'OBSERVED'
    assert store.load('attempt') == original and store.saves == saves


def test_expired_or_regressing_observation_clock_cannot_invent_new_time(prepared_attempt):
    *_, request = e._lookup(prepared_attempt)
    mt5 = InventoryMt5()
    result = owner.query_mt5_demo_open_inventory(mt5=mt5, request=request, clock=FixedClock(request.history_to + timedelta(seconds=1)))
    assert result.status == 'BLOCKED' and not mt5.calls

    class RegressingClock:
        values = iter((request.query_evaluated_at, request.query_evaluated_at - timedelta(seconds=1)))
        def now(self):
            return next(self.values)

    with pytest.raises(ValueError, match='clock regressed'):
        owner.query_mt5_demo_open_inventory(mt5=mt5, request=request, clock=RegressingClock())


def test_attempt_tag_match_is_not_position_ownership_or_reconciliation(prepared_attempt):
    *_, request = e._lookup(prepared_attempt)
    mt5 = InventoryMt5()
    mt5.positions = (row(symbol=request.identity.symbol, magic=request.identity.magic, comment=request.identity.comment),)
    result = query(mt5, request)
    assert result.rows[0].transport_tag_matches_attempt is True
    assert result.blockers == ('ACCOUNT_HAS_OPEN_POSITIONS',)
    assert result.to_payload()['broker_reconciliation_complete'] is False


def test_rehashed_numeric_false_does_not_pass_strict_inventory_flags(prepared_attempt):
    *_, request = e._lookup(prepared_attempt)
    payload = query(InventoryMt5(), request).to_payload()
    payload['order_execution_enabled'] = 0
    payload.pop('observation_fingerprint')
    payload['observation_fingerprint'] = owner._fingerprint(payload)
    with pytest.raises(ValueError, match='flags must be bool'):
        owner.parse_demo_mt5_open_inventory(payload)
