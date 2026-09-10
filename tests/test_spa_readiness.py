from __future__ import annotations

import numpy as np

from daxlab.research.pbo_evidence_adapter import PBOEvidenceMatrix
from daxlab.research.spa_readiness import BLOCKED, READY, evaluate_spa_readiness


def _evidence() -> PBOEvidenceMatrix:
    matrix = np.asarray(
        [
            [0.10, 0.20, -0.10, 0.30, 0.05, 0.15],
            [0.00, 0.10, 0.20, -0.10, 0.15, 0.05],
            [0.05, -0.05, 0.10, 0.20, 0.00, 0.10],
        ],
        dtype=float,
    )
    matrix.setflags(write=False)
    return PBOEvidenceMatrix(
        matrix=matrix,
        trial_order=("T0", "T1", "T2"),
        period_order=("P0", "P1", "P2", "P3", "P4", "P5"),
        upstream_evidence_sha256="a" * 64,
        matrix_sha256="b" * 64,
    )


def test_explicit_stationary_configuration_is_ready() -> None:
    result = evaluate_spa_readiness(
        _evidence(),
        benchmark_returns=[0.0] * 6,
        block_size=2,
        reps=1999,
        seed=17,
    )

    assert result.status == READY
    assert result.ready is True
    assert result.bootstrap == "stationary"
    assert result.block_size == 2
    assert result.reps == 1999
    assert result.seed == 17
    assert result.studentize is True
    assert result.nested is False
    assert result.loss_transform == "NEGATE_RETURNS_TO_LOSSES"
    assert result.pvalue_resolution_upper_bound == 1.0 / 2000.0
    assert result.spa_computed is False
    assert result.to_payload()["confirmatory_use_allowed"] is False


def test_benchmark_length_mismatch_blocks() -> None:
    result = evaluate_spa_readiness(
        _evidence(),
        benchmark_returns=[0.0] * 5,
        block_size=2,
        reps=1000,
        seed=1,
    )
    assert result.status == BLOCKED
    assert "BENCHMARK_LENGTH_MUST_MATCH_PERIOD_COUNT" in result.blockers


def test_spa_v1_rejects_non_stationary_bootstrap() -> None:
    result = evaluate_spa_readiness(
        _evidence(),
        benchmark_returns=[0.0] * 6,
        block_size=2,
        reps=1000,
        seed=1,
        bootstrap="circular",
    )
    assert result.status == BLOCKED
    assert "SPA_V1_REQUIRES_STATIONARY_BOOTSTRAP" in result.blockers


def test_invalid_reproducibility_parameters_block() -> None:
    result = evaluate_spa_readiness(
        _evidence(),
        benchmark_returns=[0.0] * 6,
        block_size=0,
        reps=0,
        seed=True,
    )
    assert result.status == BLOCKED
    assert "BLOCK_SIZE_MUST_BE_POSITIVE" in result.blockers
    assert "REPS_MUST_BE_POSITIVE" in result.blockers
    assert "SEED_MUST_BE_EXPLICIT_INTEGER" in result.blockers


def test_studentization_and_nested_contract_are_explicit() -> None:
    result = evaluate_spa_readiness(
        _evidence(),
        benchmark_returns=[0.0] * 6,
        block_size=2,
        reps=1000,
        seed=1,
        studentize=False,
        nested=True,
    )
    assert result.status == BLOCKED
    assert "SPA_V1_REQUIRES_STUDENTIZATION" in result.blockers
    assert "SPA_V1_NESTED_BOOTSTRAP_NOT_SUPPORTED" in result.blockers


def test_readiness_hash_changes_with_method_configuration() -> None:
    first = evaluate_spa_readiness(
        _evidence(),
        benchmark_returns=[0.0] * 6,
        block_size=2,
        reps=1000,
        seed=1,
    )
    second = evaluate_spa_readiness(
        _evidence(),
        benchmark_returns=[0.0] * 6,
        block_size=3,
        reps=1000,
        seed=1,
    )
    third = evaluate_spa_readiness(
        _evidence(),
        benchmark_returns=[0.01] * 6,
        block_size=2,
        reps=1000,
        seed=1,
    )
    assert first.readiness_sha256 != second.readiness_sha256
    assert first.readiness_sha256 != third.readiness_sha256
