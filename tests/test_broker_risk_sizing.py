from __future__ import annotations

import pytest

from daxlab.research.broker_risk_sizing import (
    BROKER_RISK_SIZING_RESEARCH_VERSION,
    BrokerRiskSizingState,
    estimate_volume_for_cash_risk,
)
from daxlab.runtime.mt5_readonly import BrokerSymbol


def _symbol(**overrides) -> BrokerSymbol:
    values = {
        "name": "DE40",
        "digits": 2,
        "point": 0.01,
        "trade_mode": "FULL",
        "contract_size": 1.0,
        "volume_min": 0.1,
        "volume_step": 0.1,
        "volume_max": 100.0,
        "volume_limit": 0.0,
        "tick_size": 0.01,
        "tick_value": 0.01,
        "tick_value_profit": 0.01,
        "tick_value_loss": 0.01,
        "currency_profit": "EUR",
        "currency_margin": "EUR",
        "margin_initial": 0.0,
        "margin_maintenance": 0.0,
    }
    values.update(overrides)
    return BrokerSymbol(**values)


def test_exact_cash_risk_translation_is_research_only() -> None:
    result = estimate_volume_for_cash_risk(
        symbol=_symbol(),
        stop_distance_price=10.0,
        risk_budget_cash=100.0,
        risk_currency="EUR",
    )

    assert result.state is BrokerRiskSizingState.ESTIMATE_AVAILABLE
    assert result.policy_version == BROKER_RISK_SIZING_RESEARCH_VERSION
    assert result.raw_volume == pytest.approx(10.0)
    assert result.volume == pytest.approx(10.0)
    assert result.projected_stop_loss_cash == pytest.approx(100.0)
    assert result.execution_capability == "NONE"
    assert result.order_execution_enabled is False


def test_volume_step_rounding_is_downward_only() -> None:
    result = estimate_volume_for_cash_risk(
        symbol=_symbol(volume_step=0.1),
        stop_distance_price=12.0,
        risk_budget_cash=95.0,
        risk_currency="EUR",
    )

    assert result.available is True
    assert result.raw_volume == pytest.approx(95.0 / 12.0)
    assert result.volume == pytest.approx(7.9)
    assert result.projected_stop_loss_cash == pytest.approx(94.8)
    assert result.projected_stop_loss_cash <= result.risk_budget_cash


def test_budget_below_minimum_volume_fails_closed() -> None:
    result = estimate_volume_for_cash_risk(
        symbol=_symbol(volume_min=0.1, volume_step=0.1),
        stop_distance_price=10.0,
        risk_budget_cash=0.5,
        risk_currency="EUR",
    )

    assert result.state is BrokerRiskSizingState.BELOW_MINIMUM_VOLUME
    assert result.available is False
    assert result.volume is None
    assert result.projected_stop_loss_cash is None
    assert result.blockers == ("RISK_BUDGET_BELOW_MINIMUM_VOLUME",)


def test_volume_max_only_caps_downward() -> None:
    result = estimate_volume_for_cash_risk(
        symbol=_symbol(volume_max=2.0),
        stop_distance_price=10.0,
        risk_budget_cash=100.0,
        risk_currency="EUR",
    )

    assert result.available is True
    assert result.raw_volume == pytest.approx(10.0)
    assert result.volume == pytest.approx(2.0)
    assert result.effective_volume_cap == pytest.approx(2.0)
    assert result.projected_stop_loss_cash == pytest.approx(20.0)


def test_positive_volume_limit_tightens_maximum() -> None:
    result = estimate_volume_for_cash_risk(
        symbol=_symbol(volume_max=10.0, volume_limit=1.5),
        stop_distance_price=10.0,
        risk_budget_cash=100.0,
        risk_currency="EUR",
    )

    assert result.available is True
    assert result.volume == pytest.approx(1.5)
    assert result.effective_volume_cap == pytest.approx(1.5)
    assert result.projected_stop_loss_cash == pytest.approx(15.0)


def test_currency_mismatch_blocks_estimate() -> None:
    result = estimate_volume_for_cash_risk(
        symbol=_symbol(currency_profit="EUR"),
        stop_distance_price=10.0,
        risk_budget_cash=100.0,
        risk_currency="USD",
    )

    assert result.state is BrokerRiskSizingState.ECONOMICS_INCOMPLETE
    assert result.volume is None
    assert result.blockers == ("RISK_CURRENCY_MISMATCH",)


def test_incomplete_broker_economics_blocks_estimate() -> None:
    result = estimate_volume_for_cash_risk(
        symbol=_symbol(tick_value=0.0, tick_value_profit=0.0, tick_value_loss=0.0),
        stop_distance_price=10.0,
        risk_budget_cash=100.0,
        risk_currency="EUR",
    )

    assert result.state is BrokerRiskSizingState.ECONOMICS_INCOMPLETE
    assert result.available is False
    assert "POSITIVE_TICK_VALUE_UNVERIFIED" in result.blockers
    assert result.execution_capability == "NONE"
    assert result.order_execution_enabled is False


def test_invalid_risk_inputs_fail_before_any_estimate() -> None:
    with pytest.raises(ValueError, match="stop_distance_price must be positive"):
        estimate_volume_for_cash_risk(
            symbol=_symbol(),
            stop_distance_price=0.0,
            risk_budget_cash=100.0,
            risk_currency="EUR",
        )
    with pytest.raises(ValueError, match="risk_budget_cash must be positive"):
        estimate_volume_for_cash_risk(
            symbol=_symbol(),
            stop_distance_price=10.0,
            risk_budget_cash=0.0,
            risk_currency="EUR",
        )
