from __future__ import annotations

import math

import numpy as np
import pytest

from daxlab.research.experimental_keff import estimate_raw_correlation_effective_rank
from daxlab.research.keff_readiness import BLOCKED, READY, RESEARCH_ONLY, evaluate_keff_readiness
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


def test_orthogonal_trial_structure_has_keff_equal_to_trial_count() -> None:
    evidence = _evidence(
        [
            [1.0, 1.0, -1.0, -1.0],
            [1.0, -1.0, 1.0, -1.0],
            [1.0, -1.0, -1.0, 1.0],
        ]
    )
    readiness = evaluate_keff_readiness(evidence)
    assert readiness.status == READY

    result = estimate_raw_correlation_effective_rank(readiness)
    assert math.isclose(result.k_eff, 3.0, rel_tol=0.0, abs_tol=1e-12)
    assert result.confirmatory_use_allowed is False
    assert result.research_only is True
    assert result.dsr_adjustment_applied is False


def test_duplicate_structure_reduces_effective_rank() -> None:
    evidence = _evidence(
        [
            [1.0, 1.0, -1.0, -1.0, 0.5],
            [1.0, 1.0, -1.0, -1.0, 0.5],
            [1.0, -1.0, 1.0, -1.0, -0.5],
        ]
    )
    readiness = evaluate_keff_readiness(evidence)
    assert readiness.status == RESEARCH_ONLY

    result = estimate_raw_correlation_effective_rank(readiness)
    assert 1.0 < result.k_eff < 3.0
    assert result.readiness_status == RESEARCH_ONLY
    assert result.confirmatory_use_allowed is False


def test_sample_limited_readiness_remains_research_only() -> None:
    evidence = _evidence(
        [
            [0.1, 0.3, -0.2],
            [-0.2, 0.7, 0.1],
            [0.8, -0.4, 0.2],
            [0.5, 0.6, -0.1],
        ]
    )
    readiness = evaluate_keff_readiness(evidence)
    assert readiness.status == RESEARCH_ONLY

    result = estimate_raw_correlation_effective_rank(readiness)
    assert result.readiness_status == RESEARCH_ONLY
    assert result.n_trials == 4
    assert result.n_periods == 3
    assert result.confirmatory_use_allowed is False
    assert result.to_payload()["shrinkage_applied"] is False


def test_blocked_readiness_cannot_be_estimated() -> None:
    evidence = _evidence(
        [
            [0.1, 0.4, -0.2, 0.8],
            [1.0, 1.0, 1.0, 1.0],
            [-0.3, 0.2, 0.7, -0.4],
        ]
    )
    readiness = evaluate_keff_readiness(evidence)
    assert readiness.status == BLOCKED

    with pytest.raises(ValueError, match="BLOCKED"):
        estimate_raw_correlation_effective_rank(readiness)


def test_estimator_hash_is_deterministic_and_bound_to_readiness() -> None:
    evidence = _evidence(
        [
            [1.0, 1.0, -1.0, -1.0],
            [1.0, -1.0, 1.0, -1.0],
            [1.0, -1.0, -1.0, 1.0],
        ]
    )
    readiness = evaluate_keff_readiness(evidence)
    first = estimate_raw_correlation_effective_rank(readiness)
    second = estimate_raw_correlation_effective_rank(readiness)
    assert first.estimator_sha256 == second.estimator_sha256
    assert first.readiness_diagnostic_sha256 == readiness.diagnostic_sha256
