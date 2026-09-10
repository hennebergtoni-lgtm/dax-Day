from daxlab.research.multiple_testing_preflight import TrialPeriodReturn
from daxlab.research.statistics_readiness import (
    BLOCKED,
    READY,
    preflight_statistics_readiness,
)


def _rows(trials=("t1", "t2"), periods=tuple(f"p{i}" for i in range(1, 9))):
    return [
        TrialPeriodReturn(
            trial_id=trial,
            period_id=period,
            return_value=float(index + offset) / 100.0,
        )
        for offset, trial in enumerate(trials)
        for index, period in enumerate(periods, start=1)
    ]


def test_full_confirmatory_readiness_is_green():
    periods = tuple(f"p{i}" for i in range(1, 9))
    result = preflight_statistics_readiness(
        _rows(periods=periods),
        expected_trial_count=2,
        declared_trial_ids=["t1", "t2"],
        verified_predeclared_trial_ids=["t1", "t2"],
        period_order=periods,
        pbo_blocks=4,
    )
    assert result.status == READY
    assert result.ready is True
    assert result.dsr_ready is True
    assert result.pbo_ready is True
    assert result.confirmatory_governance_required is True
    assert result.blockers == ()
    assert result.to_payload()["statistics_computed"] is False


def test_missing_chronology_verification_blocks_both_statistics():
    periods = tuple(f"p{i}" for i in range(1, 9))
    result = preflight_statistics_readiness(
        _rows(periods=periods),
        expected_trial_count=2,
        declared_trial_ids=["t1", "t2"],
        verified_predeclared_trial_ids=["t1"],
        period_order=periods,
        pbo_blocks=4,
    )
    assert result.status == BLOCKED
    assert result.dsr_ready is False
    assert result.pbo_ready is False
    assert "NOT_ALL_DECLARED_TRIALS_CHRONOLOGY_VERIFIED" in result.blockers


def test_period_order_set_mismatch_blocks_both():
    periods = tuple(f"p{i}" for i in range(1, 9))
    wrong_order = periods[:-1] + ("p9",)
    result = preflight_statistics_readiness(
        _rows(periods=periods),
        expected_trial_count=2,
        declared_trial_ids=["t1", "t2"],
        verified_predeclared_trial_ids=["t1", "t2"],
        period_order=wrong_order,
        pbo_blocks=4,
    )
    assert result.dsr_ready is False
    assert result.pbo_ready is False
    assert "PERIOD_ORDER_SET_MISMATCH" in result.blockers


def test_pbo_partition_blocker_does_not_block_dsr():
    periods = tuple(f"p{i}" for i in range(1, 7))
    result = preflight_statistics_readiness(
        _rows(periods=periods),
        expected_trial_count=2,
        declared_trial_ids=["t1", "t2"],
        verified_predeclared_trial_ids=["t1", "t2"],
        period_order=periods,
        pbo_blocks=4,
    )
    assert result.status == BLOCKED
    assert result.dsr_ready is True
    assert result.pbo_ready is False
    assert "PERIOD_COUNT_NOT_DIVISIBLE_BY_PBO_BLOCKS" in result.blockers


def test_too_few_periods_blocks_dsr_and_pbo():
    periods = ("p1", "p2", "p3")
    result = preflight_statistics_readiness(
        _rows(periods=periods),
        expected_trial_count=2,
        declared_trial_ids=["t1", "t2"],
        verified_predeclared_trial_ids=["t1", "t2"],
        period_order=periods,
        pbo_blocks=4,
    )
    assert result.dsr_ready is False
    assert result.pbo_ready is False
    assert "INSUFFICIENT_PERIODS_FOR_DSR_MOMENTS" in result.blockers
    assert "PBO_BLOCK_COUNT_EXCEEDS_PERIOD_COUNT" in result.blockers


def test_base_matrix_preflight_blocker_propagates():
    periods = ("p1", "p2", "p3", "p4")
    rows = _rows(periods=periods)
    rows.pop()
    result = preflight_statistics_readiness(
        rows,
        expected_trial_count=2,
        declared_trial_ids=["t1", "t2"],
        verified_predeclared_trial_ids=["t1", "t2"],
        period_order=periods,
        pbo_blocks=4,
    )
    assert result.dsr_ready is False
    assert result.pbo_ready is False
    assert "INCOMPLETE_TRIAL_PERIOD_MATRIX" in result.blockers
