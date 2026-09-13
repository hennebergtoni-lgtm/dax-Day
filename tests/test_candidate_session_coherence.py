from copy import deepcopy
from dataclasses import replace
from datetime import timedelta
import json
from unittest.mock import Mock

import pytest

from daxlab.runtime.candidate_admission import Cand001AdmissionState
from daxlab.runtime.candidate_pipeline import Cand001PipelineState, process_cand001_candle
from daxlab.runtime.candidate_signal import Cand001SignalState
from daxlab.runtime.candidate_shadow_checkpoint import parse_candidate_shadow_checkpoint_payload
from daxlab.runtime.candidate_shadow_host_cycle import run_cand001_shadow_host_cycle
from daxlab.runtime.candidate_state import candidate_state_payload, parse_candidate_state_payload
from daxlab.runtime.contracts import DataQualityState
from daxlab.strategies.cand001 import Cand001PipelineStateCodec
from test_candidate_shadow_host_cycle import _bars, _bundle, _rehash
from test_candidate_operator_context import _bar, _step


@pytest.mark.parametrize(('signal_date', 'admission_date'), [
    ('2026-09-11', '2026-09-10'), ('2026-09-10', '2026-09-11'),
    (None, '2026-09-11'), ('2026-09-11', None),
])
@pytest.mark.parametrize('count', [0, 1])
def test_pipeline_rejects_incoherent_sessions(signal_date, admission_date, count):
    with pytest.raises(ValueError):
        Cand001PipelineState(
            signal=Cand001SignalState(session_date=signal_date),
            admission=Cand001AdmissionState(session_date=admission_date, trades_admitted=count),
        )


@pytest.mark.parametrize('count', [-1, 2, 10, True, False, 0.0, 1.0, float('nan'), float('inf'), float('-inf')])
def test_admission_count_rejects_noncanonical_values_direct_and_restore(count):
    with pytest.raises(ValueError, match='trades_admitted'):
        Cand001AdmissionState(session_date='2026-09-11', trades_admitted=count)
    payload = candidate_state_payload(Cand001PipelineState(
        signal=Cand001SignalState(session_date='2026-09-11'),
        admission=Cand001AdmissionState(session_date='2026-09-11'),
    ))
    payload['state']['admission']['trades_admitted'] = count
    _rehash(payload)
    with pytest.raises(ValueError, match='trades_admitted'):
        parse_candidate_state_payload(payload)


@pytest.mark.parametrize('count', [None, 0, 1])
def test_valid_initial_and_same_session_roundtrip(count):
    state = Cand001PipelineState() if count is None else Cand001PipelineState(
        signal=Cand001SignalState(session_date='2026-09-11'),
        admission=Cand001AdmissionState(session_date='2026-09-11', trades_admitted=count),
    )
    assert parse_candidate_state_payload(candidate_state_payload(state)) == state
    codec = Cand001PipelineStateCodec()
    assert codec.decode(codec.encode(state)) == state


def test_absent_session_requires_true_initial_signal():
    with pytest.raises(ValueError, match='initial signal'):
        Cand001PipelineState(signal=Cand001SignalState(or_high=103, or_low=98))


def test_completed_trade_mixed_session_checkpoint_rejected_before_strategy(monkeypatch):
    bars = _bars()
    first = run_cand001_shadow_host_cycle(_bundle(bars, marker='1'), single_instance_lock_held=True)
    assert first.runtime.state.active_trade is None
    assert first.runtime.state.pipeline.admission.trades_admitted == 1
    assert len(first.runtime.state.publication.published_intent_ids) == 1
    next_bar = replace(bars[-1], open_time=bars[-1].open_time + timedelta(minutes=5),
                       open=113., high=115., low=112., close=114.)
    bundle = _bundle((*bars, next_bar), marker='2')
    control = run_cand001_shadow_host_cycle(bundle, single_instance_lock_held=True,
                                          checkpoint_payload=first.checkpoint_payload)
    assert not control.intents_to_publish
    assert control.runtime.candidate_feed_result.steps[-1].pipeline_result.admission.status.value == 'SESSION_LIMIT'
    payload = deepcopy(first.checkpoint_payload)
    payload['pipeline_state']['state']['admission']['session_date'] = '2026-09-10'
    _rehash(payload['pipeline_state'])
    _rehash(payload)
    wire = json.loads(json.dumps(payload, allow_nan=False))
    with pytest.raises(ValueError, match='session mismatch'):
        parse_candidate_shadow_checkpoint_payload(wire, run_manifest=first.manifest)
    strategy = Mock(side_effect=AssertionError('strategy reached'))
    monkeypatch.setattr('daxlab.runtime.candidate_shadow_host_cycle.run_cand001_mt5_shadow', strategy)
    with pytest.raises(ValueError, match='session mismatch'):
        run_cand001_shadow_host_cycle(bundle, single_instance_lock_held=True, checkpoint_payload=wire)
    strategy.assert_not_called()


@pytest.mark.parametrize('rejected', ['initial_unsafe', 'next_day_unsafe', 'previous_day', 'duplicate'])
def test_rejected_bars_preserve_both_session_states(rejected):
    candle = _bar(9, 0, open_=100, high=102, low=99, close=101)
    state = Cand001PipelineState() if rejected == 'initial_unsafe' else _step(Cand001PipelineState(), candle).state
    if rejected in ('initial_unsafe', 'next_day_unsafe'):
        candle = replace(candle, quality_state=DataQualityState.GAP)
    delta = timedelta(days=1 if rejected == 'next_day_unsafe' else -1 if rejected == 'previous_day' else 0)
    candle = replace(candle, event_time=candle.event_time + delta,
                     close_time=candle.close_time + delta, received_at=candle.received_at + delta)
    result = _step(state, candle)
    assert result.state == state
    assert parse_candidate_state_payload(candidate_state_payload(result.state)) == state


def test_real_next_session_resets_both_states_and_preserves_restart_parity():
    bars = _bars()
    first = run_cand001_shadow_host_cycle(_bundle(bars, marker='1'), single_instance_lock_held=True)
    state = first.runtime.state.pipeline
    next_day = _bar(9, 0, open_=100, high=102, low=99, close=101)
    next_day = replace(next_day, event_time=next_day.event_time + timedelta(days=1),
                       close_time=next_day.close_time + timedelta(days=1),
                       received_at=next_day.received_at + timedelta(days=1))
    restored = parse_candidate_state_payload(candidate_state_payload(state))
    result = process_cand001_candle(restored, next_day, observed_at=next_day.received_at)
    assert result == process_cand001_candle(state, next_day, observed_at=next_day.received_at)
    assert result.state.signal.session_date == result.state.admission.session_date == '2026-09-12'
    assert result.state.admission.trades_admitted == 0
    assert result.state.signal.or_slots == ('09:00',)


def test_outside_session_midnight_bar_uses_canonical_event_session():
    candle = _bar(23, 55, open_=100, high=102, low=99, close=101)
    result = _step(Cand001PipelineState(), candle)
    assert result.decision.final_action.value == 'NO_TRADE'
    assert result.state.signal.session_date == result.state.admission.session_date == '2026-09-11'
    assert result.state.admission.trades_admitted == 0
    assert parse_candidate_state_payload(candidate_state_payload(result.state)) == result.state
