import pytest

from daxlab.research.filter_candidate_readiness import (
    FilterCandidateEvidence,
    ReadinessThresholds,
    evaluate_filter_candidate_readiness,
)


def thresholds():
    return ReadinessThresholds(
        min_changed_decisions=2,
        min_trade_survival=0.50,
        min_cash_delta_eur=10.0,
        max_drawdown_worsening_eur=5.0,
    )


def evidence(**overrides):
    values = dict(
        candidate_id="ATR001",
        activation_status="ACTIVATED",
        changed_decisions=4,
        trade_survival=0.75,
        cash_delta_eur=20.0,
        drawdown_delta_eur=0.0,
        comparison_status="COMPLETE_COMPARISON",
        pareto_dominated=False,
    )
    values.update(overrides)
    return FilterCandidateEvidence(**values)


def test_research_ready_does_not_promote_or_enable_execution():
    result = evaluate_filter_candidate_readiness(evidence(), thresholds())
    assert result.status == "RESEARCH_READY"
    assert result.blockers == ()
    assert result.research_only is True
    assert result.automatic_promotion is False
    assert result.execution_capability == "NONE"
    assert result.order_execution_enabled is False


def test_false_null_activation_is_blocked():
    result = evaluate_filter_candidate_readiness(
        evidence(activation_status="NO_OBSERVED_ACTIVATION", changed_decisions=0), thresholds()
    )
    assert "FILTER_NOT_ACTIVATED" in result.blockers
    assert "INSUFFICIENT_DECISION_EFFECT" in result.blockers


def test_trade_starvation_cash_and_drawdown_fail_independently():
    result = evaluate_filter_candidate_readiness(
        evidence(trade_survival=0.20, cash_delta_eur=-10.0, drawdown_delta_eur=9.0), thresholds()
    )
    assert "TRADE_SURVIVAL_TOO_LOW" in result.blockers
    assert "CASH_DELTA_BELOW_PROTOCOL" in result.blockers
    assert "DRAWDOWN_WORSENING_ABOVE_PROTOCOL" in result.blockers


def test_incomplete_and_pareto_dominated_are_blocked():
    result = evaluate_filter_candidate_readiness(
        evidence(comparison_status="INCOMPLETE_CAPITAL_PATH", pareto_dominated=True), thresholds()
    )
    assert "INCOMPLETE_CAPITAL_PATH" in result.blockers
    assert "PARETO_DOMINATED" in result.blockers


def test_thresholds_are_part_of_evidence_hash():
    first = evaluate_filter_candidate_readiness(evidence(), thresholds())
    second = evaluate_filter_candidate_readiness(
        evidence(),
        ReadinessThresholds(2, 0.60, 10.0, 5.0),
    )
    assert first.evidence_hash != second.evidence_hash


def test_no_hidden_threshold_defaults_or_invalid_ranges():
    with pytest.raises(TypeError):
        ReadinessThresholds()
    with pytest.raises(ValueError):
        ReadinessThresholds(0, 0.5, 0.0, 0.0)
    with pytest.raises(ValueError):
        ReadinessThresholds(1, 1.1, 0.0, 0.0)
    with pytest.raises(ValueError):
        ReadinessThresholds(1, 0.5, 0.0, -1.0)
