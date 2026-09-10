from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Iterable, Mapping, Sequence

import numpy as np

from daxlab.research.multiple_testing_preflight import (
    READY,
    TrialPeriodReturn,
    preflight_multiple_testing_evidence,
)


_ESTIMATOR = "DAXLAB_NATIVE_SAMPLE_V1"


@dataclass(frozen=True)
class DSREvidenceStatistics:
    target_trial_id: str
    observed_sr: float
    n_obs: int
    skewness: float
    pearson_kurtosis: float
    n_trials: int
    trial_sharpe_variance: float
    trial_variance_ddof: int
    sharpe_estimator: str
    trial_order: tuple[str, ...]
    period_order: tuple[str, ...]
    upstream_evidence_sha256: str
    evidence_sha256: str

    def to_payload(self) -> dict[str, object]:
        return {
            "schema_version": "DAXLAB_DSR_EVIDENCE_STATISTICS_V1",
            "target_trial_id": self.target_trial_id,
            "observed_sr": self.observed_sr,
            "n_obs": self.n_obs,
            "skewness": self.skewness,
            "pearson_kurtosis": self.pearson_kurtosis,
            "n_trials": self.n_trials,
            "trial_sharpe_variance": self.trial_sharpe_variance,
            "trial_variance_ddof": self.trial_variance_ddof,
            "sharpe_estimator": self.sharpe_estimator,
            "trial_order": list(self.trial_order),
            "period_order": list(self.period_order),
            "upstream_evidence_sha256": self.upstream_evidence_sha256,
            "evidence_sha256": self.evidence_sha256,
            "sharpe_unit": "NATIVE_PERIOD",
            "annualized": False,
            "statistics_computed": False,
        }


def _coerce(row: TrialPeriodReturn | Mapping[str, object]) -> TrialPeriodReturn:
    if isinstance(row, TrialPeriodReturn):
        return row
    return TrialPeriodReturn(
        trial_id=str(row["trial_id"]),
        period_id=str(row["period_id"]),
        return_value=float(row["return_value"]),
        status=str(row.get("status", "COMPLETED")).upper(),
    )


def _native_sample_moments(values: np.ndarray) -> tuple[float, float, float]:
    if values.ndim != 1 or values.size < 3:
        raise ValueError("DSR target series must contain at least 3 periods")
    if not np.isfinite(values).all():
        raise ValueError("DSR target series must contain only finite values")
    mean = float(values.mean())
    std = float(values.std(ddof=1))
    if not math.isfinite(std) or std <= 0.0:
        raise ValueError("DSR target series has zero or invalid sample variance")
    centered = values - mean
    observed_sr = mean / std
    skewness = float(np.mean(centered**3) / std**3)
    pearson_kurtosis = float(np.mean(centered**4) / std**4)
    if not all(math.isfinite(v) for v in (observed_sr, skewness, pearson_kurtosis)):
        raise ValueError("DSR target moments are non-finite")
    return observed_sr, skewness, pearson_kurtosis


def build_dsr_evidence_statistics(
    rows: Iterable[TrialPeriodReturn | Mapping[str, object]],
    *,
    target_trial_id: str,
    trial_order: Sequence[str],
    period_order: Sequence[str],
) -> DSREvidenceStatistics:
    """Build explicit classical-DSR inputs under DAXLAB_NATIVE_SAMPLE_V1.

    Convention V1:
    - native-period Sharpe = mean / sample std (ddof=1)
    - target skew/kurtosis = standardized central moments on that same std scale
    - cross-trial Sharpe variance = sample variance (ddof=1)
    - no annualization, autocorrelation adjustment, or effective-trial correction
    """
    materialized = [_coerce(row) for row in rows]
    trials = tuple(value.strip() for value in trial_order)
    periods = tuple(value.strip() for value in period_order)
    target = target_trial_id.strip()

    if len(trials) < 2 or any(not value for value in trials) or len(trials) != len(set(trials)):
        raise ValueError("trial_order must contain at least 2 unique non-empty trial IDs")
    if len(periods) < 3 or any(not value for value in periods) or len(periods) != len(set(periods)):
        raise ValueError("period_order must contain at least 3 unique non-empty period IDs")
    if target not in trials:
        raise ValueError("target_trial_id must appear in trial_order")

    preflight = preflight_multiple_testing_evidence(
        materialized,
        expected_trial_count=len(trials),
        declared_trial_ids=trials,
    )
    if preflight.status != READY:
        raise ValueError("multiple-testing evidence is not READY: " + ",".join(preflight.blockers))
    if {row.period_id for row in materialized} != set(periods):
        raise ValueError("period_order does not match observed period IDs")

    by_key = {(row.trial_id, row.period_id): row.return_value for row in materialized}
    matrix = np.asarray(
        [[by_key[(trial_id, period_id)] for period_id in periods] for trial_id in trials],
        dtype=float,
    )
    if not np.isfinite(matrix).all():
        raise ValueError("ordered DSR return matrix is invalid")

    trial_sharpes: list[float] = []
    target_moments: tuple[float, float, float] | None = None
    for row_index, trial_id in enumerate(trials):
        values = matrix[row_index]
        observed_sr, skewness, kurtosis = _native_sample_moments(values)
        trial_sharpes.append(observed_sr)
        if trial_id == target:
            target_moments = (observed_sr, skewness, kurtosis)
    assert target_moments is not None

    trial_variance = float(np.var(np.asarray(trial_sharpes, dtype=float), ddof=1))
    if not math.isfinite(trial_variance) or trial_variance < 0.0:
        raise ValueError("trial Sharpe variance is invalid")

    identity = {
        "estimator": _ESTIMATOR,
        "target_trial_id": target,
        "trial_order": list(trials),
        "period_order": list(periods),
        "upstream_evidence_sha256": preflight.evidence_sha256,
        "trial_sharpes": trial_sharpes,
        "observed_sr": target_moments[0],
        "skewness": target_moments[1],
        "pearson_kurtosis": target_moments[2],
        "trial_sharpe_variance": trial_variance,
        "trial_variance_ddof": 1,
    }
    evidence_sha256 = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    return DSREvidenceStatistics(
        target_trial_id=target,
        observed_sr=target_moments[0],
        n_obs=len(periods),
        skewness=target_moments[1],
        pearson_kurtosis=target_moments[2],
        n_trials=len(trials),
        trial_sharpe_variance=trial_variance,
        trial_variance_ddof=1,
        sharpe_estimator=_ESTIMATOR,
        trial_order=trials,
        period_order=periods,
        upstream_evidence_sha256=preflight.evidence_sha256,
        evidence_sha256=evidence_sha256,
    )
