from __future__ import annotations

import pytest

from daxlab.research.filter_activation import (
    ACTIVATED,
    NON_MONOTONIC_GATE_BEHAVIOR,
    NO_OBSERVED_ACTIVATION,
    evaluate_filter_activation,
)


def test_restrictive_filter_activation_is_observed() -> None:
    result = evaluate_filter_activation(
        [True, True, True, True],
        [True, False, True, False],
        filter_id="F",
    )
    assert result.status == ACTIVATED
    assert result.changed_decisions == 2
    assert result.newly_blocked == 2
    assert result.newly_allowed == 0
    assert result.activation_ratio == pytest.approx(0.5)
    assert result.to_payload()["effectiveness_conclusion_allowed"] is True


def test_no_observed_activation_is_not_interpreted_as_effectiveness() -> None:
    result = evaluate_filter_activation(
        [True, False, True],
        [True, False, True],
        filter_id="F",
    )
    assert result.status == NO_OBSERVED_ACTIVATION
    assert result.changed_decisions == 0
    assert result.to_payload()["effectiveness_conclusion_allowed"] is False


def test_non_monotonic_gate_behavior_is_flagged() -> None:
    result = evaluate_filter_activation(
        [True, False, True],
        [True, True, False],
        filter_id="F",
    )
    assert result.status == NON_MONOTONIC_GATE_BEHAVIOR
    assert result.newly_allowed == 1
    assert result.newly_blocked == 1
    assert result.to_payload()["effectiveness_conclusion_allowed"] is False


def test_decision_change_changes_evidence_identity() -> None:
    first = evaluate_filter_activation(
        [True, True, True], [True, False, True], filter_id="F"
    )
    second = evaluate_filter_activation(
        [True, True, True], [True, True, False], filter_id="F"
    )
    assert first.evidence_sha256 != second.evidence_sha256


def test_invalid_inputs_fail_closed() -> None:
    with pytest.raises(ValueError, match="filter_id"):
        evaluate_filter_activation([True], [False], filter_id=" ")
    with pytest.raises(ValueError, match="at least one"):
        evaluate_filter_activation([], [], filter_id="F")
    with pytest.raises(ValueError, match="identical shape"):
        evaluate_filter_activation([True, True], [True], filter_id="F")
