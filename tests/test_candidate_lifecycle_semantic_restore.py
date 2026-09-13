from dataclasses import replace
from datetime import timedelta
import json
from unittest.mock import Mock

import pytest

from daxlab.runtime.candidate_active_trade_state import candidate_active_trade_payload, parse_candidate_active_trade_payload
from daxlab.runtime.candidate_mt5_feed import mt5_bar_to_candidate_candle
from daxlab.runtime.candidate_shadow_checkpoint import candidate_shadow_checkpoint_payload, parse_candidate_shadow_checkpoint_payload
from daxlab.runtime.candidate_shadow_host_cycle import run_cand001_shadow_host_cycle
from daxlab.runtime.candidate_state import candidate_virtual_lifecycle_payload, parse_candidate_virtual_lifecycle_payload
from daxlab.runtime.candidate_virtual_lifecycle import advance_cand001_virtual_lifecycle
from daxlab.runtime.paper_contracts import Side
from test_candidate_shadow_host_cycle import _bars, _bundle, _rehash


CASES = [
    'fill_before_request', 'close_before_fill', 'progress_before_fill', 'progress_before_close',
    'buy_stop_equal', 'buy_stop_above', 'buy_target_equal', 'buy_target_below',
    'sell_stop_equal', 'sell_stop_below', 'sell_target_equal', 'sell_target_above',
]


def _fixture():
    bars = _bars()
    first = run_cand001_shadow_host_cycle(_bundle(bars[:5], marker='1'), single_instance_lock_held=True)
    active = first.runtime.state.active_trade
    candle = mt5_bar_to_candidate_candle(bars[-1], broker_symbol='DE40', observed_at=bars[-1].open_time + timedelta(minutes=5, seconds=1))
    closed = advance_cand001_virtual_lifecycle(active.lifecycle, candle)
    return first, active, closed


def _mutation(case, opened, closed):
    state = closed if case in ('close_before_fill', 'progress_before_close') else opened
    if case == 'fill_before_request':
        changes = {'filled_at': state.requested_at - timedelta(minutes=5)}
    elif case == 'close_before_fill':
        changes = {'closed_at': state.filled_at - timedelta(minutes=5)}
    elif case == 'progress_before_fill':
        changes = {'last_close_time': state.filled_at - timedelta(minutes=5)}
    elif case == 'progress_before_close':
        changes = {'last_close_time': state.closed_at - timedelta(minutes=5)}
    else:
        side, field, relation = case.split('_')
        delta = {'equal': 0, 'above': 1, 'below': -1}[relation]
        changes = {'side': Side.BUY if side == 'buy' else Side.SELL,
                   field + '_price': state.requested_price + delta}
    return state, changes


def _wire_changes(changes):
    return {key: value.isoformat() if hasattr(value, 'isoformat') else value.value if isinstance(value, Side) else value for key, value in changes.items()}


@pytest.mark.parametrize('case', CASES)
@pytest.mark.parametrize('boundary', ['direct', 'persistence', 'active', 'checkpoint'])
def test_invalid_lifecycle_fails_at_every_restore_boundary(case, boundary):
    first, active, closed = _fixture()
    state, changes = _mutation(case, active.lifecycle, closed)
    if boundary == 'direct':
        with pytest.raises(ValueError, match='precede|geometry'):
            replace(state, **changes)
        return
    coherent_active = replace(active, lifecycle=state)
    if boundary == 'persistence':
        payload = candidate_virtual_lifecycle_payload(state)
        virtual = payload
    elif boundary == 'active':
        payload = candidate_active_trade_payload(coherent_active)
        virtual = payload['virtual_lifecycle']
    else:
        payload = candidate_shadow_checkpoint_payload(replace(first.runtime.state, active_trade=coherent_active), run_manifest=first.manifest)
        virtual = payload['active_trade']['virtual_lifecycle']
    virtual['lifecycle'].update(_wire_changes(changes))
    _rehash(virtual)
    if boundary == 'active':
        _rehash(payload)
    elif boundary == 'checkpoint':
        _rehash(payload['active_trade'])
        _rehash(payload)
    wire = json.loads(json.dumps(payload, allow_nan=False))
    with pytest.raises(ValueError, match='precede|geometry'):
        if boundary == 'persistence':
            parse_candidate_virtual_lifecycle_payload(wire)
        elif boundary == 'active':
            parse_candidate_active_trade_payload(wire)
        else:
            parse_candidate_shadow_checkpoint_payload(wire, run_manifest=first.manifest)


@pytest.mark.parametrize('case', CASES)
def test_invalid_checkpoint_never_reaches_host_processing(case, monkeypatch):
    first, active, closed = _fixture()
    state, changes = _mutation(case, active.lifecycle, closed)
    payload = candidate_shadow_checkpoint_payload(replace(first.runtime.state, active_trade=replace(active, lifecycle=state)), run_manifest=first.manifest)
    virtual = payload['active_trade']['virtual_lifecycle']
    virtual['lifecycle'].update(_wire_changes(changes))
    for envelope in (virtual, payload['active_trade'], payload):
        _rehash(envelope)
    runtime = Mock(side_effect=AssertionError('processing reached before restore rejection'))
    monkeypatch.setattr('daxlab.runtime.candidate_shadow_host_cycle.run_cand001_mt5_shadow', runtime)
    with pytest.raises(ValueError, match='precede|geometry'):
        run_cand001_shadow_host_cycle(_bundle(_bars(), marker='2'), single_instance_lock_held=True, checkpoint_payload=payload)
    runtime.assert_not_called()


@pytest.mark.parametrize('count', [4, 5, 6])
def test_valid_pending_open_closed_checkpoint_and_restart(count):
    first = run_cand001_shadow_host_cycle(_bundle(_bars()[:count], marker='1'), single_instance_lock_held=True)
    payload = json.loads(json.dumps(first.checkpoint_payload, allow_nan=False))
    assert parse_candidate_shadow_checkpoint_payload(payload, run_manifest=first.manifest) == first.runtime.state
    resumed = run_cand001_shadow_host_cycle(_bundle(_bars(), marker='2'), single_instance_lock_held=True, checkpoint_payload=payload)
    control = run_cand001_shadow_host_cycle(_bundle(_bars(), marker='2'), single_instance_lock_held=True)
    assert resumed.checkpoint_payload == control.checkpoint_payload
    assert first.outcomes_to_publish + resumed.outcomes_to_publish == control.outcomes_to_publish
    assert control.outcomes_to_publish[0].outcome_id == '7f357d4a1e7f725e833e37749433b7ea39580419a2008c535aff0818d353c1e3'
    assert control.outcomes_to_publish[0].dated_outcome.outcome_sha256 == '215f5dc1d9897cddd20d04f4bbef6615abd1230bbc5293a121a5a096af0b06cd'


def test_valid_equal_times_and_gap_exit():
    _, active, _ = _fixture()
    opened = active.lifecycle
    assert opened.filled_at == opened.requested_at
    equal_open = replace(opened, last_close_time=opened.filled_at)
    assert parse_candidate_virtual_lifecycle_payload(candidate_virtual_lifecycle_payload(equal_open)) == equal_open
    bars = _bars()
    candle = mt5_bar_to_candidate_candle(replace(bars[-1], open=120., high=121., low=119., close=120.), broker_symbol='DE40', observed_at=bars[-1].open_time + timedelta(minutes=5, seconds=1))
    gap = advance_cand001_virtual_lifecycle(opened, candle)
    assert gap.closed_at == candle.event_time
    equal_closed = replace(gap, last_close_time=gap.closed_at)
    assert parse_candidate_virtual_lifecycle_payload(candidate_virtual_lifecycle_payload(equal_closed)) == equal_closed
