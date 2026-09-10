from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math

from daxlab.research.experimental_keff import estimate_raw_correlation_effective_rank
from daxlab.research.keff_readiness import BLOCKED, KEffReadinessResult


@dataclass(frozen=True)
class KEffSpectralSensitivityResult:
    entropy_effective_rank: float
    trace_over_lambda_max_effective_rank: float
    absolute_gap: float
    relative_gap_to_entropy: float
    readiness_status: str
    warnings: tuple[str, ...]
    n_trials: int
    n_periods: int
    matrix_sha256: str
    readiness_diagnostic_sha256: str
    entropy_estimator_sha256: str
    sensitivity_sha256: str
    confirmatory_use_allowed: bool = False
    dsr_adjustment_applied: bool = False

    def to_payload(self) -> dict[str, object]:
        return {
            "schema_version": "DAXLAB_KEFF_SPECTRAL_SENSITIVITY_V1",
            "entropy_method": "RAW_CORRELATION_EIGENVALUE_ENTROPY_EFFECTIVE_RANK",
            "trace_method": "RAW_CORRELATION_TRACE_OVER_LAMBDA_MAX_EFFECTIVE_RANK",
            "entropy_effective_rank": self.entropy_effective_rank,
            "trace_over_lambda_max_effective_rank": self.trace_over_lambda_max_effective_rank,
            "absolute_gap": self.absolute_gap,
            "relative_gap_to_entropy": self.relative_gap_to_entropy,
            "readiness_status": self.readiness_status,
            "warnings": list(self.warnings),
            "n_trials": self.n_trials,
            "n_periods": self.n_periods,
            "matrix_sha256": self.matrix_sha256,
            "readiness_diagnostic_sha256": self.readiness_diagnostic_sha256,
            "entropy_estimator_sha256": self.entropy_estimator_sha256,
            "sensitivity_sha256": self.sensitivity_sha256,
            "confirmatory_use_allowed": self.confirmatory_use_allowed,
            "research_only": True,
            "dsr_adjustment_applied": self.dsr_adjustment_applied,
        }


def evaluate_keff_spectral_sensitivity(
    readiness: KEffReadinessResult,
) -> KEffSpectralSensitivityResult:
    """Compare two named effective-rank definitions on one raw correlation spectrum."""
    if readiness.status == BLOCKED:
        raise ValueError("K_eff evidence is BLOCKED; sensitivity view must not run")

    entropy_result = estimate_raw_correlation_effective_rank(readiness)
    if not readiness.eigenvalues_desc:
        raise ValueError("readiness eigenvalue spectrum is empty")
    lambda_max = float(readiness.eigenvalues_desc[0])
    if not math.isfinite(lambda_max) or lambda_max <= 0.0:
        raise ValueError("largest correlation eigenvalue must be finite and > 0")

    trace_rank = float(readiness.n_trials / lambda_max)
    trace_rank = min(max(trace_rank, 1.0), float(readiness.n_trials))
    entropy_rank = entropy_result.k_eff
    absolute_gap = abs(entropy_rank - trace_rank)
    relative_gap = absolute_gap / entropy_rank if entropy_rank > 0.0 else math.inf

    identity = {
        "schema_version": "DAXLAB_KEFF_SPECTRAL_SENSITIVITY_V1",
        "entropy_method": "RAW_CORRELATION_EIGENVALUE_ENTROPY_EFFECTIVE_RANK",
        "trace_method": "RAW_CORRELATION_TRACE_OVER_LAMBDA_MAX_EFFECTIVE_RANK",
        "entropy_effective_rank": entropy_rank,
        "trace_over_lambda_max_effective_rank": trace_rank,
        "absolute_gap": absolute_gap,
        "relative_gap_to_entropy": relative_gap,
        "readiness_status": readiness.status,
        "warnings": list(readiness.warnings),
        "n_trials": readiness.n_trials,
        "n_periods": readiness.n_periods,
        "matrix_sha256": readiness.matrix_sha256,
        "readiness_diagnostic_sha256": readiness.diagnostic_sha256,
        "entropy_estimator_sha256": entropy_result.estimator_sha256,
        "confirmatory_use_allowed": False,
        "dsr_adjustment_applied": False,
    }
    sensitivity_sha256 = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    return KEffSpectralSensitivityResult(
        entropy_effective_rank=entropy_rank,
        trace_over_lambda_max_effective_rank=trace_rank,
        absolute_gap=absolute_gap,
        relative_gap_to_entropy=relative_gap,
        readiness_status=readiness.status,
        warnings=readiness.warnings,
        n_trials=readiness.n_trials,
        n_periods=readiness.n_periods,
        matrix_sha256=readiness.matrix_sha256,
        readiness_diagnostic_sha256=readiness.diagnostic_sha256,
        entropy_estimator_sha256=entropy_result.estimator_sha256,
        sensitivity_sha256=sensitivity_sha256,
        confirmatory_use_allowed=False,
        dsr_adjustment_applied=False,
    )
