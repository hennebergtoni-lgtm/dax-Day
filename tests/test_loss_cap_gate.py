from __future__ import annotations

import pytest

from daxlab.research.loss_cap_gate import (
    LOSS_CAP_GATE_RESEARCH_VERSION,
    LossCapGateState,
    LossCapObservation,
    LossCapPolicy,
    evaluate_loss_caps,
)


def _policy(**overrides) -> LossCapPolicy:
    values = {
        "currency": "EUR",
        "daily_drawdown_cap_cash": 100.0,
        "weekly_drawdown_cap_cash": 250.0,
        "max_consecutive_losses": 3,
        "max_open_positions": 1,
    }
    values.update(overrides)
    return LossCapPolicy(**values)


def _observation(**overrides) -> LossCapObservation:
    values = {
        "currency": "EUR",
        "daily_drawdown_cash": 0.0,
        "weekly_drawdown_cash": 0.0,
        "consecutive_losses": 0,
        "open_positions": 0,
    }
    values.update(overrides)
    return LossCapObservation(**values)


def test_clear_observation_allows_research_admission_only() -> None:
    policy = _policy()
    observation = _observation()
    decision = evaluate_loss_caps(policy=policy, observation=observation)

    assert policy.policy_version == LOSS_CAP_GATE_RESEARCH_VERSION
    assert decision.state is LossCapGateState.ALLOW_RESEARCH_ADMISSION
    assert decision.allowed is True
    assert decision.blockers == ()
    assert decision.execution_capability == "NONE"
    assert decision.order_execution_enabled is False
    assert len(decision.fingerprint) == 64


@pytest.mark.parametrize(
    ("observation", "expected"),
    [
        (_observation(daily_drawdown_cash=100.0), "DAILY_DRAWDOWN_CAP"),
        (_observation(weekly_drawdown_cash=250.0), "WEEKLY_DRAWDOWN_CAP"),
        (_observation(consecutive_losses=3), "CONSECUTIVE_LOSS_COOLDOWN"),
        (_observation(open_positions=1), "MAX_OPEN_POSITIONS"),
    ],
)
def test_each_boundary_blocks_new_research_admission(
    observation: LossCapObservation,
    expected: str,
) -> None:
    decision = evaluate_loss_caps(policy=_policy(), observation=observation)

    assert decision.state is LossCapGateState.BLOCKED
    assert decision.allowed is False
    assert expected in decision.blockers
    assert decision.order_execution_enabled is False


def test_multiple_breaches_are_all_visible() -> None:
    decision = evaluate_loss_caps(
        policy=_policy(),
        observation=_observation(
            daily_drawdown_cash=150.0,
            weekly_drawdown_cash=300.0,
            consecutive_losses=4,
            open_positions=2,
        ),
    )

    assert decision.blockers == (
        "DAILY_DRAWDOWN_CAP",
        "WEEKLY_DRAWDOWN_CAP",
        "CONSECUTIVE_LOSS_COOLDOWN",
        "MAX_OPEN_POSITIONS",
    )


def test_currency_mismatch_fails_closed() -> None:
    decision = evaluate_loss_caps(
        policy=_policy(currency="EUR"),
        observation=_observation(currency="USD"),
    )

    assert decision.state is LossCapGateState.BLOCKED
    assert decision.blockers == ("RISK_CURRENCY_MISMATCH",)


def test_values_just_below_caps_do_not_block() -> None:
    decision = evaluate_loss_caps(
        policy=_policy(),
        observation=_observation(
            daily_drawdown_cash=99.99,
            weekly_drawdown_cash=249.99,
            consecutive_losses=2,
            open_positions=0,
        ),
    )

    assert decision.allowed is True


def test_policy_and_observation_inputs_are_strict() -> None:
    with pytest.raises(ValueError, match="daily_drawdown_cap_cash must be positive"):
        _policy(daily_drawdown_cap_cash=0.0)
    with pytest.raises(ValueError, match="max_consecutive_losses must be an integer >= 1"):
        _policy(max_consecutive_losses=0)
    with pytest.raises(ValueError, match="daily_drawdown_cash must be non-negative"):
        _observation(daily_drawdown_cash=-1.0)
    with pytest.raises(ValueError, match="open_positions must be a non-negative integer"):
        _observation(open_positions=-1)


def test_fingerprints_are_deterministic_and_sensitive_to_state() -> None:
    policy = _policy()
    same_policy = _policy()
    changed_policy = _policy(daily_drawdown_cap_cash=120.0)
    observation = _observation(daily_drawdown_cash=10.0)
    same_observation = _observation(daily_drawdown_cash=10.0)
    changed_observation = _observation(daily_drawdown_cash=11.0)

    first = evaluate_loss_caps(policy=policy, observation=observation)
    repeated = evaluate_loss_caps(policy=same_policy, observation=same_observation)
    changed = evaluate_loss_caps(policy=policy, observation=changed_observation)

    assert policy.fingerprint == same_policy.fingerprint
    assert policy.fingerprint != changed_policy.fingerprint
    assert observation.fingerprint == same_observation.fingerprint
    assert observation.fingerprint != changed_observation.fingerprint
    assert first.fingerprint == repeated.fingerprint
    assert first.fingerprint != changed.fingerprint
