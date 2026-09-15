"""Synthetic source-binding conformance; no broker facts or product policy grant."""
from dataclasses import replace
from datetime import timedelta
from hashlib import sha256
import json

import pytest

from daxlab.runtime.demo_evidence_authorization import DemoAccountMode
from daxlab.runtime.nextgen_loss_exposure_provenance import (
    LossExposureObservationProvenance,
    assert_loss_exposure_provenance_compatible,
    loss_exposure_provenance_from_bytes,
    loss_exposure_provenance_to_bytes,
)
from daxlab.state.loss_exposure import loss_exposure_checkpoint_to_bytes
from test_nextgen_broker_economics_observation import arguments
from test_nextgen_loss_exposure_checkpoint import _checkpoint


def evidence():
    policy, checkpoint = _checkpoint()
    day_start = checkpoint.observed_at.replace(hour=0, minute=0)
    provenance = LossExposureObservationProvenance(
        checkpoint=checkpoint,
        account_context=arguments()["expected_account_context"],
        source_fingerprint="a" * 64,
        calculation_contract_fingerprint="b" * 64,
        policy_review_record_fingerprint="c" * 64,
        daily_period_start=day_start,
        daily_period_end=day_start + timedelta(days=1),
        weekly_period_start=day_start - timedelta(days=5),
        weekly_period_end=day_start + timedelta(days=2),
    )
    return policy, checkpoint, provenance


def check(provenance, **overrides):
    policy, checkpoint, _ = evidence()
    args = dict(
        checkpoint=checkpoint, policy=policy,
        account_context=provenance.account_context,
        expected_source_fingerprint="a" * 64,
        evaluated_at=checkpoint.observed_at, max_age_seconds=60,
    ) | overrides
    assert_loss_exposure_provenance_compatible(provenance, **args)


def rehash(raw):
    raw.pop("provenance_fingerprint", None)
    raw["provenance_fingerprint"] = sha256(
        json.dumps(raw, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    ).hexdigest()
    return (json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n").encode()


def test_source_binding_roundtrip_preserves_original_checkpoint_bytes():
    _, checkpoint, provenance = evidence()
    original = loss_exposure_checkpoint_to_bytes(checkpoint)
    payload = loss_exposure_provenance_to_bytes(provenance)
    restored = loss_exposure_provenance_from_bytes(payload)
    assert restored == provenance
    assert restored.fingerprint == provenance.fingerprint
    assert loss_exposure_checkpoint_to_bytes(restored.checkpoint) == original
    check(restored)
    assert restored.execution_capability == "NONE"
    assert restored.order_execution_enabled is False


@pytest.mark.parametrize("field", [
    "source_fingerprint", "calculation_contract_fingerprint", "policy_review_record_fingerprint",
])
def test_each_source_review_binding_is_required_and_fingerprinted(field):
    _, _, provenance = evidence()
    with pytest.raises(ValueError):
        replace(provenance, **{field: ""})
    assert replace(provenance, **{field: "f" * 64}).fingerprint != provenance.fingerprint


def test_outer_tampering_rejects():
    _, _, provenance = evidence()
    raw = json.loads(loss_exposure_provenance_to_bytes(provenance))
    raw["source_fingerprint"] = "f" * 64
    with pytest.raises(ValueError, match="fingerprint"):
        loss_exposure_provenance_from_bytes(json.dumps(raw).encode())


@pytest.mark.parametrize("field", ["source", "account", "checkpoint", "policy"])
def test_rehashed_cross_wiring_rejects_at_compatibility_boundary(field):
    policy, checkpoint, provenance = evidence()
    raw = json.loads(loss_exposure_provenance_to_bytes(provenance))
    if field == "source":
        raw["source_fingerprint"] = "f" * 64
    elif field == "account":
        raw["account_context"]["account_fingerprint"] = "f" * 64
    elif field == "checkpoint":
        observation = replace(checkpoint.observation)  # canonical build below
        observation = type(observation).build(
            currency="EUR", daily_drawdown_cash=11, weekly_drawdown_cash=21,
            consecutive_losses=1, open_positions=0,
        )
        from daxlab.state.loss_exposure import build_loss_exposure_observation_checkpoint
        raw["checkpoint"] = build_loss_exposure_observation_checkpoint(
            policy_fingerprint=policy.policy_fingerprint, observation=observation,
            observed_at=checkpoint.observed_at,
        ).to_dict()
    else:
        other_policy = type(policy).build(
            currency="EUR", daily_drawdown_cap_cash=101, weekly_drawdown_cap_cash=251,
            max_consecutive_losses=3, max_open_positions=1,
        )
        from daxlab.state.loss_exposure import build_loss_exposure_observation_checkpoint
        raw["checkpoint"] = build_loss_exposure_observation_checkpoint(
            policy_fingerprint=other_policy.policy_fingerprint,
            observation=checkpoint.observation, observed_at=checkpoint.observed_at,
        ).to_dict()
    restored = loss_exposure_provenance_from_bytes(rehash(raw))
    with pytest.raises((ValueError, RuntimeError)):
        check(restored, account_context=provenance.account_context)


@pytest.mark.parametrize("field", [
    "daily_period_start", "daily_period_end", "weekly_period_start", "weekly_period_end",
])
def test_rehashed_impossible_periods_reject(field):
    _, checkpoint, provenance = evidence()
    raw = json.loads(loss_exposure_provenance_to_bytes(provenance))
    invalid = checkpoint.observed_at + timedelta(days=10)
    if field.endswith("end"):
        invalid = checkpoint.observed_at - timedelta(days=10)
    raw[field] = invalid.isoformat()
    with pytest.raises(ValueError, match="periods"):
        loss_exposure_provenance_from_bytes(rehash(raw))


@pytest.mark.parametrize("mode", [DemoAccountMode.REAL, DemoAccountMode.CONTEST, DemoAccountMode.UNKNOWN])
def test_non_demo_account_rejects(mode):
    _, _, provenance = evidence()
    with pytest.raises(ValueError, match="DEMO"):
        replace(provenance, account_context=replace(provenance.account_context, account_mode=mode))


@pytest.mark.parametrize("age", [-1, 61])
def test_future_or_stale_observation_rejects(age):
    _, checkpoint, provenance = evidence()
    with pytest.raises(ValueError, match="future-dated, stale"):
        check(provenance, evaluated_at=checkpoint.observed_at + timedelta(seconds=age))


def test_explicit_period_end_rejects_even_with_large_age_limit():
    _, _, provenance = evidence()
    with pytest.raises(ValueError, match="outside explicit period"):
        check(provenance, evaluated_at=provenance.daily_period_end, max_age_seconds=100000)


@pytest.mark.parametrize("age_limit", [float("nan"), float("inf"), True, -1])
def test_invalid_age_limits_reject(age_limit):
    _, _, provenance = evidence()
    with pytest.raises(ValueError):
        check(provenance, max_age_seconds=age_limit)


def test_duplicate_json_fields_and_rehashed_execution_flags_reject():
    _, _, provenance = evidence()
    payload = loss_exposure_provenance_to_bytes(provenance)
    with pytest.raises(ValueError, match="duplicate"):
        loss_exposure_provenance_from_bytes(payload.replace(b'{', b'{"source_fingerprint":"a",', 1))
    for field, value in [("execution_capability", "PAPER"), ("order_execution_enabled", True)]:
        raw = json.loads(payload)
        raw[field] = value
        with pytest.raises(ValueError, match="cannot authorize"):
            loss_exposure_provenance_from_bytes(rehash(raw))


def test_canonical_loss_admission_remains_the_owner():
    from daxlab.domain.loss_admission import evaluate_loss_exposure_admission
    policy, checkpoint, provenance = evidence()
    check(provenance)
    restored = loss_exposure_provenance_from_bytes(loss_exposure_provenance_to_bytes(provenance))
    assert evaluate_loss_exposure_admission(policy=policy, observation=checkpoint.observation) == (
        evaluate_loss_exposure_admission(policy=policy, observation=restored.checkpoint.observation)
    )
