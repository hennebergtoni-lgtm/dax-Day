from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

import pytest

from daxlab.adapters.file_state_store import AtomicFileStateStore
from daxlab.domain.loss_admission import LossExposureObservation, LossExposurePolicy
from daxlab.state.loss_exposure import (
    LossExposureCheckpointCompatibilityError,
    assert_loss_exposure_checkpoint_compatible,
    build_loss_exposure_observation_checkpoint,
    load_loss_exposure_checkpoint,
    loss_exposure_checkpoint_from_bytes,
    loss_exposure_checkpoint_to_bytes,
    save_loss_exposure_checkpoint,
)


def _policy() -> LossExposurePolicy:
    return LossExposurePolicy.build(
        currency="EUR",
        daily_drawdown_cap_cash=100.0,
        weekly_drawdown_cap_cash=250.0,
        max_consecutive_losses=3,
        max_open_positions=1,
    )


def _observation() -> LossExposureObservation:
    return LossExposureObservation.build(
        currency="EUR",
        daily_drawdown_cash=10.0,
        weekly_drawdown_cash=20.0,
        consecutive_losses=1,
        open_positions=0,
    )


def _checkpoint():
    policy = _policy()
    checkpoint = build_loss_exposure_observation_checkpoint(
        policy_fingerprint=policy.policy_fingerprint,
        observation=_observation(),
        observed_at=datetime(
            2026,
            9,
            12,
            21,
            30,
            tzinfo=timezone(timedelta(hours=2)),
        ),
    )
    return policy, checkpoint


def test_checkpoint_roundtrip_is_deterministic_and_normalizes_time_to_utc() -> None:
    _, checkpoint = _checkpoint()
    payload = loss_exposure_checkpoint_to_bytes(checkpoint)
    restored = loss_exposure_checkpoint_from_bytes(payload)

    assert restored == checkpoint
    assert restored.observed_at.utcoffset() == timedelta(0)
    assert loss_exposure_checkpoint_to_bytes(restored) == payload
    assert restored.execution_capability == "NONE"
    assert restored.order_execution_enabled is False


def test_checkpoint_uses_existing_atomic_state_store(tmp_path: Path) -> None:
    _, checkpoint = _checkpoint()
    store = AtomicFileStateStore(tmp_path / "state")

    assert load_loss_exposure_checkpoint(store, "loss-exposure") is None
    save_loss_exposure_checkpoint(store, "loss-exposure", checkpoint)

    assert load_loss_exposure_checkpoint(store, "loss-exposure") == checkpoint


def test_policy_compatibility_is_explicit_and_fail_closed() -> None:
    policy, checkpoint = _checkpoint()
    assert_loss_exposure_checkpoint_compatible(
        checkpoint,
        policy_fingerprint=policy.policy_fingerprint,
    )

    with pytest.raises(
        LossExposureCheckpointCompatibilityError,
        match="policy fingerprint mismatch",
    ):
        assert_loss_exposure_checkpoint_compatible(
            checkpoint,
            policy_fingerprint="f" * 64,
        )


def test_nested_observation_tampering_is_rejected() -> None:
    _, checkpoint = _checkpoint()
    decoded = json.loads(loss_exposure_checkpoint_to_bytes(checkpoint))
    decoded["observation"]["daily_drawdown_cash"] = 99.0
    tampered = (json.dumps(decoded) + "\n").encode("utf-8")

    with pytest.raises(ValueError, match="observation fingerprint mismatch"):
        loss_exposure_checkpoint_from_bytes(tampered)


def test_checkpoint_envelope_tampering_is_rejected() -> None:
    _, checkpoint = _checkpoint()
    decoded = json.loads(loss_exposure_checkpoint_to_bytes(checkpoint))
    decoded["observed_at_utc"] = "2026-09-12T20:00:00+00:00"
    tampered = (json.dumps(decoded) + "\n").encode("utf-8")

    with pytest.raises(ValueError, match="checkpoint fingerprint mismatch"):
        loss_exposure_checkpoint_from_bytes(tampered)


def test_persistence_owner_contains_no_observation_production_or_broker_api() -> None:
    root = Path(__file__).resolve().parents[1]
    source = (root / "src/daxlab/state/loss_exposure.py").read_text(encoding="utf-8")
    lowered = source.lower()

    assert "metatrader5" not in lowered
    assert "order_send" not in lowered
    assert "account_info" not in lowered
    assert "realized_pnl" not in lowered
    assert "daily reset" not in lowered
    assert "weekly reset" not in lowered
