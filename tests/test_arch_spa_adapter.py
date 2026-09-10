from __future__ import annotations

from dataclasses import replace
import math

import numpy as np
import pytest

from daxlab.research.arch_spa_adapter import _to_arch_losses, run_experimental_arch_spa
from daxlab.research.pbo_evidence_adapter import PBOEvidenceMatrix
from daxlab.research.spa_readiness import evaluate_spa_readiness


def _evidence() -> PBOEvidenceMatrix:
    matrix = np.asarray(
        [
            [0.02, 0.01, 0.03, -0.01, 0.04, 0.02, 0.01, 0.03],
            [0.00, 0.01, -0.01, 0.02, 0.00, 0.01, -0.02, 0.01],
            [-0.01, 0.00, 0.01, -0.02, 0.01, 0.00, -0.01, 0.00],
        ],
        dtype=float,
    )
    matrix.setflags(write=False)
    return PBOEvidenceMatrix(
        matrix=matrix,
        trial_order=("T0", "T1", "T2"),
        period_order=tuple(f"P{i}" for i in range(8)),
        upstream_evidence_sha256="a" * 64,
        matrix_sha256="b" * 64,
    )


def _readiness(evidence: PBOEvidenceMatrix):
    return evaluate_spa_readiness(
        evidence,
        benchmark_returns=[0.0] * 8,
        block_size=2,
        reps=199,
        seed=23,
    )


def test_return_to_loss_transform_has_arch_orientation() -> None:
    evidence = _evidence()
    readiness = _readiness(evidence)
    benchmark_losses, model_losses = _to_arch_losses(evidence, readiness)

    assert benchmark_losses.shape == (8,)
    assert model_losses.shape == (8, 3)
    np.testing.assert_allclose(benchmark_losses, np.zeros(8))
    np.testing.assert_allclose(model_losses, -np.asarray(evidence.matrix).T)


def test_real_arch_spa_returns_all_three_valid_pvalues() -> None:
    evidence = _evidence()
    result = run_experimental_arch_spa(evidence, _readiness(evidence))

    for value in (result.pvalue_lower, result.pvalue_consistent, result.pvalue_upper):
        assert math.isfinite(value)
        assert 0.0 <= value <= 1.0
    assert result.pvalue_lower <= result.pvalue_consistent <= result.pvalue_upper
    assert result.arch_version.startswith("8.")
    payload = result.to_payload()
    assert set(payload["pvalues"]) == {"lower", "consistent", "upper"}
    assert payload["binary_gate_applied"] is False
    assert payload["confirmatory_use_allowed"] is False


def test_real_arch_spa_is_reproducible_for_same_seed() -> None:
    evidence = _evidence()
    readiness = _readiness(evidence)
    first = run_experimental_arch_spa(evidence, readiness)
    second = run_experimental_arch_spa(evidence, readiness)

    assert first.pvalue_lower == second.pvalue_lower
    assert first.pvalue_consistent == second.pvalue_consistent
    assert first.pvalue_upper == second.pvalue_upper
    assert first.result_sha256 == second.result_sha256


def test_matrix_hash_mismatch_blocks_before_arch_execution() -> None:
    evidence = _evidence()
    readiness = replace(_readiness(evidence), matrix_sha256="c" * 64)

    with pytest.raises(ValueError, match="matrix hash"):
        run_experimental_arch_spa(evidence, readiness)


def test_non_ready_contract_blocks_before_arch_execution() -> None:
    evidence = _evidence()
    readiness = evaluate_spa_readiness(
        evidence,
        benchmark_returns=[0.0] * 8,
        block_size=0,
        reps=199,
        seed=23,
    )

    with pytest.raises(ValueError, match="readiness must be READY"):
        run_experimental_arch_spa(evidence, readiness)
