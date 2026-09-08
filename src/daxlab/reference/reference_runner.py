"""Reproducible runner core for the frozen V11.2 reference measurement."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd

from daxlab.contracts import REFERENCE_COSTS, REFERENCE_WF
from daxlab.research.walk_forward import build_walk_forwards


@dataclass(frozen=True, slots=True)
class CandidateScore:
    variant_index: int
    params: Any
    normal: dict[str, Any]
    stress_15: dict[str, Any]
    stress_20: dict[str, Any]
    score: float
    stress_ok: bool


def _empty_metrics(engine: Any) -> dict[str, Any]:
    return dict(engine.metrics(None))


def score_candidate(engine: Any, train_days: tuple[object, ...], variant_index: int, params: Any) -> CandidateScore:
    """Apply the frozen V11.2 train-selection rule without altering strategy semantics."""
    normal = dict(engine.cached_metrics(train_days, params, "normal"))
    stress_15 = _empty_metrics(engine)
    stress_20 = _empty_metrics(engine)

    if normal["trades"] >= 12 and normal["avg_r"] > -0.03:
        stress_15 = dict(engine.cached_metrics(train_days, params, "stress_1.5x"))
        stress_20 = dict(engine.cached_metrics(train_days, params, "stress_2x"))

    trade_factor = min(normal["trades"], 50) / 50.0
    dd_penalty = abs(min(normal["max_dd_r"], 0.0))
    score = (
        1.6 * normal["avg_r"]
        + 0.45 * min(max(normal["pf"] - 1.0, -1.0), 2.0)
        + 0.10 * trade_factor
        - 0.035 * dd_penalty
    )

    stress_ok = bool(
        stress_15["trades"] >= 12
        and stress_20["trades"] >= 12
        and stress_15["pf"] >= 1.0
        and stress_20["pf"] >= 0.95
        and stress_20["avg_r"] >= -0.02
    )
    return CandidateScore(
        variant_index=variant_index,
        params=params,
        normal=normal,
        stress_15=stress_15,
        stress_20=stress_20,
        score=float(score),
        stress_ok=stress_ok,
    )


def select_variant(engine: Any, train_days: tuple[object, ...], grid: list[Any]) -> CandidateScore:
    """Select one V11.2 variant using the frozen clean train-ranking rule."""
    scored = [score_candidate(engine, train_days, i, p) for i, p in enumerate(grid, 1)]
    eligible = [row for row in scored if row.normal["trades"] >= 12]
    if not eligible:
        raise RuntimeError("no V11.2 variant has >=12 training trades")
    stress_eligible = [row for row in eligible if row.stress_ok]
    pool = stress_eligible or eligible
    return max(pool, key=lambda row: (row.score, row.normal["avg_r"], row.normal["pf"]))


def build_reference_windows(days: list[object]) -> list[Any]:
    """Build the canonical fixed rolling 45/20/20 V11.2 schedule."""
    windows = build_walk_forwards(days, REFERENCE_WF)
    if len(days) == 1673 and len(windows) != 81:
        raise RuntimeError(f"reference WF contract failed: expected 81, got {len(windows)}")
    return windows


def run_cached_reference(engine: Any, days: list[object]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run selection and OOS metrics after the exact engine FAST cache has been built."""
    grid = list(engine.grid())
    if len(grid) != 144:
        raise RuntimeError(f"reference grid contract failed: expected 144, got {len(grid)}")
    expected_costs = [model.name for model in REFERENCE_COSTS]
    if list(engine.COST_SCENARIOS) != expected_costs:
        raise RuntimeError("reference cost-model contract failed")

    metric_rows: list[dict[str, Any]] = []
    selected_rows: list[dict[str, Any]] = []
    for window in build_reference_windows(days):
        pick = select_variant(engine, window.train, grid)
        params_dict = asdict(pick.params)
        selected_rows.append(
            {
                "wf": window.number,
                "variant_index": pick.variant_index,
                "train_start": window.train[0],
                "train_end": window.train[-1],
                "oos_start": window.oos[0],
                "oos_end": window.oos[-1],
                "train_score": pick.score,
                "train_pf": pick.normal["pf"],
                "train_avg_r": pick.normal["avg_r"],
                "train_dd_r": pick.normal["max_dd_r"],
                "train_trades": pick.normal["trades"],
                "stress_ok": pick.stress_ok,
                **params_dict,
            }
        )
        for cost_name in expected_costs:
            metrics = dict(engine.cached_metrics(window.oos, pick.params, cost_name))
            metric_rows.append(
                {
                    "wf": window.number,
                    "cost": cost_name,
                    "variant_index": pick.variant_index,
                    **metrics,
                }
            )
    return pd.DataFrame(metric_rows), pd.DataFrame(selected_rows)


def aggregate_reference(wf_metrics: pd.DataFrame) -> dict[str, Any]:
    """Produce deterministic aggregate counts without using legacy values as targets."""
    out: dict[str, Any] = {"costs": {}}
    for cost_name in [model.name for model in REFERENCE_COSTS]:
        rows = wf_metrics[wf_metrics["cost"] == cost_name]
        out["costs"][cost_name] = {
            "oos_trades": int(rows["trades"].sum()),
            "oos_return_r": float(rows["return_r"].sum()),
            "positive_wfs": int((rows["return_r"] > 0).sum()),
            "negative_wfs": int((rows["return_r"] < 0).sum()),
            "flat_wfs": int((rows["return_r"] == 0).sum()),
        }
    return out
