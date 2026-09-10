import math

import pytest

from daxlab.research.classical_dsr import (
    classical_deflated_sharpe_ratio_from_statistics,
    expected_max_standard_normal,
    probabilistic_sharpe_ratio_from_statistics,
)


def test_expected_max_standard_normal_reference_value():
    assert expected_max_standard_normal(50) == pytest.approx(2.276303093420348, abs=1e-12)


def test_classical_dsr_reference_components():
    result = classical_deflated_sharpe_ratio_from_statistics(
        observed_sr=0.1,
        n_obs=252,
        skewness=-0.3,
        pearson_kurtosis=4.2,
        n_trials=50,
        trial_sharpe_variance=0.0025,
        trial_variance_ddof=1,
    )
    assert result.expected_max_z == pytest.approx(2.276303093420348, abs=1e-12)
    assert result.sr_star == pytest.approx(0.1138151546710174, abs=1e-12)
    assert result.z_score == pytest.approx(-0.21482950883367993, abs=1e-12)
    assert result.probability == pytest.approx(0.4149501226369048, abs=1e-12)
    payload = result.to_payload()
    assert payload["method"] == "BAILEY_LOPEZ_DE_PRADO_CLASSICAL_DSR"
    assert payload["sharpe_unit"] == "NATIVE_PERIOD"
    assert payload["trial_variance_ddof"] == 1
    assert payload["autocorrelation_adjustment"] is False
    assert payload["effective_trial_adjustment"] is False


def test_single_trial_reduces_to_psr_against_zero():
    dsr = classical_deflated_sharpe_ratio_from_statistics(
        observed_sr=0.08,
        n_obs=100,
        skewness=0.0,
        pearson_kurtosis=3.0,
        n_trials=1,
        trial_sharpe_variance=0.0,
        trial_variance_ddof=0,
    )
    psr, z = probabilistic_sharpe_ratio_from_statistics(
        observed_sr=0.08,
        benchmark_sr=0.0,
        n_obs=100,
        skewness=0.0,
        pearson_kurtosis=3.0,
    )
    assert dsr.sr_star == 0.0
    assert dsr.probability == pytest.approx(psr, abs=1e-15)
    assert dsr.z_score == pytest.approx(z, abs=1e-15)


def test_non_native_sharpe_unit_is_rejected():
    with pytest.raises(ValueError, match="NATIVE_PERIOD"):
        classical_deflated_sharpe_ratio_from_statistics(
            observed_sr=1.5,
            n_obs=252,
            skewness=0.0,
            pearson_kurtosis=3.0,
            n_trials=10,
            trial_sharpe_variance=0.2,
            trial_variance_ddof=1,
            sharpe_unit="ANNUALIZED",
        )


def test_negative_trial_variance_is_rejected():
    with pytest.raises(ValueError, match="variance"):
        classical_deflated_sharpe_ratio_from_statistics(
            observed_sr=0.1,
            n_obs=20,
            skewness=0.0,
            pearson_kurtosis=3.0,
            n_trials=2,
            trial_sharpe_variance=-0.01,
            trial_variance_ddof=1,
        )


def test_invalid_ddof_is_rejected():
    with pytest.raises(ValueError, match="ddof"):
        classical_deflated_sharpe_ratio_from_statistics(
            observed_sr=0.1,
            n_obs=20,
            skewness=0.0,
            pearson_kurtosis=3.0,
            n_trials=2,
            trial_sharpe_variance=0.01,
            trial_variance_ddof=2,
        )


def test_non_positive_psr_denominator_fails_closed():
    # 1 - skew*SR + ((kurt-1)/4)*SR^2 = 1 - 2 = -1 here.
    with pytest.raises(ValueError, match="denominator"):
        probabilistic_sharpe_ratio_from_statistics(
            observed_sr=1.0,
            benchmark_sr=0.0,
            n_obs=20,
            skewness=2.0,
            pearson_kurtosis=1.0,
        )


def test_non_finite_input_is_rejected():
    with pytest.raises(ValueError, match="finite"):
        probabilistic_sharpe_ratio_from_statistics(
            observed_sr=math.inf,
            benchmark_sr=0.0,
            n_obs=20,
            skewness=0.0,
            pearson_kurtosis=3.0,
        )
