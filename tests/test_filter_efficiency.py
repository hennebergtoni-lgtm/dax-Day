from __future__ import annotations

import math

import pytest

from daxlab.research.filter_efficiency import evaluate_filter_efficiency


def test_filter_removing_only_losers_adds_net_r() -> None:
    result = evaluate_filter_efficiency(
        [1.0, -1.0, 2.0, -0.5],
        [True, False, True, False],
        filter_id="LOSS_CUT",
    )
    assert result.baseline_trades == 4
    assert result.kept_trades == 2
    assert result.trade_survival_ratio == pytest.approx(0.5)
    assert result.baseline_total_r == pytest.approx(1.5)
    assert result.filtered_total_r == pytest.approx(3.0)
    assert result.delta_total_r == pytest.approx(1.5)
    assert result.avoided_loss_r == pytest.approx(1.5)
    assert result.missed_profit_r == pytest.approx(0.0)
    assert result.net_filter_value_r == pytest.approx(1.5)
    assert result.removed_losers == 2
    assert result.removed_winners == 0
    assert result.filtered_profit_factor is not None
    assert math.isinf(result.filtered_profit_factor)


def test_filter_removing_only_winners_destroys_value() -> None:
    result = evaluate_filter_efficiency(
        [1.0, -1.0, 2.0, -0.5],
        [False, True, False, True],
        filter_id="BAD_FILTER",
    )
    assert result.filtered_total_r == pytest.approx(-1.5)
    assert result.delta_total_r == pytest.approx(-3.0)
    assert result.missed_profit_r == pytest.approx(3.0)
    assert result.avoided_loss_r == pytest.approx(0.0)
    assert result.net_filter_value_r == pytest.approx(-3.0)
    assert result.removed_winners == 2
    assert result.removed_losers == 0


def test_all_trades_blocked_is_visible_not_crash() -> None:
    result = evaluate_filter_efficiency(
        [1.0, -0.5, 0.25],
        [False, False, False],
        filter_id="OVERFILTERED",
    )
    assert result.kept_trades == 0
    assert result.trade_survival_ratio == pytest.approx(0.0)
    assert result.filtered_total_r == pytest.approx(0.0)
    assert result.filtered_expectancy_r is None
    assert result.filtered_profit_factor is None
    assert result.filtered_max_drawdown_r == pytest.approx(0.0)
    payload = result.to_payload()
    assert payload["automatic_keep_drop_decision"] is None
    assert payload["execution_capability"] == "NONE"
    assert payload["order_execution_enabled"] is False


def test_identity_filter_is_exactly_neutral() -> None:
    result = evaluate_filter_efficiency(
        [1.0, -0.5, 0.25],
        [True, True, True],
        filter_id="IDENTITY",
    )
    assert result.removed_trades == 0
    assert result.trade_survival_ratio == pytest.approx(1.0)
    assert result.delta_total_r == pytest.approx(0.0)
    assert result.net_filter_value_r == pytest.approx(0.0)
    assert result.drawdown_change_r == pytest.approx(0.0)


def test_mask_change_changes_diagnostic_identity() -> None:
    baseline = [1.0, -0.5, 0.25, -0.25]
    first = evaluate_filter_efficiency(
        baseline, [True, False, True, True], filter_id="F1"
    )
    second = evaluate_filter_efficiency(
        baseline, [True, True, False, True], filter_id="F1"
    )
    assert first.diagnostic_sha256 != second.diagnostic_sha256


def test_invalid_inputs_fail_closed() -> None:
    with pytest.raises(ValueError, match="filter_id"):
        evaluate_filter_efficiency([1.0], [True], filter_id=" ")
    with pytest.raises(ValueError, match="length"):
        evaluate_filter_efficiency([1.0, -1.0], [True], filter_id="F")
    with pytest.raises(ValueError, match="finite"):
        evaluate_filter_efficiency([1.0, float("nan")], [True, True], filter_id="F")
