from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Sequence

import numpy as np

from daxlab.research.pbo_evidence_adapter import PBOEvidenceMatrix

READY = "READY_FOR_EXPERIMENTAL_ARCH_SPA"
BLOCKED = "BLOCKED_SPA_EVIDENCE_INVALID"


@dataclass(frozen=True)
class SPAReadinessResult:
    status: str
    blockers: tuple[str, ...]
    n_periods: int
    n_models: int
    bootstrap: str
    block_size: int
    reps: int
    seed: int
    studentize: bool
    nested: bool
    pvalue_resolution_upper_bound: float
    loss_transform: str
    benchmark_returns: tuple[float, ...]
    matrix_sha256: str
    upstream_evidence_sha256: str
    readiness_sha256: str
    spa_computed: bool = False

    @property
    def ready(self) -> bool:
        return self.status == READY

    def to_payload(self) -> dict[str, object]:
        return {
            "schema_version": "DAXLAB_SPA_READINESS_V1",
            "status": self.status,
            "ready": self.ready,
            "blockers": list(self.blockers),
            "n_periods": self.n_periods,
            "n_models": self.n_models,
            "bootstrap": self.bootstrap,
            "block_size": self.block_size,
            "reps": self.reps,
            "seed": self.seed,
            "studentize": self.studentize,
            "nested": self.nested,
            "pvalue_resolution_upper_bound": self.pvalue_resolution_upper_bound,
            "loss_transform": self.loss_transform,
            "benchmark_returns": list(self.benchmark_returns),
            "matrix_sha256": self.matrix_sha256,
            "upstream_evidence_sha256": self.upstream_evidence_sha256,
            "readiness_sha256": self.readiness_sha256,
            "spa_computed": self.spa_computed,
            "confirmatory_use_allowed": False,
        }


def evaluate_spa_readiness(
    evidence: PBOEvidenceMatrix,
    *,
    benchmark_returns: Sequence[float],
    block_size: int,
    reps: int,
    seed: int,
    bootstrap: str = "stationary",
    studentize: bool = True,
    nested: bool = False,
) -> SPAReadinessResult:
    """Validate an explicit evidence/configuration contract before arch.bootstrap.SPA.

    DAXLAB uses returns upstream and will later transform both benchmark and model
    returns to losses using ``loss = -return``. This gate computes no SPA statistic.
    """
    matrix = np.asarray(evidence.matrix, dtype=float)
    blockers: set[str] = set()
    benchmark = tuple(float(value) for value in benchmark_returns)
    bootstrap_name = bootstrap.strip().lower().replace(" ", "_")

    if matrix.ndim != 2:
        blockers.add("MODEL_RETURN_MATRIX_MUST_BE_2D")
        n_models = 0
        n_periods = 0
    else:
        n_models, n_periods = map(int, matrix.shape)
        if n_models < 1:
            blockers.add("AT_LEAST_ONE_MODEL_REQUIRED")
        if n_periods < 3:
            blockers.add("AT_LEAST_THREE_PERIODS_REQUIRED")
        if not np.isfinite(matrix).all():
            blockers.add("NON_FINITE_MODEL_RETURNS")

    if len(benchmark) != n_periods:
        blockers.add("BENCHMARK_LENGTH_MUST_MATCH_PERIOD_COUNT")
    if benchmark and not all(math.isfinite(value) for value in benchmark):
        blockers.add("NON_FINITE_BENCHMARK_RETURNS")

    if bootstrap_name not in {"stationary", "sb"}:
        blockers.add("SPA_V1_REQUIRES_STATIONARY_BOOTSTRAP")
    if isinstance(block_size, bool) or not isinstance(block_size, int):
        blockers.add("BLOCK_SIZE_MUST_BE_INTEGER")
    elif block_size < 1:
        blockers.add("BLOCK_SIZE_MUST_BE_POSITIVE")
    elif n_periods > 0 and block_size > n_periods:
        blockers.add("BLOCK_SIZE_EXCEEDS_PERIOD_COUNT")

    if isinstance(reps, bool) or not isinstance(reps, int):
        blockers.add("REPS_MUST_BE_INTEGER")
    elif reps < 1:
        blockers.add("REPS_MUST_BE_POSITIVE")

    if isinstance(seed, bool) or not isinstance(seed, int):
        blockers.add("SEED_MUST_BE_EXPLICIT_INTEGER")
    if studentize is not True:
        blockers.add("SPA_V1_REQUIRES_STUDENTIZATION")
    if nested is not False:
        blockers.add("SPA_V1_NESTED_BOOTSTRAP_NOT_SUPPORTED")

    canonical_bootstrap = "stationary"
    ordered_blockers = tuple(sorted(blockers))
    status = READY if not ordered_blockers else BLOCKED
    resolution = float(1.0 / (reps + 1)) if isinstance(reps, int) and not isinstance(reps, bool) and reps >= 1 else math.nan

    identity = {
        "schema_version": "DAXLAB_SPA_READINESS_V1",
        "status": status,
        "blockers": list(ordered_blockers),
        "n_periods": n_periods,
        "n_models": n_models,
        "bootstrap": canonical_bootstrap,
        "block_size": block_size,
        "reps": reps,
        "seed": seed,
        "studentize": studentize,
        "nested": nested,
        "pvalue_resolution_upper_bound": resolution,
        "loss_transform": "NEGATE_RETURNS_TO_LOSSES",
        "benchmark_returns": list(benchmark),
        "matrix_sha256": evidence.matrix_sha256,
        "upstream_evidence_sha256": evidence.upstream_evidence_sha256,
        "spa_computed": False,
        "confirmatory_use_allowed": False,
    }
    readiness_sha256 = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    return SPAReadinessResult(
        status=status,
        blockers=ordered_blockers,
        n_periods=n_periods,
        n_models=n_models,
        bootstrap=canonical_bootstrap,
        block_size=block_size if isinstance(block_size, int) and not isinstance(block_size, bool) else 0,
        reps=reps if isinstance(reps, int) and not isinstance(reps, bool) else 0,
        seed=seed if isinstance(seed, int) and not isinstance(seed, bool) else 0,
        studentize=bool(studentize),
        nested=bool(nested),
        pvalue_resolution_upper_bound=resolution,
        loss_transform="NEGATE_RETURNS_TO_LOSSES",
        benchmark_returns=benchmark,
        matrix_sha256=evidence.matrix_sha256,
        upstream_evidence_sha256=evidence.upstream_evidence_sha256,
        readiness_sha256=readiness_sha256,
        spa_computed=False,
    )
