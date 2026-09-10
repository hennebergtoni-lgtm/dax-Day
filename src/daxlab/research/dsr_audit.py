from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Iterable, Mapping, Sequence

from daxlab.research.classical_dsr import classical_deflated_sharpe_ratio_from_statistics
from daxlab.research.dsr_evidence_adapter import build_dsr_evidence_statistics
from daxlab.research.multiple_testing_preflight import TrialPeriodReturn
from daxlab.research.statistics_readiness import preflight_statistics_readiness


@dataclass(frozen=True)
class ConfirmatoryDSRAuditResult:
    target_trial_id: str
    probability: float
    z_score: float
    observed_sr: float
    sr_star: float
    expected_max_z: float
    n_obs: int
    n_trials: int
    trial_sharpe_variance: float
    trial_variance_ddof: int
    sharpe_estimator: str
    multiple_testing_evidence_sha256: str
    dsr_evidence_sha256: str
    audit_sha256: str

    def to_payload(self) -> dict[str, object]:
        return {
            "schema_version": "DAXLAB_CONFIRMATORY_DSR_AUDIT_V1",
            "method": "BAILEY_LOPEZ_DE_PRADO_CLASSICAL_DSR",
            "target_trial_id": self.target_trial_id,
            "probability": self.probability,
            "z_score": self.z_score,
            "observed_sr": self.observed_sr,
            "sr_star": self.sr_star,
            "expected_max_z": self.expected_max_z,
            "n_obs": self.n_obs,
            "n_trials": self.n_trials,
            "trial_sharpe_variance": self.trial_sharpe_variance,
            "trial_variance_ddof": self.trial_variance_ddof,
            "sharpe_estimator": self.sharpe_estimator,
            "multiple_testing_evidence_sha256": self.multiple_testing_evidence_sha256,
            "dsr_evidence_sha256": self.dsr_evidence_sha256,
            "audit_sha256": self.audit_sha256,
            "confirmatory_governance_enforced": True,
            "sharpe_unit": "NATIVE_PERIOD",
            "annualized": False,
            "autocorrelation_adjustment": False,
            "effective_trial_adjustment": False,
            "statistics_computed": True,
        }


def run_confirmatory_dsr_audit(
    rows: Iterable[TrialPeriodReturn | Mapping[str, object]],
    *,
    expected_trial_count: int,
    declared_trial_ids: Sequence[str],
    verified_predeclared_trial_ids: Sequence[str],
    target_trial_id: str,
    trial_order: Sequence[str],
    period_order: Sequence[str],
) -> ConfirmatoryDSRAuditResult:
    """Run classical DSR only after all DAXLAB confirmatory evidence gates pass."""
    materialized = list(rows)
    readiness = preflight_statistics_readiness(
        materialized,
        expected_trial_count=expected_trial_count,
        declared_trial_ids=declared_trial_ids,
        verified_predeclared_trial_ids=verified_predeclared_trial_ids,
        period_order=period_order,
        pbo_blocks=4,
    )
    if not readiness.dsr_ready:
        dsr_blockers = [
            blocker
            for blocker in readiness.blockers
            if blocker
            not in {
                "PBO_BLOCK_COUNT_MUST_BE_EVEN_AND_AT_LEAST_4",
                "PBO_BLOCK_COUNT_EXCEEDS_PERIOD_COUNT",
                "PERIOD_COUNT_NOT_DIVISIBLE_BY_PBO_BLOCKS",
            }
        ]
        raise ValueError("DSR inputs are not confirmatory-ready: " + ",".join(dsr_blockers))

    declared = {value.strip() for value in declared_trial_ids}
    ordered_trials = tuple(value.strip() for value in trial_order)
    target = target_trial_id.strip()
    if set(ordered_trials) != declared or len(ordered_trials) != len(declared):
        raise ValueError("trial_order must contain each declared trial exactly once")
    if target not in declared:
        raise ValueError("target_trial_id must be one of the declared trials")

    evidence = build_dsr_evidence_statistics(
        materialized,
        target_trial_id=target,
        trial_order=ordered_trials,
        period_order=period_order,
    )
    if evidence.upstream_evidence_sha256 != readiness.multiple_testing_evidence_sha256:
        raise ValueError("DSR evidence hash disagrees with statistics-readiness evidence")

    dsr = classical_deflated_sharpe_ratio_from_statistics(
        observed_sr=evidence.observed_sr,
        n_obs=evidence.n_obs,
        skewness=evidence.skewness,
        pearson_kurtosis=evidence.pearson_kurtosis,
        n_trials=evidence.n_trials,
        trial_sharpe_variance=evidence.trial_sharpe_variance,
        trial_variance_ddof=evidence.trial_variance_ddof,
    )
    identity = {
        "method": "BAILEY_LOPEZ_DE_PRADO_CLASSICAL_DSR",
        "target_trial_id": target,
        "probability": dsr.probability,
        "z_score": dsr.z_score,
        "observed_sr": dsr.observed_sr,
        "sr_star": dsr.sr_star,
        "expected_max_z": dsr.expected_max_z,
        "n_obs": dsr.n_obs,
        "n_trials": dsr.n_trials,
        "trial_sharpe_variance": dsr.trial_sharpe_variance,
        "trial_variance_ddof": dsr.trial_variance_ddof,
        "sharpe_estimator": evidence.sharpe_estimator,
        "multiple_testing_evidence_sha256": readiness.multiple_testing_evidence_sha256,
        "dsr_evidence_sha256": evidence.evidence_sha256,
    }
    audit_sha256 = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    return ConfirmatoryDSRAuditResult(
        target_trial_id=target,
        probability=dsr.probability,
        z_score=dsr.z_score,
        observed_sr=dsr.observed_sr,
        sr_star=dsr.sr_star,
        expected_max_z=dsr.expected_max_z,
        n_obs=dsr.n_obs,
        n_trials=dsr.n_trials,
        trial_sharpe_variance=dsr.trial_sharpe_variance,
        trial_variance_ddof=dsr.trial_variance_ddof,
        sharpe_estimator=evidence.sharpe_estimator,
        multiple_testing_evidence_sha256=readiness.multiple_testing_evidence_sha256,
        dsr_evidence_sha256=evidence.evidence_sha256,
        audit_sha256=audit_sha256,
    )
