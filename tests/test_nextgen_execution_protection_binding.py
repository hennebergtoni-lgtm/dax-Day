from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from daxlab.domain.loss_admission import (
    LossExposureObservation,
    LossExposurePolicy,
    evaluate_loss_exposure_admission,
)
from daxlab.domain.market import InstrumentId
from daxlab.domain.risk import InstrumentRiskInputs, RiskRequest, evaluate_fixed_cash_risk
from daxlab.domain.risk_policy import FixedCashRiskPolicy
from daxlab.domain.strategy import TradeDirection, TradePlan
from daxlab.runtime.broker_execution_protection import (
    ExecutionProtectionStatus,
    evaluate_nextgen_execution_protection,
)
from daxlab.state.loss_exposure import build_loss_exposure_observation_checkpoint


UTC = timezone.utc
CLIENT_ID = "e" * 64
EVALUATED_AT = datetime(2026, 9, 12, 12, 0, tzinfo=UTC)
MAX_OBSERVATION_AGE_SECONDS = 60.0


def _risk_chain(*, policy_cash: float = 257.0, request_cash: float | None = None):
    policy = FixedCashRiskPolicy.build(currency="EUR", max_loss_cash=policy_cash)
    plan = TradePlan(
        instrument_id=InstrumentId("DAX40.CFD"),
        direction=TradeDirection.LONG,
        entry_price=25000.0,
        stop_price=24900.0,
        target_price=25200.0,
    )
    request = RiskRequest.build(
        strategy_decision_id="a" * 64,
        trade_plan=plan,
        max_loss_cash=(policy_cash if request_cash is None else request_cash),
        loss_currency="EUR",
        instrument=InstrumentRiskInputs(
            instrument_id=InstrumentId("DAX40.CFD"),
            quantity_min=0.1,
            quantity_step=0.1,
            quantity_max=10.0,
            cash_loss_per_price_unit_per_quantity=1.0,
            currency="EUR",
        ),
    )
    return policy, request, evaluate_fixed_cash_risk(request)


def _loss_chain(*, open_positions: int = 0, currency: str = "EUR"):
    policy = LossExposurePolicy.build(
        currency=currency,
        daily_drawdown_cap_cash=100.0,
        weekly_drawdown_cap_cash=250.0,
        max_consecutive_losses=3,
        max_open_positions=1,
    )
    observation = LossExposureObservation.build(
        currency=currency,
        daily_drawdown_cash=10.0,
        weekly_drawdown_cash=20.0,
        consecutive_losses=0,
        open_positions=open_positions,
    )
    decision = evaluate_loss_exposure_admission(
        policy=policy,
        observation=observation,
    )
    return policy, observation, decision


def _checkpoint(policy: LossExposurePolicy, observation: LossExposureObservation):
    return build_loss_exposure_observation_checkpoint(
        policy_fingerprint=policy.policy_fingerprint,
        observation=observation,
        observed_at=EVALUATED_AT - timedelta(seconds=1),
    )


def _evaluate(*, risk=None, loss=None):
    risk_policy, request, risk_decision = risk or _risk_chain()
    loss_policy, observation, admission = loss or _loss_chain()
    checkpoint = _checkpoint(loss_policy, observation)
    return evaluate_nextgen_execution_protection(
        client_order_id=CLIENT_ID,
        host_health_green=True,
        broker_account_trade_allowed=True,
        feed_age_seconds=0.2,
        max_feed_age_seconds=5.0,
        observed_spread_points=1.0,
        max_spread_points=2.0,
        reconciliation_inventory_complete=True,
        reconciliations=(),
        duplicate_client_order_id=False,
        risk_policy=risk_policy,
        risk_request=request,
        risk_decision=risk_decision,
        loss_policy=loss_policy,
        loss_observation=observation,
        loss_observation_checkpoint=checkpoint,
        loss_admission_decision=admission,
        evaluated_at=EVALUATED_AT,
        max_loss_observation_age_seconds=MAX_OBSERVATION_AGE_SECONDS,
        session_admission_allowed=True,
    )


def test_canonical_evidence_produces_allow_evidence_and_binds_fingerprints() -> None:
    risk_policy, _, risk_decision = _risk_chain()
    loss_policy, observation, admission = _loss_chain()
    checkpoint = _checkpoint(loss_policy, observation)

    verdict = _evaluate()

    assert verdict.status is ExecutionProtectionStatus.ALLOW_EVIDENCE
    assert verdict.allow_evidence is True
    assert verdict.sizing_evidence_fingerprint == risk_decision.decision_id
    assert verdict.risk_policy_fingerprint == risk_policy.policy_fingerprint
    assert (
        verdict.loss_admission_evidence_fingerprint
        == admission.decision_fingerprint
    )
    assert (
        verdict.loss_observation_checkpoint_fingerprint
        == checkpoint.checkpoint_fingerprint
    )
    assert verdict.loss_observation_age_seconds == 1.0
    assert verdict.execution_capability == "NONE"
    assert verdict.order_execution_enabled is False


def test_risk_request_must_match_fixed_cash_policy() -> None:
    risk = _risk_chain(policy_cash=257.0, request_cash=300.0)

    with pytest.raises(ValueError, match="fixed-cash risk policy"):
        _evaluate(risk=risk)


def test_tampered_risk_decision_fails_closed() -> None:
    policy, request, decision = _risk_chain()
    forged = replace(decision, decision_id="f" * 64)

    with pytest.raises(ValueError, match="canonical risk evaluation"):
        _evaluate(risk=(policy, request, forged))


def test_blocked_loss_admission_becomes_protection_block() -> None:
    loss = _loss_chain(open_positions=1)
    _, _, admission = loss
    assert admission.allowed is False

    verdict = _evaluate(loss=loss)

    assert verdict.status is ExecutionProtectionStatus.BLOCKED
    assert "LOSS_CAP_BLOCKED" in verdict.blockers
    assert (
        verdict.loss_admission_evidence_fingerprint
        == admission.decision_fingerprint
    )


def test_tampered_loss_admission_decision_fails_closed() -> None:
    policy, observation, admission = _loss_chain()
    forged = replace(admission, decision_fingerprint="f" * 64)

    with pytest.raises(ValueError, match="canonical admission evaluation"):
        _evaluate(loss=(policy, observation, forged))


def test_risk_and_loss_policy_currency_mismatch_fails_closed() -> None:
    with pytest.raises(ValueError, match="policy currencies must match"):
        _evaluate(loss=_loss_chain(currency="USD"))
