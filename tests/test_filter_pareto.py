from __future__ import annotations

import pytest

from daxlab.research.filter_pareto import evaluate_filter_pareto
from daxlab.research.filter_stack_cash_impact import evaluate_filter_stack_cash_impact


def _impact(mask, *, baseline=(1.0, -1.0, 2.0, -0.5), start=1000.0, risk=20.0):
    return evaluate_filter_stack_cash_impact(
        baseline,
        [("F", mask)],
        starting_balance_eur=start,
        fixed_risk_eur=risk,
    )


def test_clearly_worse_candidate_is_dominated() -> None:
    good = _impact([True, False, True, False])
    bad = _impact([False, True, False, True])
    result = evaluate_filter_pareto([("GOOD", good), ("BAD", bad)])
    by_id = {item.candidate_id: item for item in result.candidates}
    assert by_id["GOOD"].non_dominated is True
    assert by_id["BAD"].non_dominated is False
    assert by_id["BAD"].dominated_by == ("GOOD",)
    assert result.frontier_candidate_ids == ("GOOD",)


def test_real_tradeoff_keeps_both_candidates_on_frontier() -> None:
    higher_cash_fewer_trades = _impact([True, False, True, False])
    more_trades_lower_cash = _impact([True, False, True, True])
    result = evaluate_filter_pareto(
        [("LEAN", higher_cash_fewer_trades), ("ACTIVE", more_trades_lower_cash)]
    )
    assert set(result.frontier_candidate_ids) == {"LEAN", "ACTIVE"}


def test_identical_metrics_do_not_falsely_dominate_each_other() -> None:
    first = _impact([True, False, True, True])
    second = _impact([True, False, True, True])
    result = evaluate_filter_pareto([("A", first), ("B", second)])
    assert set(result.frontier_candidate_ids) == {"A", "B"}
    assert all(candidate.dominated_by == () for candidate in result.candidates)


def test_incomplete_capital_path_is_rejected() -> None:
    incomplete = _impact([True, True], baseline=(-1.5, 2.0), start=100.0, risk=50.0)
    complete = _impact([False, True], baseline=(-1.5, 2.0), start=100.0, risk=50.0)
    with pytest.raises(ValueError, match="incomplete capital path"):
        evaluate_filter_pareto([("INCOMPLETE", incomplete), ("COMPLETE", complete)])


def test_different_baseline_or_risk_is_rejected() -> None:
    first = _impact([True, False, True, True])
    different = _impact(
        [True, False, True, True],
        baseline=(1.0, -1.0, 1.5, -0.5),
    )
    with pytest.raises(ValueError, match="baseline ledger identity"):
        evaluate_filter_pareto([("A", first), ("B", different)])


def test_payload_has_no_scalar_score_or_auto_winner() -> None:
    result = evaluate_filter_pareto(
        [
            ("A", _impact([True, False, True, True])),
            ("B", _impact([True, False, True, False])),
        ]
    )
    payload = result.to_payload()
    assert payload["weighted_score_used"] is False
    assert payload["automatic_winner_selected"] is False
    assert payload["simulated_only"] is True
    assert payload["broker_balance"] is False
    assert payload["execution_capability"] == "NONE"
    assert payload["order_execution_enabled"] is False
