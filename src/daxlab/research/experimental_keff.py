from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math

import numpy as np

from daxlab.research.keff_readiness import (
    BLOCKED,
    READY,
    KEffReadinessResult,
)


@dataclass(frozen=True)
class ExperimentalKEffResult:
    k_eff: float
    method: str
    readiness_status: str
    warnings: tuple[str, ...]
    n_trials: int
    n_periods: int
    matrix_sha256: str
    upstream_evidence_sha256: str
    readiness_diagnostic_sha256: str
    estimator_sha256: str
    confirmatory_use_allowed: bool = False
    dsr_adjustment_applied: bool = False

    @property
    def research_only(self) -> bool:
        return not self.confirmatory_use_allowed

    def to_payload(self) -> dict[str, object]:
        return {
            "schema_version": "DAXLAB_EXPERIMENTAL_KEFF_V1",
            "method": self.method,
            "k_eff": self.k_eff,
            "readiness_status": self.readiness_status,
            "warnings": list(self.warnings),
            "n_trials": self.n_trials,
            "n_periods": self.n_periods,
            "matrix_sha256": self.matrix_sha256,
            "upstream_evidence_sha256": self.upstream_evidence_sha256,
            "readiness_diagnostic_sha256": self.readiness_diagnostic_sha256,
            "estimator_sha256": self.estimator_sha256,
            "confirmatory_use_allowed": self.confirmatory_use_allowed,
            "research_only": self.research_only,
            "dsr_adjustment_applied": self.dsr_adjustment_applied,
            "shrinkage_applied": False,
            "clustering_applied": False,
            "marchenko_pastur_applied": False,
        }


def estimate_raw_correlation_effective_rank(
    readiness: KEffReadinessResult,
) -> ExperimentalKEffResult:
    """Estimate entropy effective rank from the raw-correlation eigenvalue spectrum.

    This is deliberately a RESEARCH estimator. It cannot be used to alter DSR V1
    and never upgrades sample-limited evidence to confirmatory status.
    """
    if readiness.status == BLOCKED:
        raise ValueError("K_eff evidence is BLOCKED; estimator must not run")
    eigenvalues = np.asarray(readiness.eigenvalues_desc, dtype=float)
    if eigenvalues.ndim != 1 or eigenvalues.size != readiness.n_trials:
        raise ValueError("readiness eigenvalue spectrum is inconsistent")
    if not np.isfinite(eigenvalues).all() or np.any(eigenvalues < 0.0):
        raise ValueError("readiness eigenvalue spectrum is invalid")

    positive = eigenvalues[eigenvalues > readiness.eigenvalue_tolerance]
    if positive.size == 0:
        raise ValueError("no positive correlation eigenvalues above numerical tolerance")
    total = float(positive.sum())
    if not math.isfinite(total) or total <= 0.0:
        raise ValueError("positive eigenvalue mass is invalid")
    weights = positive / total
    entropy = float(-np.sum(weights * np.log(weights)))
    k_eff = float(math.exp(entropy))
    if not math.isfinite(k_eff) or not 1.0 <= k_eff <= readiness.n_trials + 1e-12:
        raise ValueError("computed effective rank is outside valid bounds")
    k_eff = min(k_eff, float(readiness.n_trials))

    method = "RAW_CORRELATION_EIGENVALUE_ENTROPY_EFFECTIVE_RANK"
    identity = {
        "schema_version": "DAXLAB_EXPERIMENTAL_KEFF_V1",
        "method": method,
        "k_eff": k_eff,
        "readiness_status": readiness.status,
        "warnings": list(readiness.warnings),
        "n_trials": readiness.n_trials,
        "n_periods": readiness.n_periods,
        "matrix_sha256": readiness.matrix_sha256,
        "upstream_evidence_sha256": readiness.upstream_evidence_sha256,
        "readiness_diagnostic_sha256": readiness.diagnostic_sha256,
        "confirmatory_use_allowed": False,
        "dsr_adjustment_applied": False,
        "shrinkage_applied": False,
        "clustering_applied": False,
        "marchenko_pastur_applied": False,
    }
    estimator_sha256 = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    return ExperimentalKEffResult(
        k_eff=k_eff,
        method=method,
        readiness_status=readiness.status,
        warnings=readiness.warnings,
        n_trials=readiness.n_trials,
        n_periods=readiness.n_periods,
        matrix_sha256=readiness.matrix_sha256,
        upstream_evidence_sha256=readiness.upstream_evidence_sha256,
        readiness_diagnostic_sha256=readiness.diagnostic_sha256,
        estimator_sha256=estimator_sha256,
        confirmatory_use_allowed=False,
        dsr_adjustment_applied=False,
    )
