"""Operator-friendly summary over weekly SHADOW setup attribution.

Descriptive only: the summary exposes leaders/laggards by observed R but never selects,
promotes, sizes or executes a setup.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Iterable

from daxlab.research.weekly_setup_attribution import WeeklySetupAttribution


@dataclass(frozen=True, slots=True)
class WeeklyAttributionSummary:
    week_key: str
    groups: int
    trades: int
    net_r: float
    best_observed_group: str | None
    best_observed_group_net_r: float | None
    worst_observed_group: str | None
    worst_observed_group_net_r: float | None
    source_report_sha256_order: tuple[str, ...]
    summary_sha256: str
    descriptive_only: bool = True
    statistical_significance_claimed: bool = False
    automatic_selection: bool = False
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False


def _label(item: WeeklySetupAttribution) -> str:
    return f"{item.regime} / {item.structure} / {item.setup}"


def build_weekly_attribution_summary(
    reports: Iterable[WeeklySetupAttribution],
) -> tuple[WeeklyAttributionSummary, ...]:
    items = tuple(reports)
    for item in items:
        if item.execution_capability != "NONE" or item.order_execution_enabled:
            raise ValueError("weekly attribution must preserve NO_ORDER")
        if not item.descriptive_only or item.automatic_selection:
            raise ValueError("weekly attribution must remain descriptive only")

    weeks: dict[str, list[WeeklySetupAttribution]] = {}
    for item in items:
        weeks.setdefault(item.week_key, []).append(item)

    output: list[WeeklyAttributionSummary] = []
    for week_key in sorted(weeks):
        group = sorted(
            weeks[week_key],
            key=lambda item: (item.regime, item.structure, item.setup, item.report_sha256),
        )
        trades = sum(item.trades for item in group)
        net_r = float(sum(item.net_r for item in group))
        best = max(group, key=lambda item: (item.net_r, item.average_r_per_trade, _label(item)))
        worst = min(group, key=lambda item: (item.net_r, item.average_r_per_trade, _label(item)))
        shas = tuple(item.report_sha256 for item in group)
        identity = {
            "schema_version": "DAXLAB_WEEKLY_ATTRIBUTION_SUMMARY_V1",
            "week_key": week_key,
            "source_report_sha256_order": list(shas),
        }
        digest = hashlib.sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        output.append(
            WeeklyAttributionSummary(
                week_key=week_key,
                groups=len(group),
                trades=trades,
                net_r=net_r,
                best_observed_group=_label(best),
                best_observed_group_net_r=best.net_r,
                worst_observed_group=_label(worst),
                worst_observed_group_net_r=worst.net_r,
                source_report_sha256_order=shas,
                summary_sha256=digest,
            )
        )
    return tuple(output)
