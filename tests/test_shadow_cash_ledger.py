from __future__ import annotations

import pytest

from daxlab.research.shadow_cash_ledger import (
    CAPITAL_EXHAUSTED_AFTER_TRADE,
    CAPITAL_INSUFFICIENT,
    COMPLETE,
    simulate_fixed_risk_cash_ledger,
)


def test_fixed_risk_translates_r_into_eur_equity() -> None:
    result = simulate_fixed_risk_cash_ledger(
        [1.0, -1.0, 2.0],
        starting_balance_eur=1000.0,
        fixed_risk_eur=20.0,
    )
    assert result.status == COMPLETE
    assert result.trade_pnl_eur == pytest.approx((20.0, -20.0, 40.0))
    assert result.equity_curve_eur == pytest.approx((1000.0, 1020.0, 1000.0, 1040.0))
    assert result.final_balance_eur == pytest.approx(1040.0)
    assert result.cash_pnl_eur == pytest.approx(40.0)
    assert result.return_pct == pytest.approx(0.04)
    assert result.max_drawdown_eur == pytest.approx(20.0)


def test_insufficient_capital_stops_before_next_trade() -> None:
    result = simulate_fixed_risk_cash_ledger(
        [-1.5, 2.0],
        starting_balance_eur=100.0,
        fixed_risk_eur=50.0,
    )
    assert result.status == CAPITAL_INSUFFICIENT
    assert result.halted_trade_index == 1
    assert result.processed_trades == 1
    assert result.unprocessed_trades == 1
    assert result.final_balance_eur == pytest.approx(25.0)
    assert result.trade_r == pytest.approx((-1.5,))


def test_zero_balance_is_explicit_capital_exhaustion() -> None:
    result = simulate_fixed_risk_cash_ledger(
        [-1.0, 3.0],
        starting_balance_eur=100.0,
        fixed_risk_eur=100.0,
    )
    assert result.status == CAPITAL_EXHAUSTED_AFTER_TRADE
    assert result.halted_trade_index == 0
    assert result.processed_trades == 1
    assert result.unprocessed_trades == 1
    assert result.final_balance_eur == pytest.approx(0.0)
    assert result.max_drawdown_pct_of_peak == pytest.approx(1.0)


def test_empty_trade_sequence_is_valid_flat_shadow_ledger() -> None:
    result = simulate_fixed_risk_cash_ledger(
        [], starting_balance_eur=1000.0, fixed_risk_eur=20.0
    )
    assert result.status == COMPLETE
    assert result.processed_trades == 0
    assert result.final_balance_eur == pytest.approx(1000.0)
    assert result.cash_pnl_eur == pytest.approx(0.0)


def test_payload_cannot_be_confused_with_real_broker_balance() -> None:
    payload = simulate_fixed_risk_cash_ledger(
        [0.5], starting_balance_eur=1000.0, fixed_risk_eur=20.0
    ).to_payload()
    assert payload["simulated_only"] is True
    assert payload["broker_balance"] is False
    assert payload["execution_capability"] == "NONE"
    assert payload["order_execution_enabled"] is False


def test_inputs_fail_closed() -> None:
    with pytest.raises(ValueError, match="starting_balance"):
        simulate_fixed_risk_cash_ledger([1.0], starting_balance_eur=0.0, fixed_risk_eur=20.0)
    with pytest.raises(ValueError, match="fixed_risk_eur"):
        simulate_fixed_risk_cash_ledger([1.0], starting_balance_eur=1000.0, fixed_risk_eur=0.0)
    with pytest.raises(ValueError, match="cannot exceed"):
        simulate_fixed_risk_cash_ledger([1.0], starting_balance_eur=100.0, fixed_risk_eur=101.0)
    with pytest.raises(ValueError, match="finite"):
        simulate_fixed_risk_cash_ledger(
            [float("nan")], starting_balance_eur=1000.0, fixed_risk_eur=20.0
        )
