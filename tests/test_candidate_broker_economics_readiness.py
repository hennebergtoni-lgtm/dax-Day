from __future__ import annotations

from daxlab.runtime.broker_economics_readiness import (
    BrokerEconomicsState,
    assess_broker_economics,
)
from daxlab.runtime.mt5_readonly import BrokerSymbol


def _symbol(**overrides) -> BrokerSymbol:
    values = {
        "name": "DE40",
        "digits": 2,
        "point": 0.01,
        "trade_mode": "FULL",
        "contract_size": 1.0,
        "volume_min": 0.01,
        "volume_step": 0.01,
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


def test_complete_positive_metadata_is_ready_for_sizing_research_only() -> None:
    result = assess_broker_economics(_symbol())

    assert result.state is BrokerEconomicsState.READY_FOR_SIZING_RESEARCH
    assert result.ready is True
    assert result.blockers == ()
    assert result.risk_tick_value == 0.01
    assert result.execution_capability == "NONE"
    assert result.order_execution_enabled is False
    # Zero broker margin metadata is observable but is not promoted into a
    # positive margin assumption.
    assert result.margin_metadata_observed is False


def test_missing_positive_tick_value_fails_closed() -> None:
    result = assess_broker_economics(
        _symbol(tick_value=0.0, tick_value_profit=0.0, tick_value_loss=0.0)
    )

    assert result.state is BrokerEconomicsState.INCOMPLETE
    assert result.ready is False
    assert "POSITIVE_TICK_VALUE_UNVERIFIED" in result.blockers
    assert result.risk_tick_value is None
    assert result.execution_capability == "NONE"
    assert result.order_execution_enabled is False


def test_missing_volume_max_fails_closed() -> None:
    result = assess_broker_economics(_symbol(volume_max=None))

    assert result.state is BrokerEconomicsState.INCOMPLETE
    assert "VOLUME_MAX_MISSING" in result.blockers


def test_invalid_volume_range_and_step_are_visible_blockers() -> None:
    result = assess_broker_economics(
        _symbol(volume_min=2.0, volume_step=3.0, volume_max=1.0)
    )

    assert result.state is BrokerEconomicsState.INCOMPLETE
    assert "VOLUME_RANGE_INVALID" in result.blockers
    assert "VOLUME_STEP_INVALID" in result.blockers


def test_profit_and_margin_currency_are_required_for_research_readiness() -> None:
    result = assess_broker_economics(
        _symbol(currency_profit=None, currency_margin=None)
    )

    assert result.state is BrokerEconomicsState.INCOMPLETE
    assert "CURRENCY_PROFIT_MISSING" in result.blockers
    assert "CURRENCY_MARGIN_MISSING" in result.blockers


def test_worst_positive_tick_value_is_selected_conservatively() -> None:
    result = assess_broker_economics(
        _symbol(tick_value=0.8, tick_value_profit=0.9, tick_value_loss=1.2)
    )

    assert result.ready is True
    assert result.risk_tick_value == 1.2


def test_positive_margin_metadata_is_observed_not_interpreted() -> None:
    result = assess_broker_economics(
        _symbol(margin_initial=50.0, margin_maintenance=25.0)
    )

    assert result.ready is True
    assert result.margin_metadata_observed is True
    assert result.execution_capability == "NONE"
    assert result.order_execution_enabled is False
