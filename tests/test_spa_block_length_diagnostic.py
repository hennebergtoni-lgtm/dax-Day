from __future__ import annotations

import math

import numpy as np
import pytest

from daxlab.research.pbo_evidence_adapter import PBOEvidenceMatrix
from daxlab.research.spa_block_length_diagnostic import diagnose_spa_stationary_block_lengths


def _evidence() -> PBOEvidenceMatrix:
    matrix = np.asarray(
        [
            [0.02, 0.01, 0.03, -0.01, 0.04, 0.02, 0.01, 0.03, 0.02, 0.00, 0.01, 0.02],
            [0.00, 0.01, -0.01, 0.02, 0.00, 0.01, -0.02, 0.01, 0.00, 0.01, 0.00, -0.01],
            [-0.01, 0.00, 0.01, -0.02, 0.01, 0.00, -0.01, 0.00, 0.01, -0.01, 0.00, 0.01],
        ],
        dtype=float,
    )
    matrix.setflags(write=False)
    return PBOEvidenceMatrix(
        matrix=matrix,
        trial_order=("T0", "T1", "T2"),
        period_order=tuple(f"P{i}" for i in range(12)),
        upstream_evidence_sha256="a" * 64,
        matrix_sha256="b" * 64,
    )


def test_diagnostic_matches_arch_per_model_stationary_estimates() -> None:
    from arch.bootstrap import optimal_block_length

    evidence = _evidence()
    benchmark = np.asarray([0.0] * 12)
    expected = optimal_block_length(np.asarray(evidence.matrix).T - benchmark[:, None])

    result = diagnose_spa_stationary_block_lengths(evidence, benchmark_returns=benchmark)

    np.testing.assert_allclose(
        result.model_stationary_block_lengths,
        np.asarray(expected["stationary"], dtype=float),
    )
    assert result.model_executable_block_candidates == tuple(
        max(1, math.ceil(float(value))) for value in expected["stationary"]
    )
    assert result.selected_block_size is None
    assert result.to_payload()["automatic_selection_applied"] is False
    assert result.to_payload()["confirmatory_use_allowed"] is False


def test_diagnostic_is_deterministic_and_hash_bound() -> None:
    evidence = _evidence()
    first = diagnose_spa_stationary_block_lengths(evidence, benchmark_returns=[0.0] * 12)
    second = diagnose_spa_stationary_block_lengths(evidence, benchmark_returns=[0.0] * 12)

    assert first == second
    assert len(first.diagnostic_sha256) == 64
    assert first.matrix_sha256 == evidence.matrix_sha256
    assert first.upstream_evidence_sha256 == evidence.upstream_evidence_sha256


def test_benchmark_change_changes_diagnostic_identity() -> None:
    evidence = _evidence()
    first = diagnose_spa_stationary_block_lengths(evidence, benchmark_returns=[0.0] * 12)
    second = diagnose_spa_stationary_block_lengths(
        evidence, benchmark_returns=[0.001] + [0.0] * 11
    )

    assert first.diagnostic_sha256 != second.diagnostic_sha256


def test_invalid_benchmark_length_is_rejected() -> None:
    with pytest.raises(ValueError, match="benchmark return length"):
        diagnose_spa_stationary_block_lengths(_evidence(), benchmark_returns=[0.0] * 11)


def test_non_finite_inputs_are_rejected() -> None:
    benchmark = [0.0] * 12
    benchmark[4] = float("nan")
    with pytest.raises(ValueError, match="finite"):
        diagnose_spa_stationary_block_lengths(_evidence(), benchmark_returns=benchmark)
