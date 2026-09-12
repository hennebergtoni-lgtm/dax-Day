"""Deterministic aggregation for frozen CAND-001 OOS/WF measurements.

Aggregation is measurement-only: no tuning, ranking, candidate selection or
execution authorization is performed. The summary binds both the Step-2105
bundle identity and the exact serialized measurement payload consumed here.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from statistics import median

from daxlab.research.cand001_oos_measurement_runner import (
    Cand001OosMeasurement,
    Cand001OosMeasurementBundle,
)
from daxlab.research.cand001_oos_walk_forward import ECONOMIC_CLAIM, EVIDENCE_CLASS
from daxlab.runtime.decision import stable_fingerprint


CAND001_OOS_AGGREGATION_SCHEMA = "DAXLAB_CAND001_OOS_WF_AGGREGATION_V1"


@dataclass(frozen=True, slots=True)
class Cand001OosCostSummary:
    cost_model: str
    cost_multiplier: float
    window_count: int
    completed_trades: int
    total_gross_r: float
    total_cost_r: float
    total_net_r: float
    positive_windows: int
    negative_windows: int
    flat_windows: int
    median_window_net_r: float
    median_defined_window_profit_factor: float | None
    defined_window_profit_factor_count: int
    undefined_window_profit_factor_count: int
    worst_window_number: int
    worst_window_net_r: float
    worst_window_max_drawdown_r: float
    max_window_drawdown_r: float
    open_trade_at_end_windows: int
    aggregate_profit_factor: float | None
    aggregate_profit_factor_complete: bool
    summary_fingerprint: str
    evidence_class: str = EVIDENCE_CLASS
    economic_claim: str = ECONOMIC_CLAIM
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        if not self.cost_model or self.cost_multiplier <= 0 or self.window_count <= 0:
            raise ValueError("invalid OOS cost summary identity/counts")
        if self.completed_trades < 0:
            raise ValueError("completed_trades must be non-negative")
        if self.positive_windows + self.negative_windows + self.flat_windows != self.window_count:
            raise ValueError("window sign counts do not cover all windows")
        if (
            self.defined_window_profit_factor_count
            + self.undefined_window_profit_factor_count
            != self.window_count
        ):
            raise ValueError("window PF counts do not cover all windows")
        if self.worst_window_number <= 0:
            raise ValueError("worst_window_number must be positive")
        _assert_sha256(self.summary_fingerprint, field="summary_fingerprint")
        if self.execution_capability != "NONE" or self.order_execution_enabled:
            raise ValueError("OOS aggregation cannot authorize execution")

    def to_payload(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class Cand001OosCostDegradation:
    from_cost_model: str
    to_cost_model: str
    from_multiplier: float
    to_multiplier: float
    delta_total_net_r: float
    delta_median_window_net_r: float
    delta_positive_windows: int
    delta_completed_trades: int
    degradation_fingerprint: str

    def __post_init__(self) -> None:
        if not self.from_cost_model or not self.to_cost_model:
            raise ValueError("degradation cost models must be non-empty")
        if not (0 < self.from_multiplier < self.to_multiplier):
            raise ValueError("degradation multipliers must increase")
        _assert_sha256(self.degradation_fingerprint, field="degradation_fingerprint")

    def to_payload(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class Cand001OosAggregation:
    schema_version: str
    source_bundle_fingerprint: str
    source_payload_fingerprint: str
    dataset_fingerprint: str
    contract_fingerprint: str
    candidate_id: str
    config_fingerprint: str
    window_count: int
    measurement_count: int
    cost_summaries: tuple[Cand001OosCostSummary, ...]
    degradations: tuple[Cand001OosCostDegradation, ...]
    aggregation_fingerprint: str
    evidence_class: str = EVIDENCE_CLASS
    economic_claim: str = ECONOMIC_CLAIM
    selection_policy: str = "FROZEN_PREDECLARED_CANDIDATE_NO_TUNING"
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != CAND001_OOS_AGGREGATION_SCHEMA:
            raise ValueError("unsupported CAND-001 OOS aggregation schema")
        for field, value in (
            ("source_bundle_fingerprint", self.source_bundle_fingerprint),
            ("source_payload_fingerprint", self.source_payload_fingerprint),
            ("dataset_fingerprint", self.dataset_fingerprint),
            ("contract_fingerprint", self.contract_fingerprint),
            ("config_fingerprint", self.config_fingerprint),
            ("aggregation_fingerprint", self.aggregation_fingerprint),
        ):
            _assert_sha256(value, field=field)
        if self.window_count <= 0 or self.measurement_count <= 0:
            raise ValueError("OOS aggregation counts must be positive")
        if len(self.cost_summaries) <= 0:
            raise ValueError("OOS aggregation requires cost summaries")
        if self.execution_capability != "NONE" or self.order_execution_enabled:
            raise ValueError("OOS aggregation cannot authorize execution")

    def to_payload(self) -> dict[str, object]:
        payload = asdict(self)
        payload["cost_summaries"] = [item.to_payload() for item in self.cost_summaries]
        payload["degradations"] = [item.to_payload() for item in self.degradations]
        return payload


def aggregate_cand001_oos(
    bundle: Cand001OosMeasurementBundle,
) -> Cand001OosAggregation:
    """Aggregate one complete frozen OOS/WF measurement bundle deterministically."""
    if bundle.execution_capability != "NONE" or bundle.order_execution_enabled:
        raise ValueError("source OOS bundle is not execution-safe")
    if bundle.measurement_count != bundle.window_count * bundle.cost_model_count:
        raise ValueError("source OOS bundle is incomplete")

    source_payload_fingerprint = stable_fingerprint(bundle.to_payload())
    by_cost: dict[str, list[Cand001OosMeasurement]] = {}
    multiplier_by_cost: dict[str, float] = {}
    expected_windows = set(range(1, bundle.window_count + 1))
    for item in bundle.measurements:
        by_cost.setdefault(item.cost_model, []).append(item)
        prior = multiplier_by_cost.setdefault(item.cost_model, item.cost_multiplier)
        if prior != item.cost_multiplier:
            raise ValueError("cost multiplier drift inside OOS bundle")

    if len(by_cost) != bundle.cost_model_count:
        raise ValueError("source OOS bundle cost-model count drift")

    summaries: list[Cand001OosCostSummary] = []
    for cost_model, multiplier in sorted(
        multiplier_by_cost.items(), key=lambda item: item[1]
    ):
        items = tuple(sorted(by_cost[cost_model], key=lambda item: item.window_number))
        if {item.window_number for item in items} != expected_windows:
            raise ValueError(f"cost model {cost_model} does not cover every OOS window")
        summaries.append(_aggregate_cost(cost_model, multiplier, items))

    degradations = tuple(
        _degradation(left, right)
        for left, right in zip(summaries[:-1], summaries[1:], strict=True)
    )
    summary_tuple = tuple(summaries)
    aggregate_identity = {
        "schema_version": CAND001_OOS_AGGREGATION_SCHEMA,
        "source_bundle_fingerprint": bundle.bundle_fingerprint,
        "source_payload_fingerprint": source_payload_fingerprint,
        "dataset_fingerprint": bundle.dataset_fingerprint,
        "contract_fingerprint": bundle.contract_fingerprint,
        "candidate_id": bundle.candidate_id,
        "config_fingerprint": bundle.config_fingerprint,
        "window_count": bundle.window_count,
        "measurement_count": bundle.measurement_count,
        "cost_summary_fingerprints": tuple(
            item.summary_fingerprint for item in summary_tuple
        ),
        "degradation_fingerprints": tuple(
            item.degradation_fingerprint for item in degradations
        ),
        "evidence_class": EVIDENCE_CLASS,
        "economic_claim": ECONOMIC_CLAIM,
    }
    return Cand001OosAggregation(
        schema_version=CAND001_OOS_AGGREGATION_SCHEMA,
        source_bundle_fingerprint=bundle.bundle_fingerprint,
        source_payload_fingerprint=source_payload_fingerprint,
        dataset_fingerprint=bundle.dataset_fingerprint,
        contract_fingerprint=bundle.contract_fingerprint,
        candidate_id=bundle.candidate_id,
        config_fingerprint=bundle.config_fingerprint,
        window_count=bundle.window_count,
        measurement_count=bundle.measurement_count,
        cost_summaries=summary_tuple,
        degradations=degradations,
        aggregation_fingerprint=stable_fingerprint(aggregate_identity),
    )


def _aggregate_cost(
    cost_model: str,
    multiplier: float,
    items: tuple[Cand001OosMeasurement, ...],
) -> Cand001OosCostSummary:
    net_values = tuple(float(item.net_r) for item in items)
    pf_values = tuple(
        float(item.profit_factor)
        for item in items
        if item.profit_factor is not None
    )
    worst = min(items, key=lambda item: (item.net_r, item.window_number))

    positive_leg = 0.0
    negative_leg = 0.0
    pf_complete = True
    for item in items:
        legs = _reconstruct_net_legs(item)
        if legs is None:
            pf_complete = False
            continue
        positive_leg += legs[0]
        negative_leg += legs[1]

    aggregate_pf = None
    if pf_complete and negative_leg > 0.0:
        aggregate_pf = positive_leg / negative_leg

    identity = {
        "cost_model": cost_model,
        "cost_multiplier": multiplier,
        "window_result_fingerprints": tuple(item.result_fingerprint for item in items),
        "completed_trades": sum(item.completed_trades for item in items),
        "total_gross_r": float(sum(item.gross_r for item in items)),
        "total_cost_r": float(sum(item.cost_r for item in items)),
        "total_net_r": float(sum(net_values)),
        "positive_windows": sum(value > 0.0 for value in net_values),
        "negative_windows": sum(value < 0.0 for value in net_values),
        "flat_windows": sum(value == 0.0 for value in net_values),
        "median_window_net_r": float(median(net_values)),
        "median_defined_window_profit_factor": (
            None if not pf_values else float(median(pf_values))
        ),
        "defined_window_profit_factor_count": len(pf_values),
        "undefined_window_profit_factor_count": len(items) - len(pf_values),
        "worst_window_number": worst.window_number,
        "worst_window_net_r": float(worst.net_r),
        "worst_window_max_drawdown_r": float(worst.max_drawdown_r),
        "max_window_drawdown_r": float(max(item.max_drawdown_r for item in items)),
        "open_trade_at_end_windows": sum(item.open_trade_at_end for item in items),
        "aggregate_profit_factor": (
            None if aggregate_pf is None else float(aggregate_pf)
        ),
        "aggregate_profit_factor_complete": pf_complete,
    }
    return Cand001OosCostSummary(
        **identity,
        summary_fingerprint=stable_fingerprint(identity),
    )


def _reconstruct_net_legs(
    item: Cand001OosMeasurement,
) -> tuple[float, float] | None:
    """Recover positive/negative net-R legs where window PF makes them identifiable."""
    net = float(item.net_r)
    pf = item.profit_factor
    tolerance = 1e-12

    if item.completed_trades == 0:
        if abs(net) > tolerance:
            raise ValueError("zero-trade OOS window cannot carry non-zero net R")
        return 0.0, 0.0

    if pf is None:
        if net < -tolerance:
            raise ValueError("undefined PF with negative net R is inconsistent")
        return max(net, 0.0), 0.0

    pf_value = float(pf)
    if pf_value < 0.0:
        raise ValueError("window profit factor cannot be negative")
    if abs(pf_value - 1.0) <= tolerance:
        if abs(net) > tolerance:
            raise ValueError("PF=1 requires zero net R")
        return None

    negative = net / (pf_value - 1.0)
    positive = pf_value * negative
    if negative < -tolerance or positive < -tolerance:
        raise ValueError("window PF/net-R combination is inconsistent")
    return max(float(positive), 0.0), max(float(negative), 0.0)


def _degradation(
    left: Cand001OosCostSummary,
    right: Cand001OosCostSummary,
) -> Cand001OosCostDegradation:
    identity = {
        "from_cost_model": left.cost_model,
        "to_cost_model": right.cost_model,
        "from_multiplier": left.cost_multiplier,
        "to_multiplier": right.cost_multiplier,
        "delta_total_net_r": float(right.total_net_r - left.total_net_r),
        "delta_median_window_net_r": float(
            right.median_window_net_r - left.median_window_net_r
        ),
        "delta_positive_windows": right.positive_windows - left.positive_windows,
        "delta_completed_trades": right.completed_trades - left.completed_trades,
        "from_summary_fingerprint": left.summary_fingerprint,
        "to_summary_fingerprint": right.summary_fingerprint,
    }
    return Cand001OosCostDegradation(
        from_cost_model=left.cost_model,
        to_cost_model=right.cost_model,
        from_multiplier=left.cost_multiplier,
        to_multiplier=right.cost_multiplier,
        delta_total_net_r=float(right.total_net_r - left.total_net_r),
        delta_median_window_net_r=float(
            right.median_window_net_r - left.median_window_net_r
        ),
        delta_positive_windows=right.positive_windows - left.positive_windows,
        delta_completed_trades=right.completed_trades - left.completed_trades,
        degradation_fingerprint=stable_fingerprint(identity),
    )


def _assert_sha256(value: str, *, field: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{field} must be sha256")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field} must be hexadecimal") from exc
