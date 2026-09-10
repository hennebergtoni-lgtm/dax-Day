from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math

import numpy as np

from daxlab.research.keff_readiness import BLOCKED, evaluate_keff_readiness
from daxlab.research.keff_spectral_sensitivity import evaluate_keff_spectral_sensitivity
from daxlab.research.pbo_evidence_adapter import PBOEvidenceMatrix


@dataclass(frozen=True)
class KEffLOOObservation:
    omitted_period_id: str
    entropy_effective_rank: float
    trace_over_lambda_max_effective_rank: float
    reduced_matrix_rank: int
    reduced_n_periods: int
    child_sha256: str

    def to_payload(self) -> dict[str, object]:
        return {
            "omitted_period_id": self.omitted_period_id,
            "entropy_effective_rank": self.entropy_effective_rank,
            "trace_over_lambda_max_effective_rank": self.trace_over_lambda_max_effective_rank,
            "reduced_matrix_rank": self.reduced_matrix_rank,
            "reduced_n_periods": self.reduced_n_periods,
            "child_sha256": self.child_sha256,
        }


@dataclass(frozen=True)
class KEffLOOStabilityResult:
    parent_entropy_effective_rank: float
    parent_trace_over_lambda_max_effective_rank: float
    observations: tuple[KEffLOOObservation, ...]
    entropy_min: float
    entropy_median: float
    entropy_max: float
    entropy_max_abs_deviation_from_parent: float
    trace_min: float
    trace_median: float
    trace_max: float
    trace_max_abs_deviation_from_parent: float
    parent_matrix_sha256: str
    upstream_evidence_sha256: str
    stability_sha256: str
    confirmatory_use_allowed: bool = False
    dsr_adjustment_applied: bool = False

    def to_payload(self) -> dict[str, object]:
        return {
            "schema_version": "DAXLAB_KEFF_LOO_STABILITY_V1",
            "method": "LEAVE_ONE_PERIOD_OUT_SPECTRAL_SENSITIVITY",
            "parent_entropy_effective_rank": self.parent_entropy_effective_rank,
            "parent_trace_over_lambda_max_effective_rank": (
                self.parent_trace_over_lambda_max_effective_rank
            ),
            "observations": [item.to_payload() for item in self.observations],
            "entropy_min": self.entropy_min,
            "entropy_median": self.entropy_median,
            "entropy_max": self.entropy_max,
            "entropy_max_abs_deviation_from_parent": self.entropy_max_abs_deviation_from_parent,
            "trace_min": self.trace_min,
            "trace_median": self.trace_median,
            "trace_max": self.trace_max,
            "trace_max_abs_deviation_from_parent": self.trace_max_abs_deviation_from_parent,
            "parent_matrix_sha256": self.parent_matrix_sha256,
            "upstream_evidence_sha256": self.upstream_evidence_sha256,
            "stability_sha256": self.stability_sha256,
            "confirmatory_use_allowed": self.confirmatory_use_allowed,
            "research_only": True,
            "dsr_adjustment_applied": self.dsr_adjustment_applied,
            "confidence_interval_claimed": False,
        }


def _child_matrix_identity(
    parent: PBOEvidenceMatrix,
    omitted_period_id: str,
    reduced_period_order: tuple[str, ...],
    reduced_matrix: np.ndarray,
) -> str:
    identity = {
        "schema_version": "DAXLAB_KEFF_LOO_CHILD_V1",
        "parent_matrix_sha256": parent.matrix_sha256,
        "upstream_evidence_sha256": parent.upstream_evidence_sha256,
        "omitted_period_id": omitted_period_id,
        "trial_order": list(parent.trial_order),
        "reduced_period_order": list(reduced_period_order),
        "matrix": reduced_matrix.tolist(),
    }
    return hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def evaluate_keff_loo_stability(evidence: PBOEvidenceMatrix) -> KEffLOOStabilityResult:
    """Measure deterministic leave-one-period-out sensitivity of two effective-rank views.

    This is a sensitivity diagnostic, not a confidence interval and not a confirmatory
    K_eff estimator. Child identities are explicitly derived from the parent matrix and
    omitted period; they are not represented as new confirmatory evidence.
    """
    parent_readiness = evaluate_keff_readiness(evidence)
    if parent_readiness.status == BLOCKED:
        raise ValueError("parent K_eff evidence is BLOCKED")
    if evidence.matrix.shape[1] < 4:
        raise ValueError("at least 4 periods are required for leave-one-period-out stability")

    parent_sensitivity = evaluate_keff_spectral_sensitivity(parent_readiness)
    observations: list[KEffLOOObservation] = []

    for period_index, omitted_period_id in enumerate(evidence.period_order):
        reduced_matrix = np.delete(np.asarray(evidence.matrix, dtype=float), period_index, axis=1)
        reduced_period_order = tuple(
            period_id for idx, period_id in enumerate(evidence.period_order) if idx != period_index
        )
        child_sha256 = _child_matrix_identity(
            evidence,
            omitted_period_id,
            reduced_period_order,
            reduced_matrix,
        )
        reduced_matrix.setflags(write=False)
        child = PBOEvidenceMatrix(
            matrix=reduced_matrix,
            trial_order=evidence.trial_order,
            period_order=reduced_period_order,
            upstream_evidence_sha256=evidence.upstream_evidence_sha256,
            matrix_sha256=child_sha256,
        )
        readiness = evaluate_keff_readiness(child)
        if readiness.status == BLOCKED:
            raise ValueError(
                f"leave-one-period-out child became BLOCKED for period {omitted_period_id}"
            )
        sensitivity = evaluate_keff_spectral_sensitivity(readiness)
        observations.append(
            KEffLOOObservation(
                omitted_period_id=omitted_period_id,
                entropy_effective_rank=sensitivity.entropy_effective_rank,
                trace_over_lambda_max_effective_rank=(
                    sensitivity.trace_over_lambda_max_effective_rank
                ),
                reduced_matrix_rank=readiness.matrix_rank,
                reduced_n_periods=readiness.n_periods,
                child_sha256=child_sha256,
            )
        )

    entropy_values = np.asarray([item.entropy_effective_rank for item in observations], dtype=float)
    trace_values = np.asarray(
        [item.trace_over_lambda_max_effective_rank for item in observations], dtype=float
    )
    parent_entropy = parent_sensitivity.entropy_effective_rank
    parent_trace = parent_sensitivity.trace_over_lambda_max_effective_rank

    entropy_min = float(np.min(entropy_values))
    entropy_median = float(np.median(entropy_values))
    entropy_max = float(np.max(entropy_values))
    entropy_max_dev = float(np.max(np.abs(entropy_values - parent_entropy)))
    trace_min = float(np.min(trace_values))
    trace_median = float(np.median(trace_values))
    trace_max = float(np.max(trace_values))
    trace_max_dev = float(np.max(np.abs(trace_values - parent_trace)))

    if not all(
        math.isfinite(value)
        for value in (
            entropy_min,
            entropy_median,
            entropy_max,
            entropy_max_dev,
            trace_min,
            trace_median,
            trace_max,
            trace_max_dev,
        )
    ):
        raise ValueError("leave-one-period-out stability summary is non-finite")

    identity = {
        "schema_version": "DAXLAB_KEFF_LOO_STABILITY_V1",
        "method": "LEAVE_ONE_PERIOD_OUT_SPECTRAL_SENSITIVITY",
        "parent_entropy_effective_rank": parent_entropy,
        "parent_trace_over_lambda_max_effective_rank": parent_trace,
        "observations": [item.to_payload() for item in observations],
        "entropy_min": entropy_min,
        "entropy_median": entropy_median,
        "entropy_max": entropy_max,
        "entropy_max_abs_deviation_from_parent": entropy_max_dev,
        "trace_min": trace_min,
        "trace_median": trace_median,
        "trace_max": trace_max,
        "trace_max_abs_deviation_from_parent": trace_max_dev,
        "parent_matrix_sha256": evidence.matrix_sha256,
        "upstream_evidence_sha256": evidence.upstream_evidence_sha256,
        "confirmatory_use_allowed": False,
        "dsr_adjustment_applied": False,
        "confidence_interval_claimed": False,
    }
    stability_sha256 = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    return KEffLOOStabilityResult(
        parent_entropy_effective_rank=parent_entropy,
        parent_trace_over_lambda_max_effective_rank=parent_trace,
        observations=tuple(observations),
        entropy_min=entropy_min,
        entropy_median=entropy_median,
        entropy_max=entropy_max,
        entropy_max_abs_deviation_from_parent=entropy_max_dev,
        trace_min=trace_min,
        trace_median=trace_median,
        trace_max=trace_max,
        trace_max_abs_deviation_from_parent=trace_max_dev,
        parent_matrix_sha256=evidence.matrix_sha256,
        upstream_evidence_sha256=evidence.upstream_evidence_sha256,
        stability_sha256=stability_sha256,
        confirmatory_use_allowed=False,
        dsr_adjustment_applied=False,
    )
