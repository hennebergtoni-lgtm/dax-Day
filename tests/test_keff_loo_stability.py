from __future__ import annotations

import math

import numpy as np
import pytest

from daxlab.research.keff_loo_stability import evaluate_keff_loo_stability
from daxlab.research.pbo_evidence_adapter import PBOEvidenceMatrix


def _evidence(values: list[list[float]]) -> PBOEvidenceMatrix:
    matrix = np.asarray(values, dtype=float)
    matrix.setflags(write=False)
    return PBOEvidenceMatrix(
        matrix=matrix,
        trial_order=tuple(f"T{i}" for i in range(matrix.shape[0])),
        period_order=tuple(f"P{i}" for i in range(matrix.shape[1])),
        upstream_evidence_sha256="a" * 64,
        matrix_sha256="b" * 64,
    )


def test_one_observation_is_emitted_per_omitted_period() -> None:
    evidence = _evidence(
        [
            [0.1, 0.4, -0.2, 0.8, 0.3, -0.1],
            [-0.3, 0.2, 0.7, -0.4, 0.6, 0.1],
            [0.5, -0.1, 0.2, 0.4, -0.6, 0.9],
        ]
    )
    result = evaluate_keff_loo_stability(evidence)

    assert len(result.observations) == 6
    assert tuple(item.omitted_period_id for item in result.observations) == evidence.period_order
    assert all(item.reduced_n_periods == 5 for item in result.observations)
    assert len({item.child_sha256 for item in result.observations}) == 6
    assert result.confirmatory_use_allowed is False
    assert result.dsr_adjustment_applied is False
    assert result.to_payload()["confidence_interval_claimed"] is False


def test_summary_bounds_contain_all_leave_one_out_estimates() -> None:
    evidence = _evidence(
        [
            [0.1, 0.4, -0.2, 0.8, 0.3, -0.1],
            [-0.3, 0.2, 0.7, -0.4, 0.6, 0.1],
            [0.5, -0.1, 0.2, 0.4, -0.6, 0.9],
        ]
    )
    result = evaluate_keff_loo_stability(evidence)
    entropy = [item.entropy_effective_rank for item in result.observations]
    trace = [item.trace_over_lambda_max_effective_rank for item in result.observations]

    assert math.isclose(result.entropy_min, min(entropy))
    assert math.isclose(result.entropy_max, max(entropy))
    assert result.entropy_min <= result.entropy_median <= result.entropy_max
    assert math.isclose(result.trace_min, min(trace))
    assert math.isclose(result.trace_max, max(trace))
    assert result.trace_min <= result.trace_median <= result.trace_max
    assert result.entropy_max_abs_deviation_from_parent >= 0.0
    assert result.trace_max_abs_deviation_from_parent >= 0.0


def test_stability_result_and_child_hashes_are_deterministic() -> None:
    evidence = _evidence(
        [
            [0.1, 0.4, -0.2, 0.8, 0.3, -0.1],
            [-0.3, 0.2, 0.7, -0.4, 0.6, 0.1],
            [0.5, -0.1, 0.2, 0.4, -0.6, 0.9],
        ]
    )
    first = evaluate_keff_loo_stability(evidence)
    second = evaluate_keff_loo_stability(evidence)

    assert first.stability_sha256 == second.stability_sha256
    assert [item.child_sha256 for item in first.observations] == [
        item.child_sha256 for item in second.observations
    ]


def test_blocked_parent_is_rejected() -> None:
    evidence = _evidence(
        [
            [0.1, 0.4, -0.2, 0.8],
            [1.0, 1.0, 1.0, 1.0],
            [-0.3, 0.2, 0.7, -0.4],
        ]
    )
    with pytest.raises(ValueError, match="parent K_eff evidence is BLOCKED"):
        evaluate_keff_loo_stability(evidence)


def test_child_degeneracy_is_fail_closed() -> None:
    evidence = _evidence(
        [
            [0.0, 1.0, 1.0, 1.0],
            [0.0, 2.0, -1.0, 3.0],
            [0.0, -1.0, 2.0, -2.0],
        ]
    )
    with pytest.raises(ValueError, match="child became BLOCKED"):
        evaluate_keff_loo_stability(evidence)
