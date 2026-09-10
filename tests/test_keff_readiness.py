from __future__ import annotations

import numpy as np

from daxlab.research.keff_readiness import (
    BLOCKED,
    READY,
    RESEARCH_ONLY,
    evaluate_keff_readiness,
)
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


def test_full_rank_with_more_periods_than_trials_is_ready() -> None:
    evidence = _evidence(
        [
            [0.1, 0.4, -0.2, 0.8, 0.3, -0.1],
            [-0.3, 0.2, 0.7, -0.4, 0.6, 0.1],
            [0.5, -0.1, 0.2, 0.4, -0.6, 0.9],
        ]
    )
    result = evaluate_keff_readiness(evidence)

    assert result.status == READY
    assert result.ready_for_experimental_keff is True
    assert result.n_trials == 3
    assert result.n_periods == 6
    assert result.max_identifiable_rank == 3
    assert result.matrix_rank == 3
    assert result.correlation_nullity == 0
    assert result.blockers == ()
    assert result.warnings == ()
    assert result.keff_computed is False


def test_more_trials_than_centered_period_rank_is_research_only() -> None:
    evidence = _evidence(
        [
            [0.1, 0.3, -0.2],
            [-0.2, 0.7, 0.1],
            [0.8, -0.4, 0.2],
            [0.5, 0.6, -0.1],
        ]
    )
    result = evaluate_keff_readiness(evidence)

    assert result.status == RESEARCH_ONLY
    assert result.max_identifiable_rank == 2
    assert result.matrix_rank <= 2
    assert result.correlation_nullity >= 2
    assert "PERIOD_COUNT_LIMITS_CORRELATION_RANK" in result.warnings
    assert result.near_zero_eigenvalue_count >= 2
    assert result.keff_computed is False


def test_duplicate_trial_structure_is_research_only_not_invalid() -> None:
    evidence = _evidence(
        [
            [0.1, 0.4, -0.2, 0.8, 0.3, -0.1],
            [0.1, 0.4, -0.2, 0.8, 0.3, -0.1],
            [-0.3, 0.2, 0.7, -0.4, 0.6, 0.1],
        ]
    )
    result = evaluate_keff_readiness(evidence)

    assert result.status == RESEARCH_ONLY
    assert result.matrix_rank == 2
    assert result.correlation_nullity == 1
    assert "OBSERVED_RANK_BELOW_SAMPLE_LIMIT" in result.warnings
    assert "NEAR_ZERO_CORRELATION_EIGENVALUES_PRESENT" in result.warnings


def test_constant_trial_series_blocks_correlation_inference() -> None:
    evidence = _evidence(
        [
            [0.1, 0.4, -0.2, 0.8],
            [1.0, 1.0, 1.0, 1.0],
            [-0.3, 0.2, 0.7, -0.4],
        ]
    )
    result = evaluate_keff_readiness(evidence)

    assert result.status == BLOCKED
    assert result.blockers == ("CONSTANT_OR_INVALID_TRIAL_SERIES",)
    assert result.ready_for_experimental_keff is False
    assert result.keff_computed is False


def test_diagnostic_hash_is_deterministic_and_bound_to_matrix_identity() -> None:
    first = evaluate_keff_readiness(
        _evidence(
            [
                [0.1, 0.4, -0.2, 0.8, 0.3, -0.1],
                [-0.3, 0.2, 0.7, -0.4, 0.6, 0.1],
                [0.5, -0.1, 0.2, 0.4, -0.6, 0.9],
            ]
        )
    )
    second = evaluate_keff_readiness(
        _evidence(
            [
                [0.1, 0.4, -0.2, 0.8, 0.3, -0.1],
                [-0.3, 0.2, 0.7, -0.4, 0.6, 0.1],
                [0.5, -0.1, 0.2, 0.4, -0.6, 0.9],
            ]
        )
    )
    assert first.diagnostic_sha256 == second.diagnostic_sha256
    assert first.to_payload()["dsr_adjustment_applied"] is False
