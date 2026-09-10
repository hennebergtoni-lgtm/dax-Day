import pytest

from daxlab.research.dsr_audit import run_confirmatory_dsr_audit
from daxlab.research.multiple_testing_preflight import TrialPeriodReturn


PERIODS = ["P1", "P2", "P3", "P4", "P5"]
TRIALS = ["T1", "T2", "T3"]


def _rows():
    values = {
        "T1": [0.01, 0.02, -0.01, 0.03, 0.00],
        "T2": [-0.02, 0.00, 0.01, 0.02, -0.01],
        "T3": [0.03, 0.01, 0.02, -0.01, 0.01],
    }
    return [
        TrialPeriodReturn(trial, period, values[trial][idx])
        for trial in TRIALS
        for idx, period in enumerate(PERIODS)
    ]


def _run(rows=None, **overrides):
    kwargs = {
        "rows": _rows() if rows is None else rows,
        "expected_trial_count": 3,
        "declared_trial_ids": TRIALS,
        "verified_predeclared_trial_ids": TRIALS,
        "target_trial_id": "T1",
        "trial_order": TRIALS,
        "period_order": PERIODS,
    }
    kwargs.update(overrides)
    return run_confirmatory_dsr_audit(**kwargs)


def test_confirmatory_dsr_audit_computes_hash_bound_result():
    result = _run()
    payload = result.to_payload()
    assert 0.0 <= result.probability <= 1.0
    assert result.target_trial_id == "T1"
    assert result.n_obs == 5
    assert result.n_trials == 3
    assert result.trial_variance_ddof == 1
    assert result.sharpe_estimator == "DAXLAB_NATIVE_SAMPLE_V1"
    assert len(result.multiple_testing_evidence_sha256) == 64
    assert len(result.dsr_evidence_sha256) == 64
    assert len(result.audit_sha256) == 64
    assert payload["confirmatory_governance_enforced"] is True
    assert payload["statistics_computed"] is True
    assert payload["annualized"] is False
    assert payload["effective_trial_adjustment"] is False


def test_row_input_order_does_not_change_audit_identity():
    first = _run()
    second = _run(rows=list(reversed(_rows())))
    assert second.multiple_testing_evidence_sha256 == first.multiple_testing_evidence_sha256
    assert second.dsr_evidence_sha256 == first.dsr_evidence_sha256
    assert second.audit_sha256 == first.audit_sha256
    assert second.probability == first.probability


def test_missing_git_verified_predeclaration_blocks_before_dsr():
    with pytest.raises(ValueError, match="confirmatory-ready"):
        _run(verified_predeclared_trial_ids=["T1", "T2"])


def test_unknown_target_trial_is_rejected():
    with pytest.raises(ValueError, match="target_trial_id"):
        _run(target_trial_id="TX")


def test_incomplete_matrix_blocks_before_dsr():
    with pytest.raises(ValueError, match="confirmatory-ready"):
        _run(rows=_rows()[:-1])


def test_trial_order_must_cover_declared_trials_exactly_once():
    with pytest.raises(ValueError, match="trial_order"):
        _run(trial_order=["T1", "T2", "T2"])


def test_explicit_trial_reordering_changes_dsr_evidence_and_audit_identity():
    first = _run()
    second = _run(trial_order=["T3", "T2", "T1"])
    assert second.dsr_evidence_sha256 != first.dsr_evidence_sha256
    assert second.audit_sha256 != first.audit_sha256


def test_pbo_partition_issue_does_not_block_dsr_readiness():
    # Five periods are not divisible by the shared readiness helper's internal
    # PBO block count of 4. DSR must still run because that blocker is PBO-only.
    result = _run()
    assert 0.0 <= result.probability <= 1.0
