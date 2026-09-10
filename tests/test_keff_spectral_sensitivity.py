from __future__ import annotations

import math

import numpy as np
import pytest

from daxlab.research.keff_readiness import BLOCKED, READY, RESEARCH_ONLY, evaluate_keff_readiness
from daxlab.research.keff_spectral_sensitivity import evaluate_keff_spectral_sensitivity
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


def test_isotropic_spectrum_gives_identical_effective_ranks() -> None:
    evidence = _evidence(
        [
            [1.0, 1.0, -1.0, -1.0],
            [1.0, -1.0, 1.0, -1.0],
            [1.0, -1.0, -1.0, 1.0],
        ]
    )
    readiness = evaluate_keff_readiness(evidence)
    assert readiness.status == READY

    result = evaluate_keff_spectral_sensitivity(readiness)
    assert math.isclose(result.entropy_effective_rank, 3.0, abs_tol=1e-12)
    assert math.isclose(result.trace_over_lambda_max_effective_rank, 3.0, abs_tol=1e-12)
    assert math.isclose(result.absolute_gap, 0.0, abs_tol=1e-12)
    assert result.confirmatory_use_allowed is False
    assert result.dsr_adjustment_applied is False


def test_concentrated_spectrum_exposes_definition_sensitivity() -> None:
    evidence = _evidence(
        [
            [1.0, 1.0, -1.0, -1.0, 0.5],
            [1.0, 1.0, -1.0, -1.0, 0.5],
            [1.0, -1.0, 1.0, -1.0, -0.5],
        ]
    )
    readiness = evaluate_keff_readiness(evidence)
    assert readiness.status == RESEARCH_ONLY

    result = evaluate_keff_spectral_sensitivity(readiness)
    assert 1.0 <= result.trace_over_lambda_max_effective_rank <= 3.0
    assert 1.0 <= result.entropy_effective_rank <= 3.0
    assert result.absolute_gap > 0.0
    assert result.relative_gap_to_entropy > 0.0
    assert result.readiness_status == RESEARCH_ONLY


def test_sample_limited_status_is_preserved() -> None:
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

    result = evaluate_keff_spectral_sensitivity(readiness)
    assert result.readiness_status == RESEARCH_ONLY
    assert result.to_payload()["research_only"] is True
    assert result.to_payload()["dsr_adjustment_applied"] is False


def test_blocked_evidence_cannot_produce_sensitivity_view() -> None:
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
        evaluate_keff_spectral_sensitivity(readiness)


def test_sensitivity_hash_is_deterministic() -> None:
    evidence = _evidence(
        [
            [1.0, 1.0, -1.0, -1.0],
            [1.0, -1.0, 1.0, -1.0],
            [1.0, -1.0, -1.0, 1.0],
        ]
    )
    readiness = evaluate_keff_readiness(evidence)
    first = evaluate_keff_spectral_sensitivity(readiness)
    second = evaluate_keff_spectral_sensitivity(readiness)
    assert first.sensitivity_sha256 == second.sensitivity_sha256
    assert first.entropy_estimator_sha256 == second.entropy_estimator_sha256
