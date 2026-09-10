import numpy as np
import pytest

from daxlab.research.multiple_testing_preflight import TrialPeriodReturn
from daxlab.research.pbo_evidence_adapter import build_pbo_evidence_matrix


def _rows():
    return [
        TrialPeriodReturn("T1", "P1", 0.10),
        TrialPeriodReturn("T1", "P2", -0.05),
        TrialPeriodReturn("T1", "P3", 0.20),
        TrialPeriodReturn("T1", "P4", 0.00),
        TrialPeriodReturn("T2", "P1", 0.00),
        TrialPeriodReturn("T2", "P2", 0.10),
        TrialPeriodReturn("T2", "P3", -0.10),
        TrialPeriodReturn("T2", "P4", 0.05),
    ]


def test_input_row_order_does_not_change_explicit_matrix_identity():
    rows = _rows()
    first = build_pbo_evidence_matrix(
        rows, trial_order=["T1", "T2"], period_order=["P1", "P2", "P3", "P4"]
    )
    second = build_pbo_evidence_matrix(
        list(reversed(rows)),
        trial_order=["T1", "T2"],
        period_order=["P1", "P2", "P3", "P4"],
    )
    np.testing.assert_array_equal(first.matrix, second.matrix)
    assert first.upstream_evidence_sha256 == second.upstream_evidence_sha256
    assert first.matrix_sha256 == second.matrix_sha256


def test_trial_order_is_bound_into_matrix_identity():
    first = build_pbo_evidence_matrix(
        _rows(), trial_order=["T1", "T2"], period_order=["P1", "P2", "P3", "P4"]
    )
    second = build_pbo_evidence_matrix(
        _rows(), trial_order=["T2", "T1"], period_order=["P1", "P2", "P3", "P4"]
    )
    assert first.matrix_sha256 != second.matrix_sha256
    np.testing.assert_array_equal(first.matrix[0], second.matrix[1])


def test_period_order_is_bound_into_matrix_identity():
    first = build_pbo_evidence_matrix(
        _rows(), trial_order=["T1", "T2"], period_order=["P1", "P2", "P3", "P4"]
    )
    second = build_pbo_evidence_matrix(
        _rows(), trial_order=["T1", "T2"], period_order=["P4", "P3", "P2", "P1"]
    )
    assert first.matrix_sha256 != second.matrix_sha256
    assert first.period_order != second.period_order


def test_incomplete_evidence_is_rejected_before_matrix_build():
    rows = _rows()[:-1]
    with pytest.raises(ValueError, match="not READY"):
        build_pbo_evidence_matrix(
            rows, trial_order=["T1", "T2"], period_order=["P1", "P2", "P3", "P4"]
        )


def test_period_order_must_match_observed_period_set():
    with pytest.raises(ValueError, match="period_order"):
        build_pbo_evidence_matrix(
            _rows(), trial_order=["T1", "T2"], period_order=["P1", "P2", "P3", "PX"]
        )


def test_returned_matrix_is_read_only():
    result = build_pbo_evidence_matrix(
        _rows(), trial_order=["T1", "T2"], period_order=["P1", "P2", "P3", "P4"]
    )
    assert result.matrix.flags.writeable is False
    with pytest.raises(ValueError):
        result.matrix[0, 0] = 999.0


def test_payload_does_not_claim_statistics_were_computed():
    result = build_pbo_evidence_matrix(
        _rows(), trial_order=["T1", "T2"], period_order=["P1", "P2", "P3", "P4"]
    )
    payload = result.to_payload()
    assert payload["statistics_computed"] is False
    assert payload["matrix"] == [
        [0.10, -0.05, 0.20, 0.00],
        [0.00, 0.10, -0.10, 0.05],
    ]
