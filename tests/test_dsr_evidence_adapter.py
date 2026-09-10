import numpy as np
import pytest

from daxlab.research.dsr_evidence_adapter import build_dsr_evidence_statistics
from daxlab.research.multiple_testing_preflight import TrialPeriodReturn


PERIODS = ["P1", "P2", "P3", "P4"]
TRIALS = ["T1", "T2", "T3"]


def _rows():
    values = {
        "T1": [0.01, 0.02, -0.01, 0.03],
        "T2": [-0.02, 0.00, 0.01, 0.02],
        "T3": [0.03, 0.01, 0.02, -0.01],
    }
    return [
        TrialPeriodReturn(trial, period, values[trial][idx])
        for trial in TRIALS
        for idx, period in enumerate(PERIODS)
    ]


def test_reference_statistics_match_declared_v1_convention():
    result = build_dsr_evidence_statistics(
        _rows(), target_trial_id="T1", trial_order=TRIALS, period_order=PERIODS
    )
    values = np.asarray([0.01, 0.02, -0.01, 0.03], dtype=float)
    mean = values.mean()
    std = values.std(ddof=1)
    centered = values - mean
    assert result.observed_sr == pytest.approx(mean / std)
    assert result.skewness == pytest.approx(np.mean(centered**3) / std**3)
    assert result.pearson_kurtosis == pytest.approx(np.mean(centered**4) / std**4)
    assert result.n_obs == 4
    assert result.n_trials == 3
    assert result.trial_variance_ddof == 1
    assert result.sharpe_estimator == "DAXLAB_NATIVE_SAMPLE_V1"


def test_input_row_order_does_not_change_evidence_identity():
    first = build_dsr_evidence_statistics(
        _rows(), target_trial_id="T1", trial_order=TRIALS, period_order=PERIODS
    )
    second = build_dsr_evidence_statistics(
        list(reversed(_rows())),
        target_trial_id="T1",
        trial_order=TRIALS,
        period_order=PERIODS,
    )
    assert second.upstream_evidence_sha256 == first.upstream_evidence_sha256
    assert second.evidence_sha256 == first.evidence_sha256
    assert second.observed_sr == first.observed_sr


def test_target_trial_is_explicit_and_changes_evidence():
    first = build_dsr_evidence_statistics(
        _rows(), target_trial_id="T1", trial_order=TRIALS, period_order=PERIODS
    )
    second = build_dsr_evidence_statistics(
        _rows(), target_trial_id="T2", trial_order=TRIALS, period_order=PERIODS
    )
    assert second.target_trial_id == "T2"
    assert second.evidence_sha256 != first.evidence_sha256


def test_trial_reordering_changes_evidence_identity():
    first = build_dsr_evidence_statistics(
        _rows(), target_trial_id="T1", trial_order=TRIALS, period_order=PERIODS
    )
    second = build_dsr_evidence_statistics(
        _rows(), target_trial_id="T1", trial_order=["T3", "T2", "T1"], period_order=PERIODS
    )
    assert second.evidence_sha256 != first.evidence_sha256


def test_period_reordering_changes_evidence_identity():
    first = build_dsr_evidence_statistics(
        _rows(), target_trial_id="T1", trial_order=TRIALS, period_order=PERIODS
    )
    second = build_dsr_evidence_statistics(
        _rows(),
        target_trial_id="T1",
        trial_order=TRIALS,
        period_order=list(reversed(PERIODS)),
    )
    assert second.evidence_sha256 != first.evidence_sha256


def test_incomplete_multiple_testing_evidence_is_rejected():
    with pytest.raises(ValueError, match="not READY"):
        build_dsr_evidence_statistics(
            _rows()[:-1], target_trial_id="T1", trial_order=TRIALS, period_order=PERIODS
        )


def test_target_must_exist_in_trial_order():
    with pytest.raises(ValueError, match="target_trial_id"):
        build_dsr_evidence_statistics(
            _rows(), target_trial_id="TX", trial_order=TRIALS, period_order=PERIODS
        )


def test_constant_trial_series_is_rejected_fail_closed():
    rows = _rows()
    rows = [row for row in rows if row.trial_id != "T3"] + [
        TrialPeriodReturn("T3", period, 0.01) for period in PERIODS
    ]
    with pytest.raises(ValueError, match="zero or invalid sample variance"):
        build_dsr_evidence_statistics(
            rows, target_trial_id="T1", trial_order=TRIALS, period_order=PERIODS
        )


def test_payload_is_explicit_about_estimation_vs_dsr():
    payload = build_dsr_evidence_statistics(
        _rows(), target_trial_id="T1", trial_order=TRIALS, period_order=PERIODS
    ).to_payload()
    assert payload["summary_statistics_computed"] is True
    assert payload["dsr_computed"] is False
    assert payload["annualized"] is False
    assert payload["sharpe_unit"] == "NATIVE_PERIOD"
