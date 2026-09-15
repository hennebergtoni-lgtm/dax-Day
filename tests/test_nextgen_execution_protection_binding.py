from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import inspect

import pytest

from daxlab.domain.loss_admission import (
    LossExposureObservation,
    LossExposurePolicy,
    evaluate_loss_exposure_admission,
)
from daxlab.domain.market import InstrumentId
from daxlab.domain.risk import InstrumentRiskInputs, RiskRequest, evaluate_fixed_cash_risk
from daxlab.domain.risk_policy import FixedCashRiskPolicy
from daxlab.domain.session_admission import (
    SessionAdmissionConsumptionRecord,
    SessionAdmissionConsumptionState,
    SessionAdmissionPolicy,
    evaluate_session_admission,
)
from daxlab.domain.strategy import TradeDirection, TradePlan
from daxlab.runtime.broker_execution_protection import (
    ExecutionProtectionStatus,
    evaluate_nextgen_execution_protection,
)
from daxlab.state.loss_exposure import build_loss_exposure_observation_checkpoint
from daxlab.state.session_admission import build_session_admission_guard_checkpoint


UTC = timezone.utc
CLIENT_ID = "e" * 64
EVALUATED_AT = datetime(2026, 9, 12, 12, 0, tzinfo=UTC)
MAX_OBSERVATION_AGE_SECONDS = 60.0
MAX_SESSION_OBSERVATION_AGE_SECONDS = 60.0
SESSION_KEY = "2026-09-12-DE40-DAY"


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


def _session_chain(*, trades_admitted: int = 0, max_trades: int = 1):
    policy = SessionAdmissionPolicy.build(max_trades_per_session=max_trades)
    records = tuple(
        SessionAdmissionConsumptionRecord.build(
            consumption_id=f"{index + 1:064x}",
            admission_decision_fingerprint="d" * 64,
        )
        for index in range(trades_admitted)
    )
    state = SessionAdmissionConsumptionState.build(
        session_key=SESSION_KEY,
        records=records,
    )
    decision = evaluate_session_admission(
        policy=policy,
        observation=state.observation,
    )
    return policy, state, decision


def _checkpoint(policy: LossExposurePolicy, observation: LossExposureObservation):
    return build_loss_exposure_observation_checkpoint(
        policy_fingerprint=policy.policy_fingerprint,
        observation=observation,
        observed_at=EVALUATED_AT - timedelta(seconds=1),
    )


def _session_guard(
    policy: SessionAdmissionPolicy,
    state: SessionAdmissionConsumptionState,
    *,
    observed_at: datetime | None = None,
):
    return build_session_admission_guard_checkpoint(
        policy_fingerprint=policy.policy_fingerprint,
        state=state,
        observed_at=(
            EVALUATED_AT - timedelta(seconds=1)
            if observed_at is None
            else observed_at
        ),
    )


def _evaluate(
    *,
    risk=None,
    loss=None,
    session=None,
    session_guard=None,
    evaluated_at: datetime = EVALUATED_AT,
    max_session_age_seconds: float = MAX_SESSION_OBSERVATION_AGE_SECONDS,
):
    risk_policy, request, risk_decision = risk or _risk_chain()
    loss_policy, observation, admission = loss or _loss_chain()
    session_policy, session_state, session_decision = session or _session_chain()
    checkpoint = _checkpoint(loss_policy, observation)
    session_guard = session_guard or _session_guard(session_policy, session_state)
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
        evaluated_at=evaluated_at,
        max_loss_observation_age_seconds=MAX_OBSERVATION_AGE_SECONDS,
        session_policy=session_policy,
        session_guard_checkpoint=session_guard,
        session_admission_decision=session_decision,
        max_session_observation_age_seconds=max_session_age_seconds,
    )


def test_typed_signature_accepts_guard_not_independent_session_observation() -> None:
    parameters = inspect.signature(evaluate_nextgen_execution_protection).parameters

    assert "session_guard_checkpoint" in parameters
    assert "session_observation" not in parameters
    assert "session_observation_checkpoint" not in parameters


def test_canonical_evidence_produces_allow_evidence_and_binds_guard() -> None:
    risk_policy, _, risk_decision = _risk_chain()
    loss_policy, observation, admission = _loss_chain()
    checkpoint = _checkpoint(loss_policy, observation)
    session_policy, session_state, session_decision = _session_chain()
    guard = _session_guard(session_policy, session_state)

    verdict = _evaluate()

    assert verdict.status is ExecutionProtectionStatus.ALLOW_EVIDENCE
    assert verdict.allow_evidence is True
    assert verdict.sizing_evidence_fingerprint == risk_decision.decision_id
    assert verdict.risk_policy_fingerprint == risk_policy.policy_fingerprint
    assert verdict.loss_admission_evidence_fingerprint == admission.decision_fingerprint
    assert (
        verdict.loss_observation_checkpoint_fingerprint
        == checkpoint.checkpoint_fingerprint
    )
    assert verdict.loss_observation_age_seconds == 1.0
    assert verdict.session_policy_fingerprint == session_policy.policy_fingerprint
    assert (
        verdict.session_observation_fingerprint
        == session_state.observation.observation_fingerprint
    )
    assert (
        verdict.session_admission_evidence_fingerprint
        == session_decision.decision_fingerprint
    )
    assert verdict.session_observation_checkpoint_fingerprint is None
    assert verdict.session_guard_checkpoint_fingerprint == guard.checkpoint_fingerprint
    assert verdict.session_observation_age_seconds == 1.0
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
    assert verdict.loss_admission_evidence_fingerprint == admission.decision_fingerprint


def test_tampered_loss_admission_decision_fails_closed() -> None:
    policy, observation, admission = _loss_chain()
    forged = replace(admission, decision_fingerprint="f" * 64)

    with pytest.raises(ValueError, match="canonical admission evaluation"):
        _evaluate(loss=(policy, observation, forged))


def test_risk_and_loss_policy_currency_mismatch_fails_closed() -> None:
    with pytest.raises(ValueError, match="policy currencies must match"):
        _evaluate(loss=_loss_chain(currency="USD"))


def test_blocked_session_admission_becomes_protection_block() -> None:
    session = _session_chain(trades_admitted=1, max_trades=1)
    _, _, decision = session
    assert decision.allowed is False

    verdict = _evaluate(session=session)

    assert verdict.status is ExecutionProtectionStatus.BLOCKED
    assert "SESSION_ADMISSION_BLOCKED" in verdict.blockers
    assert verdict.session_admission_evidence_fingerprint == decision.decision_fingerprint


def test_mismatched_session_admission_decision_fails_closed() -> None:
    policy, state, _ = _session_chain(trades_admitted=0, max_trades=2)
    _, other_state, other_decision = _session_chain(trades_admitted=1, max_trades=2)
    assert other_state.observation != state.observation

    with pytest.raises(ValueError, match="canonical session evaluation"):
        _evaluate(session=(policy, state, other_decision))


def test_session_guard_policy_mismatch_fails_closed() -> None:
    policy, state, decision = _session_chain()
    other_policy = SessionAdmissionPolicy.build(max_trades_per_session=2)
    guard = build_session_admission_guard_checkpoint(
        policy_fingerprint=other_policy.policy_fingerprint,
        state=state,
        observed_at=EVALUATED_AT - timedelta(seconds=1),
    )

    with pytest.raises(ValueError, match="session guard checkpoint policy mismatch"):
        _evaluate(session=(policy, state, decision), session_guard=guard)


def test_stale_session_guard_blocks_new_admission() -> None:
    policy, state, decision = _session_chain()
    guard = _session_guard(
        policy,
        state,
        observed_at=EVALUATED_AT - timedelta(seconds=61),
    )

    verdict = _evaluate(
        session=(policy, state, decision),
        session_guard=guard,
    )

    assert verdict.status is ExecutionProtectionStatus.BLOCKED
    assert "SESSION_ADMISSION_OBSERVATION_STALE" in verdict.blockers
    assert verdict.session_observation_age_seconds == 61.0
    assert verdict.session_guard_checkpoint_fingerprint == guard.checkpoint_fingerprint


def test_future_dated_session_guard_fails_closed() -> None:
    policy, state, decision = _session_chain()
    guard = _session_guard(
        policy,
        state,
        observed_at=EVALUATED_AT + timedelta(seconds=1),
    )

    with pytest.raises(ValueError, match="session guard checkpoint cannot be future-dated"):
        _evaluate(session=(policy, state, decision), session_guard=guard)


@pytest.mark.parametrize("value", [-1.0, float("inf"), True])
def test_invalid_max_session_observation_age_fails_closed(value) -> None:
    with pytest.raises(
        ValueError,
        match="max_session_observation_age_seconds must be finite and non-negative",
    ):
        _evaluate(max_session_age_seconds=value)
