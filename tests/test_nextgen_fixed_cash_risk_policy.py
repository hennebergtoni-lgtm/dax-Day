from __future__ import annotations

import math

import pytest

from daxlab.domain.market import InstrumentId
from daxlab.domain.risk import InstrumentRiskInputs, evaluate_fixed_cash_risk
from daxlab.domain.risk_policy import (
    FixedCashRiskPolicy,
    build_risk_request_from_policy,
)
from daxlab.domain.strategy import TradeDirection, TradePlan


def _instrument(*, currency: str = "EUR") -> InstrumentRiskInputs:
    return InstrumentRiskInputs(
        instrument_id=InstrumentId("DAX40.CFD"),
        quantity_min=1.0,
        quantity_step=1.0,
        quantity_max=10.0,
        cash_loss_per_price_unit_per_quantity=10.0,
        currency=currency,
    )


def _plan() -> TradePlan:
    return TradePlan(
        instrument_id=InstrumentId("DAX40.CFD"),
        direction=TradeDirection.LONG,
        entry_price=100.0,
        stop_price=99.0,
        target_price=102.0,
    )


def test_policy_identity_is_deterministic() -> None:
    first = FixedCashRiskPolicy.build(currency="EUR", max_loss_cash=50.0)
    second = FixedCashRiskPolicy.build(currency="EUR", max_loss_cash=50.0)

    assert first.policy_fingerprint == second.policy_fingerprint
    assert len(first.policy_fingerprint) == 64


def test_policy_rejects_malformed_values_and_tampering() -> None:
    for currency in ("", " EUR", "EUR "):
        with pytest.raises(ValueError):
            FixedCashRiskPolicy.build(currency=currency, max_loss_cash=50.0)

    for value in (0.0, -1.0, math.inf, math.nan):
        with pytest.raises(ValueError):
            FixedCashRiskPolicy.build(currency="EUR", max_loss_cash=value)

    with pytest.raises(ValueError, match="fingerprint mismatch"):
        FixedCashRiskPolicy(
            currency="EUR",
            max_loss_cash=50.0,
            policy_fingerprint="0" * 64,
        )


def test_policy_currency_mismatch_fails_closed_before_risk_request() -> None:
    policy = FixedCashRiskPolicy.build(currency="EUR", max_loss_cash=50.0)

    with pytest.raises(ValueError, match="currency must match"):
        build_risk_request_from_policy(
            policy=policy,
            strategy_decision_id="a" * 64,
            trade_plan=_plan(),
            instrument=_instrument(currency="USD"),
        )


def test_policy_delegates_to_existing_risk_v1_sizing() -> None:
    policy = FixedCashRiskPolicy.build(currency="EUR", max_loss_cash=50.0)
    request = build_risk_request_from_policy(
        policy=policy,
        strategy_decision_id="a" * 64,
        trade_plan=_plan(),
        instrument=_instrument(),
    )
    decision = evaluate_fixed_cash_risk(request)

    assert request.max_loss_cash == 50.0
    assert request.loss_currency == "EUR"
    assert decision.allowed is True
    assert decision.quantity == 5.0
