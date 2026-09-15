from __future__ import annotations

import json

import pytest

from daxlab.adapters.file_state_store import AtomicFileStateStore
from daxlab.domain.session_admission import (
    SessionAdmissionConsumptionAction,
    SessionAdmissionConsumptionState,
    SessionAdmissionPolicy,
    consume_session_admission,
    evaluate_session_admission,
)
from daxlab.state.session_admission import (
    build_session_admission_consumption_state_checkpoint,
    load_session_admission_consumption_state_checkpoint,
    save_session_admission_consumption_state_checkpoint,
    session_admission_consumption_state_checkpoint_from_bytes,
    session_admission_consumption_state_checkpoint_to_bytes,
)


SESSION_KEY = "2026-09-12-DE40-DAY"
CONSUMPTION_ID = "a" * 64


def _consumed_state():
    policy = SessionAdmissionPolicy.build(max_trades_per_session=2)
    initial = SessionAdmissionConsumptionState.build(session_key=SESSION_KEY)
    decision = evaluate_session_admission(
        policy=policy,
        observation=initial.observation,
    )
    transition = consume_session_admission(
        state=initial,
        policy=policy,
        decision=decision,
        session_key=SESSION_KEY,
        consumption_id=CONSUMPTION_ID,
    )
    return policy, decision, transition.state


def _checkpoint():
    _, _, state = _consumed_state()
    return build_session_admission_consumption_state_checkpoint(state=state)


def test_consumption_state_checkpoint_bytes_roundtrip_is_deterministic() -> None:
    checkpoint = _checkpoint()

    first = session_admission_consumption_state_checkpoint_to_bytes(checkpoint)
    restored = session_admission_consumption_state_checkpoint_from_bytes(first)
    second = session_admission_consumption_state_checkpoint_to_bytes(restored)

    assert restored == checkpoint
    assert restored.state == checkpoint.state
    assert restored.state.trades_admitted == 1
    assert restored.state.records[0].consumption_id == CONSUMPTION_ID
    assert first == second
    assert restored.execution_capability == "NONE"
    assert restored.order_execution_enabled is False


def test_consumption_state_checkpoint_reuses_atomic_file_state_store(tmp_path) -> None:
    checkpoint = _checkpoint()
    store = AtomicFileStateStore(tmp_path)

    assert load_session_admission_consumption_state_checkpoint(store, "session-ledger") is None
    save_session_admission_consumption_state_checkpoint(
        store,
        "session-ledger",
        checkpoint,
    )

    assert (
        load_session_admission_consumption_state_checkpoint(store, "session-ledger")
        == checkpoint
    )


def test_restored_consumption_state_preserves_idempotent_retry() -> None:
    policy, decision, state = _consumed_state()
    checkpoint = build_session_admission_consumption_state_checkpoint(state=state)
    restored = session_admission_consumption_state_checkpoint_from_bytes(
        session_admission_consumption_state_checkpoint_to_bytes(checkpoint)
    )

    replay = consume_session_admission(
        state=restored.state,
        policy=policy,
        decision=decision,
        session_key=SESSION_KEY,
        consumption_id=CONSUMPTION_ID,
    )

    assert replay.action is SessionAdmissionConsumptionAction.IDEMPOTENT_REPLAY
    assert replay.state == restored.state
    assert replay.state.trades_admitted == 1


def test_tampered_consumption_record_fails_closed() -> None:
    checkpoint = _checkpoint()
    raw = json.loads(session_admission_consumption_state_checkpoint_to_bytes(checkpoint))
    raw["state"]["records"][0]["consumption_id"] = "b" * 64
    tampered = (json.dumps(raw, sort_keys=True) + "\n").encode("utf-8")

    with pytest.raises(ValueError, match="consumption record fingerprint mismatch"):
        session_admission_consumption_state_checkpoint_from_bytes(tampered)


def test_duplicate_consumption_ids_fail_closed_on_restore() -> None:
    checkpoint = _checkpoint()
    raw = json.loads(session_admission_consumption_state_checkpoint_to_bytes(checkpoint))
    raw["state"]["records"].append(dict(raw["state"]["records"][0]))
    tampered = (json.dumps(raw, sort_keys=True) + "\n").encode("utf-8")

    with pytest.raises(ValueError, match="consumption IDs must be unique"):
        session_admission_consumption_state_checkpoint_from_bytes(tampered)


def test_tampered_state_fingerprint_fails_closed() -> None:
    checkpoint = _checkpoint()
    raw = json.loads(session_admission_consumption_state_checkpoint_to_bytes(checkpoint))
    raw["state"]["state_fingerprint"] = "f" * 64
    tampered = (json.dumps(raw, sort_keys=True) + "\n").encode("utf-8")

    with pytest.raises(ValueError, match="consumption state fingerprint mismatch"):
        session_admission_consumption_state_checkpoint_from_bytes(tampered)


def test_unknown_checkpoint_field_fails_closed() -> None:
    checkpoint = _checkpoint()
    raw = json.loads(session_admission_consumption_state_checkpoint_to_bytes(checkpoint))
    raw["unexpected"] = True
    tampered = (json.dumps(raw, sort_keys=True) + "\n").encode("utf-8")

    with pytest.raises(ValueError, match="checkpoint field set mismatch"):
        session_admission_consumption_state_checkpoint_from_bytes(tampered)


def test_missing_record_field_fails_closed() -> None:
    checkpoint = _checkpoint()
    raw = json.loads(session_admission_consumption_state_checkpoint_to_bytes(checkpoint))
    raw["state"]["records"][0].pop("record_fingerprint")
    tampered = (json.dumps(raw, sort_keys=True) + "\n").encode("utf-8")

    with pytest.raises(ValueError, match="consumption record field set mismatch"):
        session_admission_consumption_state_checkpoint_from_bytes(tampered)


def test_execution_safety_drift_fails_closed() -> None:
    checkpoint = _checkpoint()
    raw = json.loads(session_admission_consumption_state_checkpoint_to_bytes(checkpoint))
    raw["order_execution_enabled"] = True
    tampered = (json.dumps(raw, sort_keys=True) + "\n").encode("utf-8")

    with pytest.raises(ValueError, match="cannot authorize execution"):
        session_admission_consumption_state_checkpoint_from_bytes(tampered)


def test_checkpoint_fingerprint_drift_fails_closed() -> None:
    checkpoint = _checkpoint()
    raw = json.loads(session_admission_consumption_state_checkpoint_to_bytes(checkpoint))
    raw["checkpoint_fingerprint"] = "f" * 64
    tampered = (json.dumps(raw, sort_keys=True) + "\n").encode("utf-8")

    with pytest.raises(ValueError, match="checkpoint fingerprint mismatch"):
        session_admission_consumption_state_checkpoint_from_bytes(tampered)
