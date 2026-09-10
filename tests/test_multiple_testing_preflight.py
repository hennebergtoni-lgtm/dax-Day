from daxlab.research.multiple_testing_preflight import (
    BLOCKED,
    READY,
    preflight_multiple_testing_evidence,
)


def _rows():
    return [
        {"trial_id": "A", "period_id": "P1", "return_value": 1.0, "status": "COMPLETED"},
        {"trial_id": "A", "period_id": "P2", "return_value": -0.5, "status": "COMPLETED"},
        {"trial_id": "B", "period_id": "P1", "return_value": -1.0, "status": "REJECTED"},
        {"trial_id": "B", "period_id": "P2", "return_value": 0.2, "status": "REJECTED"},
    ]


def test_complete_matrix_is_ready():
    result = preflight_multiple_testing_evidence(
        _rows(), expected_trial_count=2, declared_trial_ids=["A", "B"]
    )
    assert result.status == READY
    assert result.ready is True
    assert result.blockers == ()
    assert result.matrix_cell_count == 4
    assert result.to_payload()["statistics_computed"] is False


def test_declared_trial_set_is_required_for_ready():
    result = preflight_multiple_testing_evidence(
        _rows(), expected_trial_count=2, declared_trial_ids=None
    )
    assert result.status == BLOCKED
    assert "DECLARED_TRIAL_SET_REQUIRED" in result.blockers


def test_missing_trial_blocks():
    result = preflight_multiple_testing_evidence(
        _rows()[:2], expected_trial_count=2, declared_trial_ids=["A", "B"]
    )
    assert result.status == BLOCKED
    assert "TRIAL_COUNT_MISMATCH" in result.blockers
    assert "DECLARED_TRIAL_SET_MISMATCH" in result.blockers


def test_missing_period_cell_blocks():
    result = preflight_multiple_testing_evidence(
        _rows()[:-1], expected_trial_count=2, declared_trial_ids=["A", "B"]
    )
    assert result.status == BLOCKED
    assert "INCOMPLETE_TRIAL_PERIOD_MATRIX" in result.blockers
    assert "MATRIX_CELL_COUNT_MISMATCH" in result.blockers


def test_duplicate_cell_blocks():
    result = preflight_multiple_testing_evidence(
        _rows() + [_rows()[0]], expected_trial_count=2, declared_trial_ids=["A", "B"]
    )
    assert result.status == BLOCKED
    assert "DUPLICATE_TRIAL_PERIOD_CELL" in result.blockers


def test_declared_trial_count_and_set_must_match():
    result = preflight_multiple_testing_evidence(
        _rows(), expected_trial_count=2, declared_trial_ids=["A", "C"]
    )
    assert result.status == BLOCKED
    assert "DECLARED_TRIAL_SET_MISMATCH" in result.blockers


def test_unknown_status_blocks():
    rows = _rows()
    rows[0] = {**rows[0], "status": "WINNER_ONLY"}
    result = preflight_multiple_testing_evidence(
        rows, expected_trial_count=2, declared_trial_ids=["A", "B"]
    )
    assert result.status == BLOCKED
    assert "UNKNOWN_TRIAL_STATUS" in result.blockers


def test_non_finite_return_blocks():
    rows = _rows()
    rows[0] = {**rows[0], "return_value": float("nan")}
    result = preflight_multiple_testing_evidence(
        rows, expected_trial_count=2, declared_trial_ids=["A", "B"]
    )
    assert result.status == BLOCKED
    assert "NON_FINITE_RETURN_VALUE" in result.blockers


def test_inconsistent_trial_status_blocks():
    rows = _rows()
    rows[1] = {**rows[1], "status": "REJECTED"}
    result = preflight_multiple_testing_evidence(
        rows, expected_trial_count=2, declared_trial_ids=["A", "B"]
    )
    assert result.status == BLOCKED
    assert "INCONSISTENT_TRIAL_STATUS" in result.blockers


def test_rejected_abandoned_failed_trials_are_not_filtered():
    rows = [
        {"trial_id": "A", "period_id": "P1", "return_value": 1.0, "status": "COMPLETED"},
        {"trial_id": "B", "period_id": "P1", "return_value": -1.0, "status": "ABANDONED"},
        {"trial_id": "C", "period_id": "P1", "return_value": 0.0, "status": "FAILED"},
    ]
    result = preflight_multiple_testing_evidence(
        rows, expected_trial_count=3, declared_trial_ids=["A", "B", "C"]
    )
    assert result.status == READY
    assert result.observed_trial_count == 3


def test_evidence_fingerprint_is_order_independent():
    forward = preflight_multiple_testing_evidence(
        _rows(), expected_trial_count=2, declared_trial_ids=["A", "B"]
    )
    reverse = preflight_multiple_testing_evidence(
        list(reversed(_rows())), expected_trial_count=2, declared_trial_ids=["B", "A"]
    )
    assert forward.evidence_sha256 == reverse.evidence_sha256


def test_evidence_fingerprint_binds_declared_contract():
    good = preflight_multiple_testing_evidence(
        _rows(), expected_trial_count=2, declared_trial_ids=["A", "B"]
    )
    altered = preflight_multiple_testing_evidence(
        _rows(), expected_trial_count=2, declared_trial_ids=["A", "C"]
    )
    assert good.evidence_sha256 != altered.evidence_sha256


def test_expected_trial_count_must_be_at_least_two():
    try:
        preflight_multiple_testing_evidence(
            [], expected_trial_count=1, declared_trial_ids=[]
        )
    except ValueError as exc:
        assert "expected_trial_count" in str(exc)
    else:
        raise AssertionError("expected ValueError")
