"""Cost-stress integrity audit for frozen CAND-001 OOS/WF evidence.

The explicit 1.x cost model applies spread/slippage/commission as additive adverse
points after the causal market-price lifecycle. Therefore changing only the cost
multiplier must not change strategy/lifecycle path counts or gross-R. This audit
checks those invariants before any economic interpretation is allowed.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
import math

from daxlab.research.cand001_oos_aggregation import (
    Cand001OosAggregation,
    aggregate_cand001_oos,
)
from daxlab.research.cand001_oos_measurement_runner import (
    Cand001OosMeasurement,
    Cand001OosMeasurementBundle,
)
from daxlab.research.cand001_oos_walk_forward import ECONOMIC_CLAIM, EVIDENCE_CLASS
from daxlab.runtime.decision import stable_fingerprint


CAND001_OOS_COST_CONSISTENCY_SCHEMA = "DAXLAB_CAND001_OOS_COST_CONSISTENCY_V1"
_EXPECTED_COSTS = (("normal", 1.0), ("stress_1.5x", 1.5), ("stress_2x", 2.0))
_TOLERANCE = 1e-10


class CostConsistencyState(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"


@dataclass(frozen=True, slots=True)
class Cand001OosWindowCostConsistency:
    window_number: int
    cost_result_fingerprints: tuple[str, ...]
    blockers: tuple[str, ...]
    state: CostConsistencyState
    audit_fingerprint: str

    def __post_init__(self) -> None:
        if self.window_number <= 0:
            raise ValueError("window_number must be positive")
        if len(self.cost_result_fingerprints) != len(_EXPECTED_COSTS):
            raise ValueError("window cost audit requires exactly three result fingerprints")
        for index, value in enumerate(self.cost_result_fingerprints, start=1):
            _assert_sha256(value, field=f"cost_result_fingerprints[{index}]")
        if self.state is CostConsistencyState.PASS and self.blockers:
            raise ValueError("PASS window cost audit cannot carry blockers")
        if self.state is CostConsistencyState.FAIL and not self.blockers:
            raise ValueError("FAIL window cost audit requires blockers")
        _assert_sha256(self.audit_fingerprint, field="audit_fingerprint")

    def to_payload(self) -> dict[str, object]:
        payload = asdict(self)
        payload["state"] = self.state.value
        return payload


@dataclass(frozen=True, slots=True)
class Cand001OosCostConsistencyAudit:
    schema_version: str
    state: CostConsistencyState
    source_bundle_fingerprint: str
    source_aggregation_fingerprint: str
    window_count: int
    passed_windows: int
    failed_windows: int
    window_audits: tuple[Cand001OosWindowCostConsistency, ...]
    blockers: tuple[str, ...]
    trade_record_identity_policy: str
    audit_fingerprint: str
    evidence_class: str = EVIDENCE_CLASS
    economic_claim: str = ECONOMIC_CLAIM
    interpretation: str = "EVIDENCE_INTEGRITY_ONLY_NOT_ECONOMIC_PASS_FAIL"
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != CAND001_OOS_COST_CONSISTENCY_SCHEMA:
            raise ValueError("unsupported OOS cost-consistency schema")
        _assert_sha256(self.source_bundle_fingerprint, field="source_bundle_fingerprint")
        _assert_sha256(
            self.source_aggregation_fingerprint,
            field="source_aggregation_fingerprint",
        )
        _assert_sha256(self.audit_fingerprint, field="audit_fingerprint")
        if self.window_count <= 0 or len(self.window_audits) != self.window_count:
            raise ValueError("cost-consistency window count drift")
        if self.passed_windows + self.failed_windows != self.window_count:
            raise ValueError("cost-consistency pass/fail counts do not cover windows")
        if self.state is CostConsistencyState.PASS and self.blockers:
            raise ValueError("PASS cost-consistency audit cannot carry blockers")
        if self.state is CostConsistencyState.FAIL and not self.blockers:
            raise ValueError("FAIL cost-consistency audit requires blockers")
        if self.execution_capability != "NONE" or self.order_execution_enabled:
            raise ValueError("cost-consistency audit cannot authorize execution")

    def to_payload(self) -> dict[str, object]:
        payload = asdict(self)
        payload["state"] = self.state.value
        payload["window_audits"] = [item.to_payload() for item in self.window_audits]
        return payload


def audit_cand001_oos_cost_consistency(
    measurement: Cand001OosMeasurementBundle,
    aggregation: Cand001OosAggregation,
) -> Cand001OosCostConsistencyAudit:
    """Audit cost-only stress invariants without interpreting profitability."""
    if aggregation != aggregate_cand001_oos(measurement):
        raise ValueError("aggregation is not the canonical result of the measurement bundle")
    observed_costs = tuple(
        sorted(
            {(item.cost_model, item.cost_multiplier) for item in measurement.measurements},
            key=lambda item: item[1],
        )
    )
    if observed_costs != _EXPECTED_COSTS:
        raise ValueError(f"unexpected frozen cost-stress contract: {observed_costs}")

    by_window: dict[int, list[Cand001OosMeasurement]] = {}
    for item in measurement.measurements:
        by_window.setdefault(item.window_number, []).append(item)
    expected_windows = set(range(1, measurement.window_count + 1))
    if set(by_window) != expected_windows:
        raise ValueError("measurement windows are incomplete for cost-consistency audit")

    window_audits = tuple(
        _audit_window(number, tuple(by_window[number]))
        for number in range(1, measurement.window_count + 1)
    )
    failed = tuple(item for item in window_audits if item.state is CostConsistencyState.FAIL)
    blockers = tuple(
        f"WINDOW_{item.window_number}:{blocker}"
        for item in failed
        for blocker in item.blockers
    )
    state = CostConsistencyState.FAIL if blockers else CostConsistencyState.PASS
    identity = {
        "schema_version": CAND001_OOS_COST_CONSISTENCY_SCHEMA,
        "source_bundle_fingerprint": measurement.bundle_fingerprint,
        "source_aggregation_fingerprint": aggregation.aggregation_fingerprint,
        "window_audit_fingerprints": tuple(item.audit_fingerprint for item in window_audits),
        "blockers": blockers,
        "trade_record_identity_policy": (
            "NOT_EQUALITY_CHECKED_COST_DEPENDENT_RECORDS_INCLUDE_NET_R_OUTCOME_AND_FILL_MODEL"
        ),
        "evidence_class": EVIDENCE_CLASS,
        "economic_claim": ECONOMIC_CLAIM,
        "interpretation": "EVIDENCE_INTEGRITY_ONLY_NOT_ECONOMIC_PASS_FAIL",
        "execution_capability": "NONE",
        "order_execution_enabled": False,
    }
    return Cand001OosCostConsistencyAudit(
        schema_version=CAND001_OOS_COST_CONSISTENCY_SCHEMA,
        state=state,
        source_bundle_fingerprint=measurement.bundle_fingerprint,
        source_aggregation_fingerprint=aggregation.aggregation_fingerprint,
        window_count=measurement.window_count,
        passed_windows=measurement.window_count - len(failed),
        failed_windows=len(failed),
        window_audits=window_audits,
        blockers=blockers,
        trade_record_identity_policy=identity["trade_record_identity_policy"],
        audit_fingerprint=stable_fingerprint(identity),
    )


def _audit_window(
    window_number: int,
    items: tuple[Cand001OosMeasurement, ...],
) -> Cand001OosWindowCostConsistency:
    ordered = tuple(sorted(items, key=lambda item: item.cost_multiplier))
    observed = tuple((item.cost_model, item.cost_multiplier) for item in ordered)
    if observed != _EXPECTED_COSTS:
        raise ValueError(f"window {window_number} cost coverage drift: {observed}")

    baseline = ordered[0]
    blockers: list[str] = []
    invariant_fields = (
        "processed_bars",
        "processed_sessions",
        "directional_signals",
        "admitted_trades",
        "completed_trades",
        "open_trade_at_end",
    )
    for item in ordered[1:]:
        for field in invariant_fields:
            if getattr(item, field) != getattr(baseline, field):
                blockers.append(f"PATH_INVARIANT_DRIFT:{field}")
        if not _close(item.gross_r, baseline.gross_r):
            blockers.append("PATH_INVARIANT_DRIFT:gross_r")

    for item in ordered:
        if not all(math.isfinite(float(value)) for value in (item.gross_r, item.cost_r, item.net_r)):
            blockers.append(f"NON_FINITE_R:{item.cost_model}")
            continue
        if not _close(item.net_r, item.gross_r - item.cost_r):
            blockers.append(f"NET_R_IDENTITY_DRIFT:{item.cost_model}")
        if item.cost_r < -_TOLERANCE:
            blockers.append(f"NEGATIVE_COST_R:{item.cost_model}")

    normalized_costs = tuple(item.cost_r / item.cost_multiplier for item in ordered)
    if any(not _close(value, normalized_costs[0]) for value in normalized_costs[1:]):
        blockers.append("COST_SCALING_DRIFT")

    for left, right in zip(ordered[:-1], ordered[1:], strict=True):
        if right.cost_r + _TOLERANCE < left.cost_r:
            blockers.append(f"COST_R_DECREASES:{left.cost_model}->{right.cost_model}")
        if right.net_r > left.net_r + _TOLERANCE:
            blockers.append(f"NET_R_IMPROVES_WITH_COST:{left.cost_model}->{right.cost_model}")

    unique_blockers = tuple(dict.fromkeys(blockers))
    state = CostConsistencyState.FAIL if unique_blockers else CostConsistencyState.PASS
    identity = {
        "window_number": window_number,
        "cost_result_fingerprints": tuple(item.result_fingerprint for item in ordered),
        "blockers": unique_blockers,
        "state": state.value,
    }
    return Cand001OosWindowCostConsistency(
        window_number=window_number,
        cost_result_fingerprints=identity["cost_result_fingerprints"],
        blockers=unique_blockers,
        state=state,
        audit_fingerprint=stable_fingerprint(identity),
    )


def _close(left: float, right: float) -> bool:
    return math.isclose(float(left), float(right), rel_tol=1e-10, abs_tol=_TOLERANCE)


def _assert_sha256(value: str, *, field: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{field} must be sha256")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field} must be hexadecimal") from exc
