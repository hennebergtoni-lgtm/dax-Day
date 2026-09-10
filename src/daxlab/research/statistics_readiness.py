from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

from daxlab.research.multiple_testing_preflight import (
    TrialPeriodReturn,
    preflight_multiple_testing_evidence,
)

READY = "READY_FOR_CONFIRMATORY_OVERFITTING_STATISTICS"
BLOCKED = "BLOCKED_CONFIRMATORY_STATISTICS_INPUT_NOT_READY"
_PBO_ONLY_BLOCKERS = {
    "PBO_BLOCK_COUNT_MUST_BE_EVEN_AND_AT_LEAST_4",
    "PBO_BLOCK_COUNT_EXCEEDS_PERIOD_COUNT",
    "PERIOD_COUNT_NOT_DIVISIBLE_BY_PBO_BLOCKS",
}


@dataclass(frozen=True)
class StatisticsReadinessResult:
    status: str
    blockers: tuple[str, ...]
    trial_count: int
    period_count: int
    pbo_blocks: int
    confirmatory_governance_required: bool
    dsr_ready: bool
    pbo_ready: bool
    multiple_testing_evidence_sha256: str

    @property
    def ready(self) -> bool:
        return self.status == READY

    def to_payload(self) -> dict[str, object]:
        return {
            "schema_version": "DAXLAB_STATISTICS_READINESS_V1",
            "status": self.status,
            "ready": self.ready,
            "blockers": list(self.blockers),
            "trial_count": self.trial_count,
            "period_count": self.period_count,
            "pbo_blocks": self.pbo_blocks,
            "confirmatory_governance_required": self.confirmatory_governance_required,
            "dsr_ready": self.dsr_ready,
            "pbo_ready": self.pbo_ready,
            "multiple_testing_evidence_sha256": self.multiple_testing_evidence_sha256,
            "statistics_computed": False,
        }


def _row_parts(row: TrialPeriodReturn | Mapping[str, object]) -> tuple[str, str]:
    if isinstance(row, TrialPeriodReturn):
        return row.trial_id, row.period_id
    return str(row["trial_id"]), str(row["period_id"])


def preflight_statistics_readiness(
    rows: Iterable[TrialPeriodReturn | Mapping[str, object]],
    *,
    expected_trial_count: int,
    declared_trial_ids: Sequence[str],
    verified_predeclared_trial_ids: Sequence[str],
    period_order: Sequence[str],
    pbo_blocks: int,
) -> StatisticsReadinessResult:
    """Fail closed before confirmatory DSR/PBO reporting is allowed.

    Full Git-verified predeclaration is a DAXLAB confirmatory-governance rule,
    not a mathematical prerequisite of the DSR formula itself. Matrix
    completeness is delegated to the established multiple-testing preflight;
    this layer adds chronology governance, explicit temporal ordering and
    CSCV/PBO partition readiness. No statistic is computed here.
    """
    materialized = list(rows)
    base = preflight_multiple_testing_evidence(
        materialized,
        expected_trial_count=expected_trial_count,
        declared_trial_ids=declared_trial_ids,
    )
    blockers: set[str] = set(base.blockers)

    declared = [value.strip() for value in declared_trial_ids]
    verified = [value.strip() for value in verified_predeclared_trial_ids]
    if any(not value for value in verified):
        blockers.add("EMPTY_VERIFIED_PREDECLARED_TRIAL_ID")
    if len(verified) != len(set(verified)):
        blockers.add("DUPLICATE_VERIFIED_PREDECLARED_TRIAL_ID")
    if set(verified) != set(declared):
        blockers.add("NOT_ALL_DECLARED_TRIALS_CHRONOLOGY_VERIFIED")

    order = [value.strip() for value in period_order]
    if any(not value for value in order):
        blockers.add("EMPTY_PERIOD_ORDER_ID")
    if len(order) != len(set(order)):
        blockers.add("DUPLICATE_PERIOD_ORDER_ID")
    observed_periods = {period_id for _, period_id in map(_row_parts, materialized)}
    if set(order) != observed_periods:
        blockers.add("PERIOD_ORDER_SET_MISMATCH")

    if len(order) < 4:
        blockers.add("INSUFFICIENT_PERIODS_FOR_DSR_MOMENTS")

    if pbo_blocks < 4 or pbo_blocks % 2 != 0:
        blockers.add("PBO_BLOCK_COUNT_MUST_BE_EVEN_AND_AT_LEAST_4")
    elif len(order) < pbo_blocks:
        blockers.add("PBO_BLOCK_COUNT_EXCEEDS_PERIOD_COUNT")
    elif len(order) % pbo_blocks != 0:
        blockers.add("PERIOD_COUNT_NOT_DIVISIBLE_BY_PBO_BLOCKS")

    ordered = tuple(sorted(blockers))
    dsr_ready = not (set(ordered) - _PBO_ONLY_BLOCKERS)
    pbo_ready = not ordered

    return StatisticsReadinessResult(
        status=READY if dsr_ready and pbo_ready else BLOCKED,
        blockers=ordered,
        trial_count=base.observed_trial_count,
        period_count=len(order),
        pbo_blocks=pbo_blocks,
        confirmatory_governance_required=True,
        dsr_ready=dsr_ready,
        pbo_ready=pbo_ready,
        multiple_testing_evidence_sha256=base.evidence_sha256,
    )
