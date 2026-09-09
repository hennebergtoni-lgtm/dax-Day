import math

import pytest

from daxlab.research.v12_isolated_evaluation import (
    IsolatedTradeOutcome,
    evaluate_isolated_outcomes,
)


def test_isolated_metrics_are_deterministic() -> None:
    outcomes = (
        IsolatedTradeOutcome(2.0, "2018"),
        IsolatedTradeOutcome(-1.0, "2018"),
        IsolatedTradeOutcome(-1.0, "2019"),
        IsolatedTradeOutcome(2.0, "2019"),
    )
    first = evaluate_isolated_outcomes(outcomes)
    second = evaluate_isolated_outcomes(outcomes)
    assert first == second
    assert first.trades == 4
    assert first.return_r == 2.0
    assert first.pf == 2.0
    assert first.avg_r == 0.5
    assert first.max_dd_r == -2.0
    assert first.positive_periods == 2
    assert first.negative_periods == 0
    assert first.flat_periods == 0


def test_empty_evidence_is_explicit_zero_state() -> None:
    metrics = evaluate_isolated_outcomes(())
    assert metrics.trades == 0
    assert metrics.return_r == 0.0
    assert metrics.pf == 0.0
    assert metrics.max_dd_r == 0.0
    assert metrics.period_returns == ()


def test_no_losses_uses_bounded_pf_sentinel() -> None:
    metrics = evaluate_isolated_outcomes(
        (IsolatedTradeOutcome(1.0, "2019"), IsolatedTradeOutcome(2.0, "2019"))
    )
    assert metrics.pf == 99.0
    assert metrics.return_r == 3.0


def test_period_stability_counts_positive_negative_and_flat() -> None:
    metrics = evaluate_isolated_outcomes(
        (
            IsolatedTradeOutcome(1.0, "2017"),
            IsolatedTradeOutcome(-1.0, "2018"),
            IsolatedTradeOutcome(1.0, "2019"),
            IsolatedTradeOutcome(-1.0, "2019"),
        )
    )
    assert metrics.period_returns == (("2017", 1.0), ("2018", -1.0), ("2019", 0.0))
    assert metrics.positive_periods == 1
    assert metrics.negative_periods == 1
    assert metrics.flat_periods == 1


def test_invalid_outcome_fails_closed() -> None:
    with pytest.raises(ValueError, match="finite"):
        IsolatedTradeOutcome(math.nan, "2019")
    with pytest.raises(ValueError, match="period"):
        IsolatedTradeOutcome(1.0, "")
