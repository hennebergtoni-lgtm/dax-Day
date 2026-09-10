from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Iterable, Mapping, Sequence

READY = "READY_FOR_MULTIPLE_TESTING"
BLOCKED = "BLOCKED_INCOMPLETE_TRIAL_EVIDENCE"
_ALLOWED_STATUSES = {"ACTIVE", "REJECTED", "ABANDONED", "FAILED", "COMPLETED"}


@dataclass(frozen=True)
class TrialPeriodReturn:
    trial_id: str
    period_id: str
    return_value: float
    status: str = "COMPLETED"


@dataclass(frozen=True)
class MultipleTestingPreflightResult:
    status: str
    blockers: tuple[str, ...]
    expected_trial_count: int
    observed_trial_count: int
    period_count: int
    matrix_cell_count: int
    expected_matrix_cell_count: int
    evidence_sha256: str

    @property
    def ready(self) -> bool:
        return self.status == READY

    def to_payload(self) -> dict[str, object]:
        return {
            "schema_version": "DAXLAB_MULTIPLE_TESTING_PREFLIGHT_V1",
            "status": self.status,
            "ready": self.ready,
            "blockers": list(self.blockers),
            "expected_trial_count": self.expected_trial_count,
            "observed_trial_count": self.observed_trial_count,
            "period_count": self.period_count,
            "matrix_cell_count": self.matrix_cell_count,
            "expected_matrix_cell_count": self.expected_matrix_cell_count,
            "evidence_sha256": self.evidence_sha256,
            "statistics_computed": False,
        }


def _coerce_row(row: TrialPeriodReturn | Mapping[str, object]) -> TrialPeriodReturn:
    if isinstance(row, TrialPeriodReturn):
        return row
    return TrialPeriodReturn(
        trial_id=str(row["trial_id"]),
        period_id=str(row["period_id"]),
        return_value=float(row["return_value"]),
        status=str(row.get("status", "COMPLETED")).upper(),
    )


def preflight_multiple_testing_evidence(
    rows: Iterable[TrialPeriodReturn | Mapping[str, object]],
    *,
    expected_trial_count: int,
    declared_trial_ids: Sequence[str] | None = None,
) -> MultipleTestingPreflightResult:
    """Check evidence completeness before DSR/PBO or related statistics are allowed."""
    if expected_trial_count < 2:
        raise ValueError("expected_trial_count must be >= 2")

    normalized = [_coerce_row(row) for row in rows]
    blockers: set[str] = set()
    cells: dict[tuple[str, str], TrialPeriodReturn] = {}
    trial_statuses: dict[str, set[str]] = {}

    for row in normalized:
        if not row.trial_id.strip() or not row.period_id.strip():
            blockers.add("EMPTY_TRIAL_OR_PERIOD_ID")
            continue
        if not math.isfinite(row.return_value):
            blockers.add("NON_FINITE_RETURN_VALUE")
        status = row.status.upper()
        if status not in _ALLOWED_STATUSES:
            blockers.add("UNKNOWN_TRIAL_STATUS")
        key = (row.trial_id, row.period_id)
        if key in cells:
            blockers.add("DUPLICATE_TRIAL_PERIOD_CELL")
        else:
            cells[key] = row
        trial_statuses.setdefault(row.trial_id, set()).add(status)

    if any(len(statuses) != 1 for statuses in trial_statuses.values()):
        blockers.add("INCONSISTENT_TRIAL_STATUS")

    trial_ids = sorted(trial_statuses)
    periods = sorted({period_id for _, period_id in cells})
    if len(trial_ids) != expected_trial_count:
        blockers.add("TRIAL_COUNT_MISMATCH")

    if declared_trial_ids is not None:
        declared = [trial_id.strip() for trial_id in declared_trial_ids]
        if len(declared) != len(set(declared)):
            blockers.add("DUPLICATE_DECLARED_TRIAL_ID")
        if len(declared) != expected_trial_count:
            blockers.add("DECLARED_TRIAL_COUNT_MISMATCH")
        if set(declared) != set(trial_ids):
            blockers.add("DECLARED_TRIAL_SET_MISMATCH")

    all_periods = set(periods)
    for trial_id in trial_ids:
        observed_periods = {period for trial, period in cells if trial == trial_id}
        if observed_periods != all_periods:
            blockers.add("INCOMPLETE_TRIAL_PERIOD_MATRIX")
            break

    expected_cells = expected_trial_count * len(periods)
    if len(cells) != expected_cells:
        blockers.add("MATRIX_CELL_COUNT_MISMATCH")

    canonical = [
        {
            "trial_id": row.trial_id,
            "period_id": row.period_id,
            "return_value": row.return_value,
            "status": row.status.upper(),
        }
        for row in sorted(cells.values(), key=lambda x: (x.trial_id, x.period_id))
    ]
    evidence_sha256 = hashlib.sha256(
        json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    ordered_blockers = tuple(sorted(blockers))
    return MultipleTestingPreflightResult(
        status=READY if not ordered_blockers else BLOCKED,
        blockers=ordered_blockers,
        expected_trial_count=expected_trial_count,
        observed_trial_count=len(trial_ids),
        period_count=len(periods),
        matrix_cell_count=len(cells),
        expected_matrix_cell_count=expected_cells,
        evidence_sha256=evidence_sha256,
    )
