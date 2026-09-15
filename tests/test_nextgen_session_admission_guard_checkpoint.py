from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json

import pytest

from daxlab.adapters.file_state_store import AtomicFileStateStore
from daxlab.domain.session_admission import (
    SessionAdmissionConsumptionState,
    SessionAdmissionPolicy,
    consume_session_admission,
    evaluate_session_admission,
)
from daxlab.state.session_admission import (
    SessionAdmissionGuardCheckpoint,
    build_session_admission_guard_checkpoint,
    load_session_admission_guard_checkpoint,
    save_session_admission_guard_checkpoint,
    session_admission_guard_checkpoint_from_bytes,
    session_admission_guard_checkpoint_to_bytes,
)


UTC = timezone.utc
SESSION_KEY = "2026-09-12-DE40-DAY"
OBSERVED_AT = datetime(2026, 9, 12, 12, 0, tzinfo=UTC)
CONSUMPTION_ID = "a" * 64


def _policy_and_state():
    policy = SessionAdmissionPolicy.build(max_trades_per_session=2)
    initial = SessionAdmissionConsumptionState.build(session_key=SESSION_KEY)
    decision = evaluate_session_admission(
        policy=policy,
        observation=initial.observation,
    )
    consumed = consume_session_admission(
        state=initial,
        policy=policy,
        decision=decision,
        session_key=SESSION_KEY,
        consumption_id=CONSUMPTION_ID,
    )
    return policy, consumed.state


def _checkpoint(*, observed_at: datetime = OBSERVED_AT):
    policy, state = _policy_and_state()
    checkpoint = build_session_admission_guard_checkpoint(
        policy_fingerprint=policy.policy_fingerprint,
        state=state,
        observed_at=observed_at,
    )
    return policy, state, checkpoint


def test_guard_checkpoint_binds_policy_state_observation_and_time() -> None:
    policy, state, checkpoint = _checkpoint()

    assert checkpoint.policy_fingerprint == policy.policy_fingerprint
    assert checkpoint.state == state
    assert checkpoint.observation == state.observation
    assert checkpoint.observation.trades_admitted == 1
    assert checkpoint.observed_at == OBSERVED_AT
    assert checkpoint.execution_capability == "NONE"
    assert checkpoint.order_execution_enabled is False


def test_guard_checkpoint_bytes_roundtrip_is_deterministic() -> None:
    _, _, checkpoint = _checkpoint()

    first = session_admission_guard_checkpoint_to_bytes(checkpoint)
    restored = session_admission_guard_checkpoint_from_bytes(first)
    second = session_admission_guard_checkpoint_to_bytes(restored)

    assert restored == checkpoint
    assert first == second


def test_guard_checkpoint_uses_one_atomic_file_state_store_key(tmp_path) -> None:
    _, _, checkpoint = _checkpoint()
    store = AtomicFileStateStore(tmp_path)

    assert load_session_admission_guard_checkpoint(store, "session-guard") is None
    save_session_admission_guard_checkpoint(store, "session-guard", checkpoint)

    assert load_session_admission_guard_checkpoint(store, "session-guard") == checkpoint
    assert sorted(path.name for path in tmp_path.iterdir()) == ["session-guard.bin"]


def test_guard_restore_never_refreshes_observed_at(tmp_path) -> None:
    _, _, checkpoint = _checkpoint(observed_at=OBSERVED_AT - timedelta(minutes=5))
    store = AtomicFileStateStore(tmp_path)
    save_session_admission_guard_checkpoint(store, "session-guard", checkpoint)

    restored = load_session_admission_guard_checkpoint(store, "session-guard")

    assert restored is not None
    assert restored.observed_at == OBSERVED_AT - timedelta(minutes=5)


def test_guard_rejects_valid_but_mismatched_observation_and_state() -> None:
    policy, state, checkpoint = _checkpoint()
    empty = SessionAdmissionConsumptionState.build(session_key=SESSION_KEY)

    with pytest.raises(ValueError, match="guard observation/state mismatch"):
        SessionAdmissionGuardCheckpoint(
            policy_fingerprint=policy.policy_fingerprint,
            state=state,
            observation=empty.observation,
            observed_at=OBSERVED_AT,
            checkpoint_fingerprint=checkpoint.checkpoint_fingerprint,
        )


def test_tampered_consumption_record_fails_closed() -> None:
    _, _, checkpoint = _checkpoint()
    raw = json.loads(session_admission_guard_checkpoint_to_bytes(checkpoint))
    raw["state"]["records"][0]["consumption_id"] = "b" * 64
    tampered = (json.dumps(raw, sort_keys=True) + "\n").encode("utf-8")

    with pytest.raises(ValueError, match="consumption record fingerprint mismatch"):
        session_admission_guard_checkpoint_from_bytes(tampered)


def test_tampered_policy_fingerprint_fails_closed() -> None:
    _, _, checkpoint = _checkpoint()
    raw = json.loads(session_admission_guard_checkpoint_to_bytes(checkpoint))
    raw["policy_fingerprint"] = "f" * 64
    tampered = (json.dumps(raw, sort_keys=True) + "\n").encode("utf-8")

    with pytest.raises(ValueError, match="guard checkpoint fingerprint mismatch"):
        session_admission_guard_checkpoint_from_bytes(tampered)


def test_tampered_observation_fails_closed() -> None:
    _, _, checkpoint = _checkpoint()
    raw = json.loads(session_admission_guard_checkpoint_to_bytes(checkpoint))
    raw["observation"]["trades_admitted"] = 0
    tampered = (json.dumps(raw, sort_keys=True) + "\n").encode("utf-8")

    with pytest.raises(ValueError):
        session_admission_guard_checkpoint_from_bytes(tampered)


def test_tampered_observed_at_fails_closed() -> None:
    _, _, checkpoint = _checkpoint()
    raw = json.loads(session_admission_guard_checkpoint_to_bytes(checkpoint))
    raw["observed_at_utc"] = (OBSERVED_AT + timedelta(seconds=1)).isoformat()
    tampered = (json.dumps(raw, sort_keys=True) + "\n").encode("utf-8")

    with pytest.raises(ValueError, match="guard checkpoint fingerprint mismatch"):
        session_admission_guard_checkpoint_from_bytes(tampered)


def test_unknown_guard_field_fails_closed() -> None:
    _, _, checkpoint = _checkpoint()
    raw = json.loads(session_admission_guard_checkpoint_to_bytes(checkpoint))
    raw["unexpected"] = True
    tampered = (json.dumps(raw, sort_keys=True) + "\n").encode("utf-8")

    with pytest.raises(ValueError, match="guard checkpoint field set mismatch"):
        session_admission_guard_checkpoint_from_bytes(tampered)


def test_guard_execution_safety_drift_fails_closed() -> None:
    _, _, checkpoint = _checkpoint()
    raw = json.loads(session_admission_guard_checkpoint_to_bytes(checkpoint))
    raw["order_execution_enabled"] = True
    tampered = (json.dumps(raw, sort_keys=True) + "\n").encode("utf-8")

    with pytest.raises(ValueError, match="cannot authorize execution"):
        session_admission_guard_checkpoint_from_bytes(tampered)
