from __future__ import annotations

from pathlib import Path

import pytest

from daxlab.domain.loss_admission import (
    LossExposureAdmissionAction,
    LossExposureObservation,
    LossExposurePolicy,
    evaluate_loss_exposure_admission,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def _policy() -> LossExposurePolicy:
    return LossExposurePolicy.build(
        currency="EUR",
        daily_drawdown_cap_cash=100.0,
        weekly_drawdown_cap_cash=250.0,
        max_consecutive_losses=3,
        max_open_positions=1,
    )


def _observation(
    *,
    currency: str = "EUR",
    daily: float = 10.0,
    weekly: float = 20.0,
    consecutive: int = 0,
    open_positions: int = 0,
) -> LossExposureObservation:
    return LossExposureObservation.build(
        currency=currency,
        daily_drawdown_cash=daily,
        weekly_drawdown_cash=weekly,
        consecutive_losses=consecutive,
        open_positions=open_positions,
    )


def test_below_all_limits_is_deterministic_allow() -> None:
    policy = _policy()
    observation = _observation()

    first = evaluate_loss_exposure_admission(policy=policy, observation=observation)
    second = evaluate_loss_exposure_admission(policy=policy, observation=observation)

    assert first.action is LossExposureAdmissionAction.ALLOW
    assert first.allowed is True
    assert first.reason_codes == ("WITHIN_LOSS_EXPOSURE_LIMITS",)
    assert first.decision_fingerprint == second.decision_fingerprint


@pytest.mark.parametrize(
    ("observation", "reason"),
    [
        (_observation(daily=100.0), "DAILY_DRAWDOWN_CAP"),
        (_observation(weekly=250.0), "WEEKLY_DRAWDOWN_CAP"),
        (_observation(consecutive=3), "CONSECUTIVE_LOSS_LIMIT"),
        (_observation(open_positions=1), "MAX_OPEN_POSITIONS"),
    ],
)
def test_equality_at_each_limit_blocks(observation: LossExposureObservation, reason: str) -> None:
    decision = evaluate_loss_exposure_admission(policy=_policy(), observation=observation)

    assert decision.action is LossExposureAdmissionAction.BLOCK
    assert decision.allowed is False
    assert reason in decision.reason_codes


def test_currency_mismatch_blocks() -> None:
    decision = evaluate_loss_exposure_admission(
        policy=_policy(),
        observation=_observation(currency="USD"),
    )

    assert decision.allowed is False
    assert "RISK_CURRENCY_MISMATCH" in decision.reason_codes


def test_policy_and_observation_validate_and_detect_tampering() -> None:
    with pytest.raises(ValueError):
        LossExposurePolicy.build(
            currency="EUR",
            daily_drawdown_cap_cash=0.0,
            weekly_drawdown_cap_cash=250.0,
            max_consecutive_losses=3,
            max_open_positions=1,
        )

    with pytest.raises(ValueError):
        LossExposureObservation.build(
            currency="EUR",
            daily_drawdown_cash=-1.0,
            weekly_drawdown_cash=0.0,
            consecutive_losses=0,
            open_positions=0,
        )

    with pytest.raises(ValueError, match="fingerprint mismatch"):
        LossExposurePolicy(
            currency="EUR",
            daily_drawdown_cap_cash=100.0,
            weekly_drawdown_cap_cash=250.0,
            max_consecutive_losses=3,
            max_open_positions=1,
            policy_fingerprint="0" * 64,
        )


def test_canonical_owner_remains_separate_from_research_risk_and_broker_execution() -> None:
    source = (REPO_ROOT / "src/daxlab/domain/loss_admission.py").read_text(encoding="utf-8")
    lowered = source.lower()

    assert "daxlab.research" not in source
    assert "riskrequest" not in source
    assert "metatrader5" not in lowered
    assert "order_send" not in lowered
