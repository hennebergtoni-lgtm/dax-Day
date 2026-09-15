"""Descriptive temporal OOS stability diagnostics for frozen CAND-001.

No composite score, economic pass threshold or promotion action exists here.
Diagnostics are available only after the cost-stress evidence-integrity audit
recomputes to PASS. Classical PBO/DSR are deliberately not applied to this
single frozen-candidate surface because no new multi-trial selection is present.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from statistics import mean, median

from daxlab.research.cand001_oos_aggregation import Cand001OosAggregation
from daxlab.research.cand001_oos_cost_consistency import (
    Cand001OosCostConsistencyAudit,
    CostConsistencyState,
    audit_cand001_oos_cost_consistency,
)
from daxlab.research.cand001_oos_measurement_runner import (
    Cand001OosMeasurement,
    Cand001OosMeasurementBundle,
)
from daxlab.research.cand001_oos_walk_forward import ECONOMIC_CLAIM, EVIDENCE_CLASS
from daxlab.runtime.decision import stable_fingerprint


CAND001_OOS_STABILITY_SCHEMA = "DAXLAB_CAND001_OOS_STABILITY_V1"


@dataclass(frozen=True, slots=True)
class Cand001OosCostStability:
    cost_model: str
    cost_multiplier: float
    window_count: int
    window_result_fingerprints: tuple[str, ...]
    total_net_r: float
    mean_window_net_r: float
    median_window_net_r: float
    positive_window_rate: float
    negative_window_rate: float
    flat_window_rate: float
    zero_trade_windows: int
    mean_completed_trades_per_window: float
    median_completed_trades_per_window: float
    longest_positive_window_streak: int
    longest_negative_window_streak: int
    cumulative_window_net_r_max_drawdown: float
    first_half_windows: int
    second_half_windows: int
    first_half_total_net_r: float
    second_half_total_net_r: float
    first_half_trades: int
    second_half_trades: int
    second_minus_first_mean_window_net_r: float
    second_minus_first_trades_per_window: float
    window_sequence_fingerprint: str
    report_fingerprint: str

    def __post_init__(self) -> None:
        if not self.cost_model or self.cost_multiplier <= 0 or self.window_count <= 0:
            raise ValueError("invalid OOS stability cost identity")
        if len(self.window_result_fingerprints) != self.window_count:
            raise ValueError("OOS stability result fingerprints must cover every window")
        for index, value in enumerate(self.window_result_fingerprints, start=1):
            _assert_sha256(value, field=f"window_result_fingerprints[{index}]")
        for field, value in (
            ("window_sequence_fingerprint", self.window_sequence_fingerprint),
            ("report_fingerprint", self.report_fingerprint),
        ):
            _assert_sha256(value, field=field)
        if not 0 <= self.zero_trade_windows <= self.window_count:
            raise ValueError("zero_trade_windows out of range")
        for rate in (
            self.positive_window_rate,
            self.negative_window_rate,
            self.flat_window_rate,
        ):
            if not 0.0 <= rate <= 1.0:
                raise ValueError("window sign rate out of range")
        if abs(
            self.positive_window_rate
            + self.negative_window_rate
            + self.flat_window_rate
            - 1.0
        ) > 1e-12:
            raise ValueError("window sign rates must sum to one")
        if self.first_half_windows + self.second_half_windows != self.window_count:
            raise ValueError("temporal halves must cover all windows")

    def to_payload(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class Cand001OosStabilityDiagnostics:
    schema_version: str
    source_bundle_fingerprint: str
    source_aggregation_fingerprint: str
    source_cost_consistency_fingerprint: str
    cost_reports: tuple[Cand001OosCostStability, ...]
    diagnostics_fingerprint: str
    evidence_class: str = EVIDENCE_CLASS
    economic_claim: str = ECONOMIC_CLAIM
    descriptive_only: bool = True
    composite_score: None = None
    automatic_promotion: bool = False
    multiple_testing_policy: str = (
        "PBO_DSR_NOT_APPLIED_SINGLE_FROZEN_CANDIDATE_NO_NEW_TRIAL_SELECTION"
    )
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != CAND001_OOS_STABILITY_SCHEMA:
            raise ValueError("unsupported CAND-001 OOS stability schema")
        for field, value in (
            ("source_bundle_fingerprint", self.source_bundle_fingerprint),
            ("source_aggregation_fingerprint", self.source_aggregation_fingerprint),
            ("source_cost_consistency_fingerprint", self.source_cost_consistency_fingerprint),
            ("diagnostics_fingerprint", self.diagnostics_fingerprint),
        ):
            _assert_sha256(value, field=field)
        if not self.cost_reports:
            raise ValueError("OOS stability requires cost reports")
        if not self.descriptive_only or self.composite_score is not None:
            raise ValueError("OOS stability must remain descriptive without composite score")
        if self.automatic_promotion:
            raise ValueError("OOS stability cannot auto-promote a candidate")
        if self.execution_capability != "NONE" or self.order_execution_enabled:
            raise ValueError("OOS stability cannot authorize execution")

    def to_payload(self) -> dict[str, object]:
        payload = asdict(self)
        payload["cost_reports"] = [item.to_payload() for item in self.cost_reports]
        return payload


def build_cand001_oos_stability_diagnostics(
    measurement: Cand001OosMeasurementBundle,
    aggregation: Cand001OosAggregation,
    cost_consistency: Cand001OosCostConsistencyAudit,
) -> Cand001OosStabilityDiagnostics:
    """Build threshold-free temporal stability diagnostics from verified OOS evidence."""
    canonical_audit = audit_cand001_oos_cost_consistency(measurement, aggregation)
    if cost_consistency != canonical_audit:
        raise ValueError("cost-consistency evidence is not canonical for the OOS source")
    if canonical_audit.state is not CostConsistencyState.PASS:
        raise ValueError("OOS stability requires PASS cost-consistency evidence")

    by_cost: dict[str, list[Cand001OosMeasurement]] = {}
    multiplier: dict[str, float] = {}
    for item in measurement.measurements:
        by_cost.setdefault(item.cost_model, []).append(item)
        multiplier[item.cost_model] = item.cost_multiplier

    reports = tuple(
        _build_cost_report(
            cost_model,
            multiplier[cost_model],
            tuple(sorted(items, key=lambda item: item.window_number)),
        )
        for cost_model, items in sorted(
            by_cost.items(), key=lambda item: multiplier[item[0]]
        )
    )
    identity = {
        "schema_version": CAND001_OOS_STABILITY_SCHEMA,
        "source_bundle_fingerprint": measurement.bundle_fingerprint,
        "source_aggregation_fingerprint": aggregation.aggregation_fingerprint,
        "source_cost_consistency_fingerprint": canonical_audit.audit_fingerprint,
        "cost_report_fingerprints": tuple(item.report_fingerprint for item in reports),
        "descriptive_only": True,
        "composite_score": None,
        "automatic_promotion": False,
        "multiple_testing_policy": (
            "PBO_DSR_NOT_APPLIED_SINGLE_FROZEN_CANDIDATE_NO_NEW_TRIAL_SELECTION"
        ),
        "execution_capability": "NONE",
        "order_execution_enabled": False,
    }
    return Cand001OosStabilityDiagnostics(
        schema_version=CAND001_OOS_STABILITY_SCHEMA,
        source_bundle_fingerprint=measurement.bundle_fingerprint,
        source_aggregation_fingerprint=aggregation.aggregation_fingerprint,
        source_cost_consistency_fingerprint=canonical_audit.audit_fingerprint,
        cost_reports=reports,
        diagnostics_fingerprint=stable_fingerprint(identity),
    )


def _build_cost_report(
    cost_model: str,
    cost_multiplier: float,
    items: tuple[Cand001OosMeasurement, ...],
) -> Cand001OosCostStability:
    if not items:
        raise ValueError("cost stability requires at least one window")
    expected = tuple(range(1, len(items) + 1))
    if tuple(item.window_number for item in items) != expected:
        raise ValueError("cost stability windows must be contiguous and start at one")

    net = tuple(float(item.net_r) for item in items)
    trades = tuple(int(item.completed_trades) for item in items)
    positive = sum(value > 0.0 for value in net)
    negative = sum(value < 0.0 for value in net)
    flat = len(net) - positive - negative
    split = len(items) // 2
    first_items = items[:split]
    second_items = items[split:]
    if not first_items or not second_items:
        raise ValueError("temporal stability requires at least two OOS windows")

    first_net = float(sum(item.net_r for item in first_items))
    second_net = float(sum(item.net_r for item in second_items))
    first_trades = sum(item.completed_trades for item in first_items)
    second_trades = sum(item.completed_trades for item in second_items)
    sequence_payload = tuple(
        {
            "window_number": item.window_number,
            "result_fingerprint": item.result_fingerprint,
            "net_r": float(item.net_r),
            "completed_trades": int(item.completed_trades),
        }
        for item in items
    )
    sequence_fingerprint = stable_fingerprint(sequence_payload)
    values = {
        "cost_model": cost_model,
        "cost_multiplier": cost_multiplier,
        "window_count": len(items),
        "window_result_fingerprints": tuple(item.result_fingerprint for item in items),
        "total_net_r": float(sum(net)),
        "mean_window_net_r": float(mean(net)),
        "median_window_net_r": float(median(net)),
        "positive_window_rate": positive / len(items),
        "negative_window_rate": negative / len(items),
        "flat_window_rate": flat / len(items),
        "zero_trade_windows": sum(value == 0 for value in trades),
        "mean_completed_trades_per_window": float(mean(trades)),
        "median_completed_trades_per_window": float(median(trades)),
        "longest_positive_window_streak": _longest_streak(net, 1),
        "longest_negative_window_streak": _longest_streak(net, -1),
        "cumulative_window_net_r_max_drawdown": _max_drawdown(net),
        "first_half_windows": len(first_items),
        "second_half_windows": len(second_items),
        "first_half_total_net_r": first_net,
        "second_half_total_net_r": second_net,
        "first_half_trades": first_trades,
        "second_half_trades": second_trades,
        "second_minus_first_mean_window_net_r": (
            second_net / len(second_items) - first_net / len(first_items)
        ),
        "second_minus_first_trades_per_window": (
            second_trades / len(second_items) - first_trades / len(first_items)
        ),
        "window_sequence_fingerprint": sequence_fingerprint,
    }
    return Cand001OosCostStability(
        **values,
        report_fingerprint=stable_fingerprint(values),
    )


def _longest_streak(values: tuple[float, ...], sign: int) -> int:
    longest = 0
    current = 0
    for value in values:
        matches = value > 0.0 if sign > 0 else value < 0.0
        if matches:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest


def _max_drawdown(values: tuple[float, ...]) -> float:
    cumulative = 0.0
    peak = 0.0
    max_drawdown = 0.0
    for value in values:
        cumulative += float(value)
        peak = max(peak, cumulative)
        max_drawdown = max(max_drawdown, peak - cumulative)
    return float(max_drawdown)


def _assert_sha256(value: str, *, field: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{field} must be sha256")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field} must be hexadecimal") from exc
