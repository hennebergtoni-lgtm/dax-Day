import pytest

from daxlab.research.failure_analysis import (
    FailureTag,
    OutcomeClass,
    TradeEvidence,
    classify_trade,
    classify_trades,
    excursion_summary,
    hypothesis_eligible,
    loss_concentration,
    tag_counts,
)


def sample_trades() -> list[TradeEvidence]:
    return [
        TradeEvidence(
            trade_id="a",
            r=-1.0,
            mfe_r=1.2,
            mae_r=-1.1,
            entry_mode="breakout",
            exit_reason="stop",
            structure_result="false_breakout",
            or_atr_bucket="low",
            prev_range_bucket="extended",
            cost_r_normal=0.1,
            cost_r_stress_1_5x=-0.02,
            cost_r_stress_2x=-0.08,
        ),
        TradeEvidence(
            trade_id="b",
            r=-0.5,
            mfe_r=0.3,
            mae_r=-0.7,
            entry_mode="retest",
            exit_reason="time",
            structure_result="failed_retest",
            or_atr_bucket="high",
            prev_range_bucket="normal",
        ),
        TradeEvidence(trade_id="c", r=1.5, entry_mode="retest"),
    ]


def test_trade_classification_is_descriptive() -> None:
    result = classify_trade(sample_trades()[0])
    assert result.outcome is OutcomeClass.LOSS
    assert result.tags == (
        FailureTag.STOP_OUT,
        FailureTag.ADVERSE_EXCURSION,
        FailureTag.MISSED_FAVORABLE_EXCURSION,
        FailureTag.FALSE_BREAKOUT,
        FailureTag.COST_SENSITIVE,
    )


def test_failure_aggregates_are_deterministic() -> None:
    trades = sample_trades()
    classified = classify_trades(trades)
    assert tag_counts(classified)["FAILED_RETEST"] == 1
    assert loss_concentration(trades, "entry_mode") == {
        "breakout": (1, -1.0),
        "retest": (1, -0.5),
    }
    assert excursion_summary(trades) == {
        "loss_count": 2,
        "mean_loss_mfe_r": 0.75,
        "mean_loss_mae_r": -0.9,
        "losses_with_mfe_ge_1r": 1,
    }


def test_duplicate_trade_evidence_is_rejected() -> None:
    trade = TradeEvidence(trade_id="x", r=-1.0)
    with pytest.raises(ValueError, match="duplicate trade_id"):
        classify_trades([trade, trade])


def test_unknown_concentration_dimension_is_rejected() -> None:
    with pytest.raises(ValueError, match="unsupported concentration"):
        loss_concentration(sample_trades(), "r")


def test_hypothesis_gate_requires_sample_and_period_breadth() -> None:
    assert hypothesis_eligible(observations=20, distinct_periods=3)
    assert not hypothesis_eligible(observations=19, distinct_periods=10)
    assert not hypothesis_eligible(observations=100, distinct_periods=2)
