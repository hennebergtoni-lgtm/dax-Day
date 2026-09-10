from __future__ import annotations

from dataclasses import dataclass
import hashlib
from importlib.metadata import version
import json
import math

import numpy as np

from daxlab.research.pbo_evidence_adapter import PBOEvidenceMatrix
from daxlab.research.spa_readiness import READY, SPAReadinessResult


@dataclass(frozen=True)
class ExperimentalArchSPAResult:
    pvalue_lower: float
    pvalue_consistent: float
    pvalue_upper: float
    arch_version: str
    bootstrap: str
    block_size: int
    reps: int
    seed: int
    studentize: bool
    nested: bool
    n_periods: int
    n_models: int
    loss_transform: str
    matrix_sha256: str
    upstream_evidence_sha256: str
    readiness_sha256: str
    result_sha256: str
    confirmatory_use_allowed: bool = False

    def to_payload(self) -> dict[str, object]:
        return {
            "schema_version": "DAXLAB_EXPERIMENTAL_ARCH_SPA_V1",
            "engine": "arch.bootstrap.SPA",
            "arch_version": self.arch_version,
            "pvalues": {
                "lower": self.pvalue_lower,
                "consistent": self.pvalue_consistent,
                "upper": self.pvalue_upper,
            },
            "bootstrap": self.bootstrap,
            "block_size": self.block_size,
            "reps": self.reps,
            "seed": self.seed,
            "studentize": self.studentize,
            "nested": self.nested,
            "n_periods": self.n_periods,
            "n_models": self.n_models,
            "loss_transform": self.loss_transform,
            "matrix_sha256": self.matrix_sha256,
            "upstream_evidence_sha256": self.upstream_evidence_sha256,
            "readiness_sha256": self.readiness_sha256,
            "result_sha256": self.result_sha256,
            "confirmatory_use_allowed": self.confirmatory_use_allowed,
            "research_only": True,
            "binary_gate_applied": False,
        }


def _to_arch_losses(
    evidence: PBOEvidenceMatrix,
    readiness: SPAReadinessResult,
) -> tuple[np.ndarray, np.ndarray]:
    model_returns = np.asarray(evidence.matrix, dtype=float)
    benchmark_returns = np.asarray(readiness.benchmark_returns, dtype=float)
    benchmark_losses = -benchmark_returns
    model_losses = -model_returns.T
    return benchmark_losses, model_losses


def run_experimental_arch_spa(
    evidence: PBOEvidenceMatrix,
    readiness: SPAReadinessResult,
) -> ExperimentalArchSPAResult:
    """Run the official arch.bootstrap.SPA engine on prevalidated DAXLAB evidence."""
    if readiness.status != READY:
        raise ValueError("SPA readiness must be READY before execution")
    if readiness.matrix_sha256 != evidence.matrix_sha256:
        raise ValueError("SPA readiness matrix hash does not match evidence")
    if readiness.upstream_evidence_sha256 != evidence.upstream_evidence_sha256:
        raise ValueError("SPA readiness upstream evidence hash does not match evidence")
    if readiness.n_models != evidence.matrix.shape[0]:
        raise ValueError("SPA readiness model count does not match evidence")
    if readiness.n_periods != evidence.matrix.shape[1]:
        raise ValueError("SPA readiness period count does not match evidence")

    try:
        from arch.bootstrap import SPA
    except ImportError as exc:  # pragma: no cover - exercised by install contract, not CI runtime
        raise RuntimeError("Install the project with the 'statistics' extra to run SPA") from exc

    benchmark_losses, model_losses = _to_arch_losses(evidence, readiness)
    spa = SPA(
        benchmark_losses,
        model_losses,
        block_size=readiness.block_size,
        reps=readiness.reps,
        bootstrap=readiness.bootstrap,
        studentize=readiness.studentize,
        nested=readiness.nested,
        seed=readiness.seed,
    )
    spa.compute()
    pvalues = spa.pvalues
    expected_keys = {"lower", "consistent", "upper"}
    if set(map(str, pvalues.index)) != expected_keys:
        raise RuntimeError("arch SPA returned an unexpected p-value schema")

    lower = float(pvalues["lower"])
    consistent = float(pvalues["consistent"])
    upper = float(pvalues["upper"])
    if not all(math.isfinite(value) and 0.0 <= value <= 1.0 for value in (lower, consistent, upper)):
        raise RuntimeError("arch SPA returned invalid p-values")

    arch_version = version("arch")
    identity = {
        "schema_version": "DAXLAB_EXPERIMENTAL_ARCH_SPA_V1",
        "engine": "arch.bootstrap.SPA",
        "arch_version": arch_version,
        "pvalues": {"lower": lower, "consistent": consistent, "upper": upper},
        "bootstrap": readiness.bootstrap,
        "block_size": readiness.block_size,
        "reps": readiness.reps,
        "seed": readiness.seed,
        "studentize": readiness.studentize,
        "nested": readiness.nested,
        "n_periods": readiness.n_periods,
        "n_models": readiness.n_models,
        "loss_transform": readiness.loss_transform,
        "matrix_sha256": evidence.matrix_sha256,
        "upstream_evidence_sha256": evidence.upstream_evidence_sha256,
        "readiness_sha256": readiness.readiness_sha256,
        "confirmatory_use_allowed": False,
        "binary_gate_applied": False,
    }
    result_sha256 = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    return ExperimentalArchSPAResult(
        pvalue_lower=lower,
        pvalue_consistent=consistent,
        pvalue_upper=upper,
        arch_version=arch_version,
        bootstrap=readiness.bootstrap,
        block_size=readiness.block_size,
        reps=readiness.reps,
        seed=readiness.seed,
        studentize=readiness.studentize,
        nested=readiness.nested,
        n_periods=readiness.n_periods,
        n_models=readiness.n_models,
        loss_transform=readiness.loss_transform,
        matrix_sha256=evidence.matrix_sha256,
        upstream_evidence_sha256=evidence.upstream_evidence_sha256,
        readiness_sha256=readiness.readiness_sha256,
        result_sha256=result_sha256,
        confirmatory_use_allowed=False,
    )
