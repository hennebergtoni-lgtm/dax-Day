import pytest

from daxlab.research.multiple_testing_preflight import TrialPeriodReturn
from daxlab.research.pbo_audit import run_confirmatory_pbo_audit


PERIODS = [f"P{i}" for i in range(1, 9)]
TRIALS = ["T1", "T2", "T3"]


def _rows():
    values = {
        "T1": [0.05, 0.02, 0.04, 0.01, 0.03, 0.02, 0.05, 0.01],
        "T2": [0.01, -0.01, 0.02, 0.00, 0.01, -0.02, 0.01, 0.00],
        "T3": [-0.01, 0.00, -0.02, 0.01, -0.01, 0.00, -0.02, 0.01],
    }
    return [
        TrialPeriodReturn(trial_id, period_id, values[trial_id][idx])
        for trial_id in TRIALS
        for idx, period_id in enumerate(PERIODS)
    ]


def _run(rows=None, **overrides):
    kwargs = {
        "rows": _rows() if rows is None else rows,
        "expected_trial_count": 3,
        "declared_trial_ids": TRIALS,
        "verified_predeclared_trial_ids": TRIALS,
        "trial_order": TRIALS,
        "period_order": PERIODS,
        "pbo_blocks": 4,
    }
    kwargs.update(overrides)
    return run_confirmatory_pbo_audit(**kwargs)


def test_confirmatory_pbo_audit_is_hash_bound_and_computed():
    result = _run()
    payload = result.to_payload()
    assert 0.0 <= result.pbo <= 1.0
    assert result.n_combinations == 6
    assert result.n_trials == 3
    assert result.n_periods == 8
    assert payload["confirmatory_governance_enforced"] is True
    assert payload["statistics_computed"] is True
    assert payload["purge_enabled"] is False
    assert payload["embargo_enabled"] is False
    assert len(result.multiple_testing_evidence_sha256) == 64
    assert len(result.matrix_sha256) == 64
    assert len(result.audit_sha256) == 64


def test_row_input_order_does_not_change_audit_identity():
    first = _run()
    second = _run(rows=list(reversed(_rows())))
    assert second.multiple_testing_evidence_sha256 == first.multiple_testing_evidence_sha256
    assert second.matrix_sha256 == first.matrix_sha256
    assert second.audit_sha256 == first.audit_sha256
    assert second.pbo == first.pbo


def test_missing_git_verified_predeclaration_blocks_before_pbo():
    with pytest.raises(ValueError, match="confirmatory-ready"):
        _run(verified_predeclared_trial_ids=["T1", "T2"])


def test_incomplete_matrix_blocks_before_pbo():
    with pytest.raises(ValueError, match="confirmatory-ready"):
        _run(rows=_rows()[:-1])


def test_trial_order_must_cover_declared_trials_exactly_once():
    with pytest.raises(ValueError, match="trial_order"):
        _run(trial_order=["T1", "T2", "T2"])


def test_explicit_trial_reordering_changes_matrix_and_audit_identity():
    first = _run()
    second = _run(trial_order=["T3", "T2", "T1"])
    assert second.matrix_sha256 != first.matrix_sha256
    assert second.audit_sha256 != first.audit_sha256
