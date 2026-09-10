"""Descriptive weekly SHADOW attribution by regime, structure and setup.

This is reporting only. It does not rank, score, select, promote, size or execute strategies.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
from typing import Iterable
from zoneinfo import ZoneInfo

from daxlab.research.dated_shadow_outcome import DatedShadowOutcome

_BERLIN = ZoneInfo("Europe/Berlin")


@dataclass(frozen=True, slots=True)
class WeeklySetupAttribution:
    week_key: str
    regime: str
    structure: str
    setup: str
    trades: int
    winning_trades: int
    losing_trades: int
    flat_trades: int
    net_r: float
    average_r_per_trade: float
    source_outcome_sha256_order: tuple[str, ...]
    report_sha256: str
    descriptive_only: bool = True
    automatic_selection: bool = False
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False


def _event_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("outcome event_time_utc must be timezone-aware")
    return parsed


def build_weekly_setup_attribution(
    outcomes: Iterable[DatedShadowOutcome],
) -> tuple[WeeklySetupAttribution, ...]:
    items = tuple(outcomes)
    if len({item.decision_id for item in items}) != len(items):
        raise ValueError("dated SHADOW outcomes must have unique decision_id values")
    for item in items:
        if item.execution_capability != "NONE" or item.order_execution_enabled:
            raise ValueError("dated SHADOW outcomes must preserve NO_ORDER")
        if not item.simulated_only or item.broker_balance:
            raise ValueError("attribution requires simulated-only SHADOW outcomes")

    ordered = sorted(items, key=lambda item: (_event_time(item.event_time_utc), item.decision_id))
    groups: dict[tuple[str, str, str, str], list[DatedShadowOutcome]] = {}
    for item in ordered:
        iso = _event_time(item.event_time_utc).astimezone(_BERLIN).isocalendar()
        key = (f"{iso.year}-W{iso.week:02d}", item.regime, item.structure, item.setup)
        groups.setdefault(key, []).append(item)

    reports: list[WeeklySetupAttribution] = []
    for (week_key, regime, structure, setup), group in groups.items():
        r_values = [float(item.r_result) for item in group]
        net_r = float(sum(r_values))
        shas = tuple(item.outcome_sha256 for item in group)
        identity = {
            "schema_version": "DAXLAB_WEEKLY_SETUP_ATTRIBUTION_V1",
            "week_key": week_key,
            "regime": regime,
            "structure": structure,
            "setup": setup,
            "source_outcome_sha256_order": list(shas),
        }
        digest = hashlib.sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        reports.append(
            WeeklySetupAttribution(
                week_key=week_key,
                regime=regime,
                structure=structure,
                setup=setup,
                trades=len(group),
                winning_trades=sum(value > 0.0 for value in r_values),
                losing_trades=sum(value < 0.0 for value in r_values),
                flat_trades=sum(value == 0.0 for value in r_values),
                net_r=net_r,
                average_r_per_trade=net_r / len(group),
                source_outcome_sha256_order=shas,
                report_sha256=digest,
            )
        )
    return tuple(reports)
