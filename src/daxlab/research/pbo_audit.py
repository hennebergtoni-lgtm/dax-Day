from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Iterable, Mapping, Sequence

from daxlab.research.classical_pbo import classical_probability_of_backtest_overfitting
from daxlab.research.multiple_testing_preflight import TrialPeriodReturn
from daxlab.research.pbo_evidence_adapter import build_pbo_evidence_matrix
from daxlab.research.statistics_readiness import preflight_statistics_readiness


@dataclass(frozen=True)
class ConfirmatoryPBOAuditResult:
    pbo: float
    n_combinations: int
    n_trials: int
    n_periods: int
    pbo_blocks: int
    performance_metric: str
    multiple_testing_evidence_sha256: str
    matrix_sha256: str
    audit_sha256: str

    def to_payload(self) -> dict[str, object]:
        return {
            "schema_version": "DAXLAB_CONFIRMATORY_PBO_AUDIT_V1",
            "method": "CLASSICAL_CSCV_PBO",
            "pbo": self.pbo,
            "n_combinations": self.n_combinations,
            "n_trials": self.n_trials,
            "n_periods": self.n_periods,
            "pbo_blocks": self.pbo_blocks,
            "performance_metric": self.performance_metric,
            "multiple_testing_evidence_sha256": self.multiple_testing_evidence_sha256,
            "matrix_sha256": self.matrix_sha256,
            "audit_sha256": self.audit_sha256,
            "confirmatory_governance_enforced": True,
            "purge_enabled": False,
            "embargo_enabled": False,
            "statistics_computed": True,
        }


def run_confirmatory_pbo_audit(
    rows: Iterable[TrialPeriodReturn | Mapping[str, object]],
    *,
    expected_trial_count: int,
    declared_trial_ids: Sequence[str],
    verified_predeclared_trial_ids: Sequence[str],
    trial_order: Sequence[str],
    period_order: Sequence[str],
    pbo_blocks: int,
) -> ConfirmatoryPBOAuditResult:
    """Run classical CSCV PBO only after all confirmatory evidence gates pass."""
    materialized = list(rows)
    readiness = preflight_statistics_readiness(
        materialized,
        expected_trial_count=expected_trial_count,
        declared_trial_ids=declared_trial_ids,
        verified_predeclared_trial_ids=verified_predeclared_trial_ids,
        period_order=period_order,
        pbo_blocks=pbo_blocks,
    )
    if not readiness.pbo_ready:
        raise ValueError("PBO inputs are not confirmatory-ready: " + ",".join(readiness.blockers))

    declared_set = {value.strip() for value in declared_trial_ids}
    ordered_trials = tuple(value.strip() for value in trial_order)
    if set(ordered_trials) != declared_set or len(ordered_trials) != len(declared_set):
        raise ValueError("trial_order must contain each declared trial exactly once")

    evidence = build_pbo_evidence_matrix(
        materialized,
        trial_order=ordered_trials,
        period_order=period_order,
    )
    if evidence.upstream_evidence_sha256 != readiness.multiple_testing_evidence_sha256:
        raise ValueError("PBO evidence hash disagrees with statistics-readiness evidence")

    pbo_result = classical_probability_of_backtest_overfitting(
        evidence.matrix,
        n_splits=pbo_blocks,
    )
    identity = {
        "method": "CLASSICAL_CSCV_PBO",
        "pbo": pbo_result.pbo,
        "n_combinations": pbo_result.n_combinations,
        "n_trials": pbo_result.n_trials,
        "n_periods": pbo_result.n_periods,
        "pbo_blocks": pbo_blocks,
        "performance_metric": pbo_result.performance_metric,
        "multiple_testing_evidence_sha256": readiness.multiple_testing_evidence_sha256,
        "matrix_sha256": evidence.matrix_sha256,
    }
    audit_sha256 = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    return ConfirmatoryPBOAuditResult(
        pbo=pbo_result.pbo,
        n_combinations=pbo_result.n_combinations,
        n_trials=pbo_result.n_trials,
        n_periods=pbo_result.n_periods,
        pbo_blocks=pbo_blocks,
        performance_metric=pbo_result.performance_metric,
        multiple_testing_evidence_sha256=readiness.multiple_testing_evidence_sha256,
        matrix_sha256=evidence.matrix_sha256,
        audit_sha256=audit_sha256,
    )
