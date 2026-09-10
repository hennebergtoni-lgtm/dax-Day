import math

import pytest

from daxlab.research.classical_dsr import probabilistic_sharpe_ratio_from_statistics
from daxlab.research.classical_mintrl import classical_minimum_track_record_length_from_statistics


def test_mintrl_inverts_classical_psr_sample_length_relation():
    result = classical_minimum_track_record_length_from_statistics(
        observed_sr=0.25,
        benchmark_sr=0.0,
        skewness=-0.2,
        pearson_kurtosis=4.0,
        confidence=0.95,
    )
    required = int(result.required_observations)
    probability, _ = probabilistic_sharpe_ratio_from_statistics(
        observed_sr=0.25,
        benchmark_sr=0.0,
        n_obs=required,
        skewness=-0.2,
        pearson_kurtosis=4.0,
    )
    assert probability >= 0.95
    if required > 2:
        previous, _ = probabilistic_sharpe_ratio_from_statistics(
            observed_sr=0.25,
            benchmark_sr=0.0,
            n_obs=required - 1,
            skewness=-0.2,
            pearson_kurtosis=4.0,
        )
        assert previous < 0.95


def test_observed_sharpe_not_above_benchmark_is_never_significant_at_current_estimate():
    result = classical_minimum_track_record_length_from_statistics(
        observed_sr=0.0,
        benchmark_sr=0.1,
        skewness=0.0,
        pearson_kurtosis=3.0,
    )
    assert result.status == "NEVER_SIGNIFICANT_AT_CURRENT_ESTIMATE"
    assert math.isinf(result.min_track_record_length)
    assert math.isinf(result.required_observations)


def test_extreme_positive_sharpe_keeps_continuous_result_but_requires_at_least_two_obs():
    result = classical_minimum_track_record_length_from_statistics(
        observed_sr=100.0,
        benchmark_sr=0.0,
        skewness=0.0,
        pearson_kurtosis=1.000001,
        confidence=0.95,
    )
    assert 1.0 < result.min_track_record_length < 2.0
    assert result.required_observations == 2.0


@pytest.mark.parametrize("confidence", [0.5, 1.0, 0.0, 1.1])
def test_invalid_confidence_is_rejected(confidence):
    with pytest.raises(ValueError, match="confidence"):
        classical_minimum_track_record_length_from_statistics(
            observed_sr=0.2,
            benchmark_sr=0.0,
            skewness=0.0,
            pearson_kurtosis=3.0,
            confidence=confidence,
        )


def test_non_positive_psr_denominator_is_rejected_not_clamped():
    with pytest.raises(ValueError, match="denominator"):
        classical_minimum_track_record_length_from_statistics(
            observed_sr=1.0,
            benchmark_sr=0.0,
            skewness=2.0,
            pearson_kurtosis=1.0,
        )


def test_annualized_sharpe_unit_is_rejected():
    with pytest.raises(ValueError, match="NATIVE_PERIOD"):
        classical_minimum_track_record_length_from_statistics(
            observed_sr=0.2,
            benchmark_sr=0.0,
            skewness=0.0,
            pearson_kurtosis=3.0,
            sharpe_unit="ANNUALIZED",
        )


def test_payload_discloses_no_autocorrelation_adjustment():
    payload = classical_minimum_track_record_length_from_statistics(
        observed_sr=0.2,
        benchmark_sr=0.0,
        skewness=0.0,
        pearson_kurtosis=3.0,
    ).to_payload()
    assert payload["annualized"] is False
    assert payload["autocorrelation_adjustment"] is False
