from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Sequence

import numpy as np

from daxlab.research.filter_efficiency import (
    FilterEfficiencyDiagnostic,
    evaluate_filter_efficiency,
)


@dataclass(frozen=True)
class FilterStackStage:
    filter_id: str
    active_effect_count: int
    redundant_in_stack: bool
    cumulative_kept_trades: int
    cumulative_survival_ratio: float
    incremental: FilterEfficiencyDiagnostic
    cumulative_total_r: float
    cumulative_delta_r_vs_baseline: float

    def to_payload(self) -> dict[str, object]:
        return {
            "filter_id": self.filter_id,
            "active_effect_count": self.active_effect_count,
            "redundant_in_stack": self.redundant_in_stack,
            "cumulative_kept_trades": self.cumulative_kept_trades,
            "cumulative_survival_ratio": self.cumulative_survival_ratio,
            "incremental": self.incremental.to_payload(),
            "cumulative_total_r": self.cumulative_total_r,
            "cumulative_delta_r_vs_baseline": self.cumulative_delta_r_vs_baseline,
        }


@dataclass(frozen=True)
class FilterStackAblation:
    baseline_trades: int
    baseline_total_r: float
    stages: tuple[FilterStackStage, ...]
    final_kept_trades: int
    final_survival_ratio: float
    final_total_r: float
    final_delta_r_vs_baseline: float
    all_trades_blocked: bool
    stack_sha256: str

    def to_payload(self) -> dict[str, object]:
        return {
            "schema_version": "DAXLAB_FILTER_STACK_ABLATION_V1",
            "baseline_trades": self.baseline_trades,
            "baseline_total_r": self.baseline_total_r,
            "stages": [stage.to_payload() for stage in self.stages],
            "final_kept_trades": self.final_kept_trades,
            "final_survival_ratio": self.final_survival_ratio,
            "final_total_r": self.final_total_r,
            "final_delta_r_vs_baseline": self.final_delta_r_vs_baseline,
            "all_trades_blocked": self.all_trades_blocked,
            "stack_sha256": self.stack_sha256,
            "automatic_keep_drop_decision": None,
            "execution_capability": "NONE",
            "order_execution_enabled": False,
        }


def evaluate_filter_stack(
    baseline_r: Sequence[float],
    filters: Sequence[tuple[str, Sequence[bool]]],
) -> FilterStackAblation:
    """Evaluate filters incrementally in the exact supplied stack order.

    Every filter mask is expressed against the original baseline trade ledger.
    The incremental effect is evaluated only on trades still alive before the
    stage. This exposes redundant filters that do not alter any active decision.
    """
    baseline = np.asarray(tuple(float(value) for value in baseline_r), dtype=float)
    if baseline.ndim != 1 or baseline.size < 1:
        raise ValueError("baseline_r must contain at least one trade")
    if not np.isfinite(baseline).all():
        raise ValueError("baseline_r must contain only finite values")
    if not filters:
        raise ValueError("at least one filter stage is required")

    labels: set[str] = set()
    normalized: list[tuple[str, np.ndarray]] = []
    for raw_label, raw_mask in filters:
        label = raw_label.strip()
        if not label:
            raise ValueError("filter_id must be non-empty")
        if label in labels:
            raise ValueError(f"duplicate filter_id: {label}")
        labels.add(label)
        mask = np.asarray(tuple(bool(value) for value in raw_mask), dtype=bool)
        if mask.shape != baseline.shape:
            raise ValueError("every filter mask must match baseline_r length")
        normalized.append((label, mask))

    baseline_total = float(baseline.sum())
    cumulative = np.ones(baseline.size, dtype=bool)
    stages: list[FilterStackStage] = []

    for label, raw_mask in normalized:
        active_indices = np.flatnonzero(cumulative)
        active_values = baseline[active_indices]
        active_keep = raw_mask[active_indices]
        active_effect_count = int(np.count_nonzero(~active_keep))
        incremental = evaluate_filter_efficiency(
            active_values,
            active_keep,
            filter_id=label,
        )
        cumulative = np.logical_and(cumulative, raw_mask)
        cumulative_values = baseline[cumulative]
        cumulative_total = float(cumulative_values.sum())
        stages.append(
            FilterStackStage(
                filter_id=label,
                active_effect_count=active_effect_count,
                redundant_in_stack=active_effect_count == 0,
                cumulative_kept_trades=int(cumulative_values.size),
                cumulative_survival_ratio=float(cumulative_values.size / baseline.size),
                incremental=incremental,
                cumulative_total_r=cumulative_total,
                cumulative_delta_r_vs_baseline=cumulative_total - baseline_total,
            )
        )

    final_values = baseline[cumulative]
    identity = {
        "schema_version": "DAXLAB_FILTER_STACK_ABLATION_V1",
        "baseline_r": [float(value) for value in baseline],
        "filters": [
            {"filter_id": label, "keep_mask": [bool(value) for value in mask]}
            for label, mask in normalized
        ],
        "stage_diagnostic_hashes": [stage.incremental.diagnostic_sha256 for stage in stages],
    }
    stack_sha256 = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    return FilterStackAblation(
        baseline_trades=int(baseline.size),
        baseline_total_r=baseline_total,
        stages=tuple(stages),
        final_kept_trades=int(final_values.size),
        final_survival_ratio=float(final_values.size / baseline.size),
        final_total_r=float(final_values.sum()),
        final_delta_r_vs_baseline=float(final_values.sum()) - baseline_total,
        all_trades_blocked=final_values.size == 0,
        stack_sha256=stack_sha256,
    )
