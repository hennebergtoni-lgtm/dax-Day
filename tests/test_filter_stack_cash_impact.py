from __future__ import annotations

import pytest

from daxlab.research.filter_stack_cash_impact import (
    COMPLETE_COMPARISON,
    INCOMPLETE_CAPITAL_PATH,
    evaluate_filter_stack_cash_impact,
)


def test_good_filter_stack_increases_simulated_final_balance() -> None:
    result = evaluate_filter_stack_cash_impact(
        [1.0, -1.0, 2.0, -0.5],
        [("LOSS_FILTER", [True, False, True, False])],
        starting_balance_eur=1000.0,
        fixed_risk_eur=20.0,
    )
    assert result.comparison_status == COMPLETE_COMPARISON
    assert result.baseline_ledger.final_balance_eur == pytest.approx(1030.0)
    assert result.filtered_ledger.final_balance_eur == pytest.approx(1060.0)
    assert result.final_balance_delta_eur == pytest.approx(30.0)
    assert result.cash_pnl_delta_eur == pytest.approx(30.0)
    assert result.final_trade_survival_ratio == pytest.approx(0.5)


def test_bad_filter_stack_lowers_simulated_final_balance() -> None:
    result = evaluate_filter_stack_cash_impact(
        [1.0, -1.0, 2.0, -0.5],
        [("WINNER_FILTER", [False, True, False, True])],
        starting_balance_eur=1000.0,
        fixed_risk_eur=20.0,
    )
    assert result.comparison_status == COMPLETE_COMPARISON
    assert result.filtered_ledger.final_balance_eur == pytest.approx(970.0)
    assert result.final_balance_delta_eur == pytest.approx(-60.0)


def test_all_trades_filtered_out_stays_visible() -> None:
    result = evaluate_filter_stack_cash_impact(
        [1.0, -1.0, 0.5],
        [("KILL_ALL", [False, False, False])],
        starting_balance_eur=1000.0,
        fixed_risk_eur=20.0,
    )
    assert result.stack.all_trades_blocked is True
    assert result.filtered_ledger.processed_trades == 0
    assert result.filtered_ledger.final_balance_eur == pytest.approx(1000.0)
    assert result.final_trade_survival_ratio == pytest.approx(0.0)


def test_incomplete_capital_path_is_not_presented_as_complete_comparison() -> None:
    result = evaluate_filter_stack_cash_impact(
        [-1.5, 2.0],
        [("KEEP_ALL", [True, True])],
        starting_balance_eur=100.0,
        fixed_risk_eur=50.0,
    )
    assert result.comparison_status == INCOMPLETE_CAPITAL_PATH
    assert result.baseline_ledger.processed_trades == 1
    assert result.filtered_ledger.processed_trades == 1


def test_payload_is_explicitly_simulated_and_no_order() -> None:
    payload = evaluate_filter_stack_cash_impact(
        [1.0, -1.0],
        [("F", [True, False])],
        starting_balance_eur=1000.0,
        fixed_risk_eur=20.0,
    ).to_payload()
    assert payload["simulated_only"] is True
    assert payload["broker_balance"] is False
    assert payload["automatic_keep_drop_decision"] is None
    assert payload["execution_capability"] == "NONE"
    assert payload["order_execution_enabled"] is False
