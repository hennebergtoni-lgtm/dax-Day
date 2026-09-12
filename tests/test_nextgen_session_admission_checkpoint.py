from __future__ import annotations

from datetime import datetime, timezone
import json

import pytest

from daxlab.adapters.file_state_store import AtomicFileStateStore
from daxlab.domain.session_admission import (
    SessionAdmissionObservation,
    SessionAdmissionPolicy,
)
from daxlab.state.session_admission import (
    SessionAdmissionCheckpointCompatibilityError,
    assert_session_admission_checkpoint_compatible,
    build_session_admission_observation_checkpoint,
    load_session_admission_checkpoint,
    save_session_admission_checkpoint,
    session_admission_checkpoint_from_bytes,
    session_admission_checkpoint_to_bytes,
)


UTC = timezone.utc
OBSERVED_AT = datetime(2026, 9, 12, 12, 0, tzinfo=UTC)


def _policy() -> SessionAdmissionPolicy:
    return SessionAdmissionPolicy.build(max_trades_per_session=2)


def _observation() -> SessionAdmissionObservation:
    return SessionAdmissionObservation.build(
        session_key="2026-09-12-DE40-DAY",
        trades_admitted=1,
    )


def _checkpoint():
    policy = _policy()
    observation = _observation()
    checkpoint = build_session_admission_observation_checkpoint(
        policy_fingerprint=policy.policy_fingerprint,
        observation=observation,
        observed_at=OBSERVED_AT,
    )
    return policy, observation, checkpoint


def test_checkpoint_bytes_roundtrip_is_deterministic() -> None:
    policy, observation, checkpoint = _checkpoint()

    first = session_admission_checkpoint_to_bytes(checkpoint)
    restored = session_admission_checkpoint_from_bytes(first)
    second = session_admission_checkpoint_to_bytes(restored)

    assert restored == checkpoint
    assert restored.observation == observation
    assert restored.policy_fingerprint == policy.policy_fingerprint
    assert restored.observed_at == OBSERVED_AT
    assert first == second
    assert restored.execution_capability == "NONE"
    assert restored.order_execution_enabled is False


def test_checkpoint_save_load_reuses_atomic_file_state_store(tmp_path) -> None:
    _, _, checkpoint = _checkpoint()
    store = AtomicFileStateStore(tmp_path)

    assert load_session_admission_checkpoint(store, "session-admission") is None
    save_session_admission_checkpoint(store, "session-admission", checkpoint)

    assert load_session_admission_checkpoint(store, "session-admission") == checkpoint


def test_policy_compatibility_is_explicit_and_fail_closed() -> None:
    policy, _, checkpoint = _checkpoint()
    assert_session_admission_checkpoint_compatible(
        checkpoint,
        policy_fingerprint=policy.policy_fingerprint,
    )

    other = SessionAdmissionPolicy.build(max_trades_per_session=3)
    with pytest.raises(
        SessionAdmissionCheckpointCompatibilityError,
        match="policy fingerprint mismatch",
    ):
        assert_session_admission_checkpoint_compatible(
            checkpoint,
            policy_fingerprint=other.policy_fingerprint,
        )


def test_tampered_checkpoint_payload_fails_closed() -> None:
    _, _, checkpoint = _checkpoint()
    raw = json.loads(session_admission_checkpoint_to_bytes(checkpoint))
    raw["observation"]["trades_admitted"] = 0
    tampered = (json.dumps(raw, sort_keys=True) + "\n").encode("utf-8")

    with pytest.raises(ValueError):
        session_admission_checkpoint_from_bytes(tampered)


def test_unknown_checkpoint_field_fails_closed() -> None:
    _, _, checkpoint = _checkpoint()
    raw = json.loads(session_admission_checkpoint_to_bytes(checkpoint))
    raw["unexpected"] = True
    tampered = (json.dumps(raw, sort_keys=True) + "\n").encode("utf-8")

    with pytest.raises(ValueError, match="field set mismatch"):
        session_admission_checkpoint_from_bytes(tampered)


def test_builder_requires_timezone_aware_observed_at() -> None:
    policy = _policy()
    observation = _observation()

    with pytest.raises(ValueError, match="timezone-aware"):
        build_session_admission_observation_checkpoint(
            policy_fingerprint=policy.policy_fingerprint,
            observation=observation,
            observed_at=datetime(2026, 9, 12, 12, 0),
        )


def test_execution_safety_drift_fails_closed() -> None:
    _, _, checkpoint = _checkpoint()
    raw = json.loads(session_admission_checkpoint_to_bytes(checkpoint))
    raw["order_execution_enabled"] = True
    tampered = (json.dumps(raw, sort_keys=True) + "\n").encode("utf-8")

    with pytest.raises(ValueError):
        session_admission_checkpoint_from_bytes(tampered)
