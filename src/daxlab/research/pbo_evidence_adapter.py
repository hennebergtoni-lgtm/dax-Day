from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Iterable, Mapping, Sequence

import numpy as np

from daxlab.research.multiple_testing_preflight import (
    READY,
    TrialPeriodReturn,
    preflight_multiple_testing_evidence,
)


@dataclass(frozen=True)
class PBOEvidenceMatrix:
    matrix: np.ndarray
    trial_order: tuple[str, ...]
    period_order: tuple[str, ...]
    upstream_evidence_sha256: str
    matrix_sha256: str

    def to_payload(self) -> dict[str, object]:
        return {
            "schema_version": "DAXLAB_PBO_EVIDENCE_MATRIX_V1",
            "trial_order": list(self.trial_order),
            "period_order": list(self.period_order),
            "matrix": self.matrix.tolist(),
            "upstream_evidence_sha256": self.upstream_evidence_sha256,
            "matrix_sha256": self.matrix_sha256,
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


def build_pbo_evidence_matrix(
    rows: Iterable[TrialPeriodReturn | Mapping[str, object]],
    *,
    trial_order: Sequence[str],
    period_order: Sequence[str],
) -> PBOEvidenceMatrix:
    """Project complete multiple-testing evidence into one ordered PBO matrix."""
    materialized = [_coerce(row) for row in rows]
    trials = tuple(value.strip() for value in trial_order)
    periods = tuple(value.strip() for value in period_order)

    if not trials or any(not value for value in trials):
        raise ValueError("trial_order must contain non-empty trial IDs")
    if len(trials) != len(set(trials)):
        raise ValueError("trial_order contains duplicates")
    if not periods or any(not value for value in periods):
        raise ValueError("period_order must contain non-empty period IDs")
    if len(periods) != len(set(periods)):
        raise ValueError("period_order contains duplicates")

    preflight = preflight_multiple_testing_evidence(
        materialized,
        expected_trial_count=len(trials),
        declared_trial_ids=trials,
    )
    if preflight.status != READY:
        raise ValueError("multiple-testing evidence is not READY: " + ",".join(preflight.blockers))

    observed_periods = {row.period_id for row in materialized}
    if set(periods) != observed_periods:
        raise ValueError("period_order does not match observed period IDs")

    by_key = {(row.trial_id, row.period_id): row.return_value for row in materialized}
    matrix = np.asarray(
        [[by_key[(trial_id, period_id)] for period_id in periods] for trial_id in trials],
        dtype=float,
    )
    if matrix.shape != (len(trials), len(periods)) or not np.isfinite(matrix).all():
        raise ValueError("ordered PBO matrix is invalid")

    identity = {
        "upstream_evidence_sha256": preflight.evidence_sha256,
        "trial_order": list(trials),
        "period_order": list(periods),
        "matrix": matrix.tolist(),
    }
    matrix_sha256 = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    matrix.setflags(write=False)
    return PBOEvidenceMatrix(
        matrix=matrix,
        trial_order=trials,
        period_order=periods,
        upstream_evidence_sha256=preflight.evidence_sha256,
        matrix_sha256=matrix_sha256,
    )
