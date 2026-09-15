from dataclasses import replace
import json

import pytest

from daxlab.adapters.file_state_store import AtomicFileStateStore
from daxlab.runtime import demo_transport_attempt_reservation as owner
import test_demo_transport_attempt_reservation as evidence

prepared_attempt = evidence.prepared_attempt


def _load(store, reservation, key='attempt'):
    return owner.load_reserved_demo_transport_attempt(
        store=store, key=key,
        expected_reservation_fingerprint=reservation.fingerprint,
    )


def test_restart_preserves_exact_original_evidence_without_build_or_save(
    prepared_attempt, monkeypatch,
):
    store, prepared = prepared_attempt
    original = evidence._reserve(store, prepared)
    payload = store.load('attempt')

    def forbidden(*args, **kwargs):
        raise AssertionError('restart must not build, reserve or save')

    monkeypatch.setattr(owner, 'build_demo_transport_attempt_reservation', forbidden)
    monkeypatch.setattr(store, 'save', forbidden)
    restored = _load(store, original)
    assert restored == original
    assert restored.evaluated_at == original.evaluated_at
    assert restored.authorization_verdict == original.authorization_verdict
    assert owner.demo_transport_attempt_reservation_to_bytes(restored) == payload
    status = owner.demo_transport_restart_status(restored)
    assert status['intent_id'] == status['client_order_id'] == prepared.intent.intent_id
    assert status['venue_state'] == 'UNKNOWN'
    assert status['local_order_state'] == 'REQUESTED'
    assert status['required_next_action'] == 'QUERY_RECONCILE_REQUIRED'
    assert not status['resubmit_allowed']
    assert not status['session_slot_release_allowed']
    assert status['execution_capability'] == 'NONE'
    assert status['order_execution_enabled'] is False
    assert prepared.broker.lifecycle.venue_order_id is None
    assert prepared.broker.lifecycle.cumulative_filled_quantity == 0
    assert store.saves == 2


@pytest.mark.parametrize('case', ['missing', 'prepared', 'corrupt', 'cross_wired'])
def test_restart_fails_closed_without_replacing_state(prepared_attempt, case):
    store, prepared = prepared_attempt
    original = evidence._reserve(store, prepared)
    if case == 'missing':
        del store.values['attempt']
    elif case == 'prepared':
        store.values['attempt'] = owner.nextgen_prepared_checkpoint_to_bytes(prepared)
    elif case == 'corrupt':
        store.values['attempt'] = b'{}'
    else:
        alternative = replace(original, authorization=evidence._authorization(authorization_id='OTHER'),
                              authorization_fingerprint=evidence._authorization(authorization_id='OTHER').fingerprint,
                              authorization_verdict=owner.evaluate_demo_evidence_authorization(
                                  authorization=evidence._authorization(authorization_id='OTHER'),
                                  observed=original.account_context.to_observed_context(),
                                  requested_action=owner.DemoEvidenceAction.SUBMIT_EVIDENCE_ORDER,
                                  evaluated_at=original.evaluated_at, submissions_already_attempted=0,
                              ))
        store.values['attempt'] = owner.demo_transport_attempt_reservation_to_bytes(alternative)
    snapshot = dict(store.values)
    with pytest.raises(ValueError):
        _load(store, original)
    assert store.values == snapshot
    assert store.saves == 2


def test_restart_requires_explicit_valid_fingerprint_pin(prepared_attempt):
    store, prepared = prepared_attempt
    evidence._reserve(store, prepared)
    with pytest.raises(ValueError):
        owner.load_reserved_demo_transport_attempt(
            store=store, key='attempt', expected_reservation_fingerprint='not-a-sha',
        )
    assert store.saves == 2


@pytest.mark.parametrize('after_save', [False, True])
def test_crash_at_reservation_write_never_triggers_transport(
    prepared_attempt, monkeypatch, after_save,
):
    store, prepared = prepared_attempt
    save = store.save

    def crash(key, payload):
        if after_save:
            save(key, payload)
        raise OSError('simulated process interruption')

    monkeypatch.setattr(store, 'save', crash)
    with pytest.raises(OSError):
        evidence._reserve(store, prepared)
    monkeypatch.setattr(store, 'save', save)
    if after_save:
        reserved = owner.demo_transport_attempt_reservation_from_bytes(store.load('attempt'))
        assert _load(store, reserved) == reserved
        assert owner.demo_transport_restart_status(reserved)['resubmit_allowed'] is False
        assert evidence._reserve(store, prepared) == reserved
        assert store.saves == 2
    else:
        assert owner.nextgen_prepared_checkpoint_from_bytes(store.load('attempt')) == prepared
        assert store.saves == 1


def test_real_file_store_restart_preserves_one_payload(prepared_attempt, tmp_path):
    memory, prepared = prepared_attempt
    original = evidence._reserve(memory, prepared)
    store = AtomicFileStateStore(tmp_path)
    store.save('attempt', memory.load('attempt'))
    restarted = AtomicFileStateStore(tmp_path)
    assert _load(restarted, original) == original
    assert [p.name for p in tmp_path.iterdir()] == ['attempt.bin']
    raw = json.loads(restarted.load('attempt'))
    assert raw['status'] == 'TRANSPORT_ATTEMPT_RESERVED'
