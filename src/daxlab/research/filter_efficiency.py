from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Sequence

import numpy as np


def _profit_factor(values: np.ndarray) -> float | None:
    if values.size == 0:
        return None
    gross_profit = float(values[values > 0.0].sum())
    gross_loss = float(-values[values < 0.0].sum())
    if gross_loss == 0.0:
        if gross_profit > 0.0:
            return math.inf
        return None
    return gross_profit / gross_loss


def _max_drawdown_r(values: np.ndarray) -> float:
    if values.size == 0:
        return 0.0
    equity = np.concatenate(([0.0], np.cumsum(values, dtype=float)))
    peaks = np.maximum.accumulate(equity)
    return float(np.max(peaks - equity))


def _json_metric(value: float | None) -> float | str | None:
    if value is None:
        return None
    if math.isinf(value):
        return "INF"
    return float(value)


@dataclass(frozen=True)
class FilterEfficiencyDiagnostic:
    filter_id: str
    baseline_trades: int
    kept_trades: int
    removed_trades: int
    trade_survival_ratio: float
    baseline_total_r: float
    filtered_total_r: float
    delta_total_r: float
    baseline_expectancy_r: float
    filtered_expectancy_r: float | None
    delta_expectancy_r: float | None
    baseline_profit_factor: float | None
    filtered_profit_factor: float | None
    baseline_max_drawdown_r: float
    filtered_max_drawdown_r: float
    drawdown_change_r: float
    removed_winners: int
    removed_losers: int
    removed_flats: int
    missed_profit_r: float
    avoided_loss_r: float
    net_filter_value_r: float
    diagnostic_sha256: str

    def to_payload(self) -> dict[str, object]:
        return {
            "schema_version": "DAXLAB_FILTER_EFFICIENCY_DIAGNOSTIC_V1",
            "filter_id": self.filter_id,
            "baseline_trades": self.baseline_trades,
            "kept_trades": self.kept_trades,
            "removed_trades": self.removed_trades,
            "trade_survival_ratio": self.trade_survival_ratio,
            "baseline_total_r": self.baseline_total_r,
            "filtered_total_r": self.filtered_total_r,
            "delta_total_r": self.delta_total_r,
            "baseline_expectancy_r": self.baseline_expectancy_r,
            "filtered_expectancy_r": self.filtered_expectancy_r,
            "delta_expectancy_r": self.delta_expectancy_r,
            "baseline_profit_factor": _json_metric(self.baseline_profit_factor),
            "filtered_profit_factor": _json_metric(self.filtered_profit_factor),
            "baseline_max_drawdown_r": self.baseline_max_drawdown_r,
            "filtered_max_drawdown_r": self.filtered_max_drawdown_r,
            "drawdown_change_r": self.drawdown_change_r,
            "removed_winners": self.removed_winners,
            "removed_losers": self.removed_losers,
            "removed_flats": self.removed_flats,
            "missed_profit_r": self.missed_profit_r,
            "avoided_loss_r": self.avoided_loss_r,
            "net_filter_value_r": self.net_filter_value_r,
            "diagnostic_sha256": self.diagnostic_sha256,
            "automatic_keep_drop_decision": None,
            "execution_capability": "NONE",
            "order_execution_enabled": False,
        }


def evaluate_filter_efficiency(
    baseline_r: Sequence[float],
    keep_mask: Sequence[bool],
    *,
    filter_id: str,
) -> FilterEfficiencyDiagnostic:
    """Measure the marginal effect of one filter against the same trade ledger.

    ``baseline_r`` must already be in deterministic chronological trade order.
    ``keep_mask`` marks trades surviving the filter. The function intentionally
    does not apply an automatic keep/drop policy; it only exposes survival and
    economic consequences in R units.
    """
    label = filter_id.strip()
    if not label:
        raise ValueError("filter_id must be non-empty")

    baseline = np.asarray(tuple(float(value) for value in baseline_r), dtype=float)
    mask = np.asarray(tuple(bool(value) for value in keep_mask), dtype=bool)
    if baseline.ndim != 1 or baseline.size < 1:
        raise ValueError("baseline_r must contain at least one trade")
    if mask.shape != baseline.shape:
        raise ValueError("keep_mask length must match baseline_r")
    if not np.isfinite(baseline).all():
        raise ValueError("baseline_r must contain only finite values")

    kept = baseline[mask]
    removed = baseline[~mask]

    baseline_total = float(baseline.sum())
    filtered_total = float(kept.sum())
    delta_total = filtered_total - baseline_total
    baseline_expectancy = float(baseline.mean())
    filtered_expectancy = float(kept.mean()) if kept.size else None
    delta_expectancy = (
        filtered_expectancy - baseline_expectancy if filtered_expectancy is not None else None
    )
    baseline_pf = _profit_factor(baseline)
    filtered_pf = _profit_factor(kept)
    baseline_dd = _max_drawdown_r(baseline)
    filtered_dd = _max_drawdown_r(kept)

    removed_winners = int(np.count_nonzero(removed > 0.0))
    removed_losers = int(np.count_nonzero(removed < 0.0))
    removed_flats = int(np.count_nonzero(removed == 0.0))
    missed_profit = float(removed[removed > 0.0].sum())
    avoided_loss = float(-removed[removed < 0.0].sum())
    net_filter_value = avoided_loss - missed_profit

    identity = {
        "schema_version": "DAXLAB_FILTER_EFFICIENCY_DIAGNOSTIC_V1",
        "filter_id": label,
        "baseline_r": [float(value) for value in baseline],
        "keep_mask": [bool(value) for value in mask],
        "metrics": {
            "baseline_trades": int(baseline.size),
            "kept_trades": int(kept.size),
            "trade_survival_ratio": float(kept.size / baseline.size),
            "baseline_total_r": baseline_total,
            "filtered_total_r": filtered_total,
            "delta_total_r": delta_total,
            "baseline_expectancy_r": baseline_expectancy,
            "filtered_expectancy_r": filtered_expectancy,
            "baseline_profit_factor": _json_metric(baseline_pf),
            "filtered_profit_factor": _json_metric(filtered_pf),
            "baseline_max_drawdown_r": baseline_dd,
            "filtered_max_drawdown_r": filtered_dd,
            "missed_profit_r": missed_profit,
            "avoided_loss_r": avoided_loss,
            "net_filter_value_r": net_filter_value,
        },
    }
    diagnostic_sha256 = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    return FilterEfficiencyDiagnostic(
        filter_id=label,
        baseline_trades=int(baseline.size),
        kept_trades=int(kept.size),
        removed_trades=int(removed.size),
        trade_survival_ratio=float(kept.size / baseline.size),
        baseline_total_r=baseline_total,
        filtered_total_r=filtered_total,
        delta_total_r=delta_total,
        baseline_expectancy_r=baseline_expectancy,
        filtered_expectancy_r=filtered_expectancy,
        delta_expectancy_r=delta_expectancy,
        baseline_profit_factor=baseline_pf,
        filtered_profit_factor=filtered_pf,
        baseline_max_drawdown_r=baseline_dd,
        filtered_max_drawdown_r=filtered_dd,
        drawdown_change_r=filtered_dd - baseline_dd,
        removed_winners=removed_winners,
        removed_losers=removed_losers,
        removed_flats=removed_flats,
        missed_profit_r=missed_profit,
        avoided_loss_r=avoided_loss,
        net_filter_value_r=net_filter_value,
        diagnostic_sha256=diagnostic_sha256,
    )
