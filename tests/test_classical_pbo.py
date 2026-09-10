import math

import numpy as np
import pytest

from daxlab.research.classical_pbo import classical_probability_of_backtest_overfitting


def test_pbo_combination_count_and_payload():
    returns = np.array(
        [
            [0.02, 0.01, 0.03, 0.02, 0.01, 0.02, 0.03, 0.01],
            [0.01, 0.00, 0.02, 0.01, 0.00, 0.01, 0.02, 0.00],
        ]
    )
    result = classical_probability_of_backtest_overfitting(returns, n_splits=4)
    assert result.n_combinations == math.comb(4, 2)
    payload = result.to_payload()
    assert payload["schema_version"] == "DAXLAB_CLASSICAL_PBO_V1"
    assert payload["purge_enabled"] is False
    assert payload["embargo_enabled"] is False
    assert payload["performance_metric"] == "SAMPLE_SHARPE_DDOF1"


def test_consistent_leader_has_low_pbo():
    returns = np.array(
        [
            [0.04, 0.01, 0.03, 0.02, 0.05, 0.01, 0.04, 0.02],
            [0.01, -0.01, 0.00, 0.01, -0.01, 0.00, 0.01, -0.01],
            [-0.01, 0.00, -0.02, 0.00, -0.01, -0.02, 0.00, -0.01],
        ]
    )
    result = classical_probability_of_backtest_overfitting(returns, n_splits=4)
    assert 0.0 <= result.pbo <= 0.5


def test_regime_flipping_leaders_show_overfitting_signal():
    returns = np.array(
        [
            [0.05, 0.04, 0.05, 0.04, -0.03, -0.04, -0.03, -0.04],
            [-0.03, -0.04, -0.03, -0.04, 0.05, 0.04, 0.05, 0.04],
            [0.01, 0.00, 0.01, 0.00, 0.01, 0.00, 0.01, 0.00],
        ]
    )
    result = classical_probability_of_backtest_overfitting(returns, n_splits=4)
    assert result.pbo >= 0.5


def test_tied_oos_scores_use_finite_average_rank_logit():
    returns = np.array(
        [
            [0.02, 0.01, 0.03, 0.00],
            [0.02, 0.01, 0.03, 0.00],
            [0.00, -0.01, 0.01, -0.02],
        ]
    )
    result = classical_probability_of_backtest_overfitting(returns, n_splits=2)
    assert all(math.isfinite(value) for value in result.logits)


def test_constant_slices_are_scored_as_zero_not_infinite():
    returns = np.array(
        [
            [0.01, 0.01, 0.01, 0.01],
            [0.00, 0.00, 0.00, 0.00],
        ]
    )
    result = classical_probability_of_backtest_overfitting(returns, n_splits=2)
    assert 0.0 <= result.pbo <= 1.0


def test_rejects_odd_split_count():
    returns = np.ones((2, 6))
    with pytest.raises(ValueError, match="even integer"):
        classical_probability_of_backtest_overfitting(returns, n_splits=3)


def test_rejects_too_short_matrix_for_splits():
    returns = np.ones((2, 3))
    with pytest.raises(ValueError, match="n_periods"):
        classical_probability_of_backtest_overfitting(returns, n_splits=4)


def test_rejects_nonfinite_matrix():
    returns = np.array([[0.1, np.nan, 0.2, 0.3], [0.0, 0.1, 0.0, 0.1]])
    with pytest.raises(ValueError, match="finite"):
        classical_probability_of_backtest_overfitting(returns, n_splits=2)


def test_requires_two_periods_per_cscv_half():
    returns = np.array([[0.1, 0.2], [0.0, 0.1]])
    with pytest.raises(ValueError, match="CSCV half"):
        classical_probability_of_backtest_overfitting(returns, n_splits=2)
