from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math

import numpy as np

from daxlab.research.pbo_evidence_adapter import PBOEvidenceMatrix

READY = "READY_FOR_EXPERIMENTAL_KEFF"
RESEARCH_ONLY = "SAMPLE_OR_RANK_LIMITED_RESEARCH_ONLY"
BLOCKED = "BLOCKED_KEFF_EVIDENCE_INVALID"


@dataclass(frozen=True)
class KEffReadinessResult:
    status: str
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    n_trials: int
    n_periods: int
    sample_ratio_periods_per_trial: float
    matrix_rank: int
    max_identifiable_rank: int
    correlation_nullity: int
    near_zero_eigenvalue_count: int
    near_zero_eigenvalue_fraction: float
    eigenvalue_tolerance: float
    eigenvalues_desc: tuple[float, ...]
    matrix_sha256: str
    upstream_evidence_sha256: str
    diagnostic_sha256: str
    keff_computed: bool = False

    @property
    def ready_for_experimental_keff(self) -> bool:
        return self.status == READY

    def to_payload(self) -> dict[str, object]:
        return {
            "schema_version": "DAXLAB_KEFF_READINESS_V1",
            "status": self.status,
            "ready_for_experimental_keff": self.ready_for_experimental_keff,
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
            "n_trials": self.n_trials,
            "n_periods": self.n_periods,
            "sample_ratio_periods_per_trial": self.sample_ratio_periods_per_trial,
            "matrix_rank": self.matrix_rank,
            "max_identifiable_rank": self.max_identifiable_rank,
            "correlation_nullity": self.correlation_nullity,
            "near_zero_eigenvalue_count": self.near_zero_eigenvalue_count,
            "near_zero_eigenvalue_fraction": self.near_zero_eigenvalue_fraction,
            "eigenvalue_tolerance": self.eigenvalue_tolerance,
            "eigenvalues_desc": list(self.eigenvalues_desc),
            "matrix_sha256": self.matrix_sha256,
            "upstream_evidence_sha256": self.upstream_evidence_sha256,
            "diagnostic_sha256": self.diagnostic_sha256,
            "keff_computed": self.keff_computed,
            "dsr_adjustment_applied": False,
            "research_only": self.status != READY,
        }


def evaluate_keff_readiness(evidence: PBOEvidenceMatrix) -> KEffReadinessResult:
    """Diagnose whether a trial×period matrix can support experimental K_eff research.

    This function intentionally does not estimate K_eff. It reuses the existing,
    hash-bound PBO evidence matrix so PBO and any future K_eff work share identical
    trial/period ordering and upstream evidence identity.
    """
    matrix = np.asarray(evidence.matrix, dtype=float)
    blockers: set[str] = set()
    warnings: set[str] = set()

    if matrix.ndim != 2:
        blockers.add("MATRIX_MUST_BE_2D")
        n_trials = 0
        n_periods = 0
    else:
        n_trials, n_periods = map(int, matrix.shape)

    if matrix.ndim == 2:
        if n_trials < 2:
            blockers.add("AT_LEAST_TWO_TRIALS_REQUIRED")
        if n_periods < 3:
            blockers.add("AT_LEAST_THREE_PERIODS_REQUIRED")
        if not np.isfinite(matrix).all():
            blockers.add("NON_FINITE_MATRIX_VALUES")

    sample_ratio = float(n_periods / n_trials) if n_trials > 0 else math.nan
    max_identifiable_rank = min(n_trials, max(0, n_periods - 1))

    matrix_rank = 0
    nullity = n_trials if n_trials > 0 else 0
    eigenvalues = np.asarray([], dtype=float)
    eigen_tol = 0.0
    near_zero_count = 0

    if not blockers:
        centered = matrix - matrix.mean(axis=1, keepdims=True)
        row_std = matrix.std(axis=1, ddof=1)
        if np.any(~np.isfinite(row_std)) or np.any(row_std <= 0.0):
            blockers.add("CONSTANT_OR_INVALID_TRIAL_SERIES")
        else:
            standardized = centered / row_std[:, None]
            matrix_rank = int(np.linalg.matrix_rank(standardized))
            corr = np.corrcoef(matrix)
            if corr.shape != (n_trials, n_trials) or not np.isfinite(corr).all():
                blockers.add("CORRELATION_MATRIX_INVALID")
            else:
                raw_eigenvalues = np.linalg.eigvalsh(corr)
                eigenvalues = np.sort(np.clip(raw_eigenvalues.real, 0.0, None))[::-1]
                largest = float(eigenvalues[0]) if eigenvalues.size else 0.0
                eigen_tol = float(
                    np.finfo(float).eps * max(n_trials, n_periods) * max(1.0, largest)
                )
                near_zero_count = int(np.sum(eigenvalues <= eigen_tol))
                nullity = max(0, n_trials - matrix_rank)

                if matrix_rank < 2:
                    blockers.add("CORRELATION_STRUCTURE_HAS_RANK_BELOW_TWO")
                if max_identifiable_rank < n_trials:
                    warnings.add("PERIOD_COUNT_LIMITS_CORRELATION_RANK")
                if matrix_rank < min(n_trials, max_identifiable_rank):
                    warnings.add("OBSERVED_RANK_BELOW_SAMPLE_LIMIT")
                if near_zero_count > 0:
                    warnings.add("NEAR_ZERO_CORRELATION_EIGENVALUES_PRESENT")

    if blockers:
        status = BLOCKED
    elif warnings:
        status = RESEARCH_ONLY
    else:
        status = READY

    ordered_blockers = tuple(sorted(blockers))
    ordered_warnings = tuple(sorted(warnings))
    eigen_tuple = tuple(float(value) for value in eigenvalues)
    near_zero_fraction = float(near_zero_count / n_trials) if n_trials > 0 else math.nan

    identity = {
        "schema_version": "DAXLAB_KEFF_READINESS_V1",
        "matrix_sha256": evidence.matrix_sha256,
        "upstream_evidence_sha256": evidence.upstream_evidence_sha256,
        "status": status,
        "blockers": list(ordered_blockers),
        "warnings": list(ordered_warnings),
        "n_trials": n_trials,
        "n_periods": n_periods,
        "sample_ratio_periods_per_trial": sample_ratio,
        "matrix_rank": matrix_rank,
        "max_identifiable_rank": max_identifiable_rank,
        "correlation_nullity": nullity,
        "near_zero_eigenvalue_count": near_zero_count,
        "near_zero_eigenvalue_fraction": near_zero_fraction,
        "eigenvalue_tolerance": eigen_tol,
        "eigenvalues_desc": list(eigen_tuple),
        "keff_computed": False,
    }
    diagnostic_sha256 = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    return KEffReadinessResult(
        status=status,
        blockers=ordered_blockers,
        warnings=ordered_warnings,
        n_trials=n_trials,
        n_periods=n_periods,
        sample_ratio_periods_per_trial=sample_ratio,
        matrix_rank=matrix_rank,
        max_identifiable_rank=max_identifiable_rank,
        correlation_nullity=nullity,
        near_zero_eigenvalue_count=near_zero_count,
        near_zero_eigenvalue_fraction=near_zero_fraction,
        eigenvalue_tolerance=eigen_tol,
        eigenvalues_desc=eigen_tuple,
        matrix_sha256=evidence.matrix_sha256,
        upstream_evidence_sha256=evidence.upstream_evidence_sha256,
        diagnostic_sha256=diagnostic_sha256,
    )
