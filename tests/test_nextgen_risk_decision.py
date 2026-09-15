from __future__ import annotations

import math

import pytest

from daxlab.domain.market import InstrumentId
from daxlab.domain.risk import (
    InstrumentRiskInputs,
    RiskDecisionAction,
    RiskRequest,
    evaluate_fixed_cash_risk,
)
from daxlab.domain.strategy import TradeDirection, TradePlan


def _plan() -> TradePlan:
    return TradePlan(
        instrument_id=InstrumentId("DAX40.CFD"),
        direction=TradeDirection.LONG,
        entry_price=25000.0,
        stop_price=24900.0,
        target_price=25200.0,
    )


def _instrument(**overrides: object) -> InstrumentRiskInputs:
    values: dict[str, object] = {
        "instrument_id": InstrumentId("DAX40.CFD"),
        "quantity_min": 0.1,
        "quantity_step": 0.1,
        "quantity_max": 10.0,
        "cash_loss_per_price_unit_per_quantity": 1.0,
        "currency": "EUR",
    }
    values.update(overrides)
    return InstrumentRiskInputs(**values)  # type: ignore[arg-type]


def _request(**overrides: object) -> RiskRequest:
    values: dict[str, object] = {
        "strategy_decision_id": "a" * 64,
        "trade_plan": _plan(),
        "max_loss_cash": 257.0,
        "loss_currency": "EUR",
        "instrument": _instrument(),
    }
    values.update(overrides)
    return RiskRequest.build(**values)  # type: ignore[arg-type]


def test_risk_request_and_allow_decision_are_deterministic() -> None:
    first_request = _request()
    second_request = _request()
    assert first_request.request_id == second_request.request_id
    assert len(first_request.request_id) == 64

    first = evaluate_fixed_cash_risk(first_request)
    second = evaluate_fixed_cash_risk(second_request)

    assert first == second
    assert first.action is RiskDecisionAction.ALLOW
    assert first.allowed is True
    assert first.quantity == 2.5
    assert first.reason_codes == ("FIXED_CASH_RISK_WITHIN_LIMIT",)
    assert len(first.decision_id) == 64


def test_quantity_is_emitted_only_after_allow_and_is_step_floored() -> None:
    decision = evaluate_fixed_cash_risk(_request(max_loss_cash=257.0))
    assert decision.quantity == 2.5
    assert math.isclose(decision.quantity % 0.1, 0.0, abs_tol=1e-9) or math.isclose(
        decision.quantity % 0.1, 0.1, abs_tol=1e-9
    )

    denied = evaluate_fixed_cash_risk(_request(max_loss_cash=5.0))
    assert denied.action is RiskDecisionAction.DENY
    assert denied.allowed is False
    assert denied.quantity is None
    assert denied.reason_codes == ("RISK_BUDGET_BELOW_MIN_QUANTITY",)


def test_currency_mismatch_denies_fail_closed() -> None:
    decision = evaluate_fixed_cash_risk(_request(loss_currency="USD"))
    assert decision.action is RiskDecisionAction.DENY
    assert decision.quantity is None
    assert decision.reason_codes == ("CURRENCY_MISMATCH",)


def test_quantity_is_capped_at_canonical_instrument_maximum() -> None:
    decision = evaluate_fixed_cash_risk(_request(max_loss_cash=2000.0))
    assert decision.action is RiskDecisionAction.ALLOW
    assert decision.quantity == 10.0
    assert decision.reason_codes == (
        "FIXED_CASH_RISK_WITHIN_LIMIT",
        "CAPPED_AT_MAX_QUANTITY",
    )


def test_risk_inputs_reject_invalid_or_non_aligned_values() -> None:
    with pytest.raises(ValueError, match="quantity_step"):
        _instrument(quantity_step=0.0)
    with pytest.raises(ValueError, match="finite and positive"):
        _instrument(quantity_max=float("nan"))
    with pytest.raises(ValueError, match="align"):
        _instrument(quantity_min=0.15)
    with pytest.raises(ValueError, match="quantity_min"):
        _instrument(quantity_min=11.0)


def test_request_rejects_instrument_mismatch_and_invalid_budget() -> None:
    with pytest.raises(ValueError, match="instrument"):
        _request(instrument=_instrument(instrument_id=InstrumentId("OTHER.CFD")))
    with pytest.raises(ValueError, match="max_loss_cash"):
        _request(max_loss_cash=0.0)


def test_risk_decision_does_not_authorize_execution_or_broker_access() -> None:
    decision = evaluate_fixed_cash_risk(_request())
    assert not hasattr(decision, "broker")
    assert not hasattr(decision, "order_execution_enabled")
    assert not hasattr(decision, "paper_authorized")
    assert not hasattr(decision, "live_authorized")
