import pytest

from daxlab.research.no_trade_analysis import (
    NoTradeEvidence,
    NoTradeOutcome,
    classify_no_trade,
    summarize_no_trades,
)


def test_no_trade_classification_is_counterfactual_only() -> None:
    assert classify_no_trade(NoTradeEvidence("a", "REGIME", -1.0)) is NoTradeOutcome.PROTECTED_LOSS
    assert classify_no_trade(NoTradeEvidence("b", "STRUCTURE", 1.5)) is NoTradeOutcome.MISSED_WINNER
    assert classify_no_trade(NoTradeEvidence("c", "DATA", 0.0)) is NoTradeOutcome.NEUTRAL
    assert classify_no_trade(NoTradeEvidence("d", "DATA", None)) is NoTradeOutcome.UNOBSERVABLE


def test_no_trade_summary_balances_protection_and_missed_opportunity() -> None:
    summary = summarize_no_trades(
        [
            NoTradeEvidence("a", "REGIME", -1.0),
            NoTradeEvidence("b", "REGIME", -0.5),
            NoTradeEvidence("c", "STRUCTURE", 1.25),
            NoTradeEvidence("d", "DATA", None),
        ]
    )
    assert summary.observations == 4
    assert summary.protected_losses == 2
    assert summary.missed_winners == 1
    assert summary.unobservable == 1
    assert summary.protected_r == 1.5
    assert summary.missed_r == 1.25
    assert summary.net_counterfactual_r == 0.25
    assert summary.blocker_counts == (("DATA", 1), ("REGIME", 2), ("STRUCTURE", 1))


def test_duplicate_no_trade_observations_are_rejected() -> None:
    row = NoTradeEvidence("x", "REGIME", -1.0)
    with pytest.raises(ValueError, match="duplicate observation_id"):
        summarize_no_trades([row, row])
