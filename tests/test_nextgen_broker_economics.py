from __future__ import annotations

from pathlib import Path

import pytest

from daxlab.domain.market import InstrumentId
from daxlab.domain.risk import RiskDecisionAction, RiskRequest, evaluate_fixed_cash_risk
from daxlab.domain.strategy import TradeDirection, TradePlan
from daxlab.research.broker_risk_sizing import estimate_volume_for_cash_risk
from daxlab.runtime.mt5_readonly import BrokerSymbol
from daxlab.runtime.nextgen_broker_economics import (
    bind_verified_broker_economics_to_risk_inputs,
)


def _symbol(**overrides: object) -> BrokerSymbol:
    values: dict[str, object] = {
        "name": "DE40",
        "digits": 2,
        "point": 0.01,
        "trade_mode": "FULL",
        "contract_size": 1.0,
        "volume_min": 0.1,
        "volume_step": 0.1,
        "volume_max": 100.0,
        "volume_limit": None,
        "tick_size": 0.1,
        "tick_value": 0.1,
        "tick_value_profit": 0.1,
        "tick_value_loss": 0.1,
        "currency_profit": "EUR",
        "currency_margin": "EUR",
        "margin_initial": 100.0,
        "margin_maintenance": 100.0,
    }
    values.update(overrides)
    return BrokerSymbol(**values)  # type: ignore[arg-type]


def test_verified_broker_economics_map_to_canonical_risk_inputs() -> None:
    binding = bind_verified_broker_economics_to_risk_inputs(
        canonical_instrument_id=InstrumentId("DAX40.CFD"),
        symbol=_symbol(),
        broker_economics_verified=True,
    )

    assert binding.canonical_instrument_id == InstrumentId("DAX40.CFD")
    assert binding.broker_symbol == "DE40"
    assert binding.risk_inputs.instrument_id == InstrumentId("DAX40.CFD")
    assert binding.risk_inputs.quantity_min == 0.1
    assert binding.risk_inputs.quantity_step == 0.1
    assert binding.risk_inputs.quantity_max == 100.0
    assert binding.risk_inputs.cash_loss_per_price_unit_per_quantity == 1.0
    assert binding.risk_inputs.currency == "EUR"
    assert len(binding.source_fingerprint) == 64
    assert binding.execution_capability == "NONE"
    assert binding.order_execution_enabled is False


def test_binding_preserves_existing_research_sizing_economics() -> None:
    symbol = _symbol()
    binding = bind_verified_broker_economics_to_risk_inputs(
        canonical_instrument_id=InstrumentId("DAX40.CFD"),
        symbol=symbol,
        broker_economics_verified=True,
    )
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
        max_loss_cash=257.0,
        loss_currency="EUR",
        instrument=binding.risk_inputs,
    )
    product_decision = evaluate_fixed_cash_risk(request)
    research = estimate_volume_for_cash_risk(
        symbol=symbol,
        stop_distance_price=100.0,
        risk_budget_cash=257.0,
        risk_currency="EUR",
    )

    assert product_decision.action is RiskDecisionAction.ALLOW
    assert product_decision.quantity == 2.5
    assert research.available is True
    assert research.volume == product_decision.quantity


def test_external_broker_economics_verification_is_required() -> None:
    with pytest.raises(ValueError, match="externally verified"):
        bind_verified_broker_economics_to_risk_inputs(
            canonical_instrument_id=InstrumentId("DAX40.CFD"),
            symbol=_symbol(),
            broker_economics_verified=False,
        )


def test_disabled_or_partial_trade_mode_fails_closed() -> None:
    for mode in ("DISABLED", "CLOSEONLY", "LONGONLY", "SHORTONLY"):
        with pytest.raises(ValueError, match="trade_mode must be FULL"):
            bind_verified_broker_economics_to_risk_inputs(
                canonical_instrument_id=InstrumentId("DAX40.CFD"),
                symbol=_symbol(trade_mode=mode),
                broker_economics_verified=True,
            )


def test_incomplete_or_non_finite_economics_fail_closed() -> None:
    with pytest.raises(ValueError, match="broker economics incomplete"):
        bind_verified_broker_economics_to_risk_inputs(
            canonical_instrument_id=InstrumentId("DAX40.CFD"),
            symbol=_symbol(tick_size=None),
            broker_economics_verified=True,
        )
    with pytest.raises(ValueError, match="finite and positive"):
        bind_verified_broker_economics_to_risk_inputs(
            canonical_instrument_id=InstrumentId("DAX40.CFD"),
            symbol=_symbol(volume_max=float("inf")),
            broker_economics_verified=True,
        )


def test_positive_volume_limit_caps_canonical_quantity_max() -> None:
    binding = bind_verified_broker_economics_to_risk_inputs(
        canonical_instrument_id=InstrumentId("DAX40.CFD"),
        symbol=_symbol(volume_limit=2.0),
        broker_economics_verified=True,
    )
    assert binding.risk_inputs.quantity_max == 2.0


def test_unaligned_volume_limit_is_rejected_by_canonical_risk_contract() -> None:
    with pytest.raises(ValueError, match="align"):
        bind_verified_broker_economics_to_risk_inputs(
            canonical_instrument_id=InstrumentId("DAX40.CFD"),
            symbol=_symbol(volume_limit=2.05),
            broker_economics_verified=True,
        )


def test_broker_economics_bridge_has_no_submission_dependency() -> None:
    path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "daxlab"
        / "runtime"
        / "nextgen_broker_economics.py"
    )
    source = path.read_text(encoding="utf-8").lower()
    assert "metatrader5" not in source
    assert "order_send" not in source
