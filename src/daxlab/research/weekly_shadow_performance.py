"""Weekly SHADOW performance aggregation over dated outcome evidence.

Evidence timestamps remain UTC. ISO week assignment is derived in Europe/Berlin for the
operator view. Cash math delegates to the existing fixed-risk SHADOW cash ledger.
No broker balance, threshold, score, promotion or execution capability is introduced.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
from typing import Iterable
from zoneinfo import ZoneInfo

from daxlab.research.dated_shadow_outcome import DatedShadowOutcome
from daxlab.research.shadow_cash_ledger import ShadowCashLedger, simulate_fixed_risk_cash_ledger

_BERLIN = ZoneInfo("Europe/Berlin")


@dataclass(frozen=True, slots=True)
class WeeklyShadowPerformance:
    iso_year: int
    iso_week: int
    week_key: str
    trades: int
    winning_trades: int
    losing_trades: int
    flat_trades: int
    net_r: float
    average_r_per_trade: float | None
    cash_ledger: ShadowCashLedger
    source_outcome_sha256_order: tuple[str, ...]
    report_sha256: str
    timezone: str = "Europe/Berlin"
    simulated_only: bool = True
    broker_balance: bool = False
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def to_payload(self) -> dict[str, object]:
        return {
            "schema_version": "DAXLAB_WEEKLY_SHADOW_PERFORMANCE_V1",
            "iso_year": self.iso_year,
            "iso_week": self.iso_week,
            "week_key": self.week_key,
            "timezone": self.timezone,
            "trades": self.trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "flat_trades": self.flat_trades,
            "net_r": self.net_r,
            "average_r_per_trade": self.average_r_per_trade,
            "cash_ledger": self.cash_ledger.to_payload(),
            "source_outcome_sha256_order": list(self.source_outcome_sha256_order),
            "report_sha256": self.report_sha256,
            "simulated_only": self.simulated_only,
            "broker_balance": self.broker_balance,
            "execution_capability": self.execution_capability,
            "order_execution_enabled": self.order_execution_enabled,
        }


def _parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError("outcome event_time_utc must be timezone-aware")
    if parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 0:
        raise ValueError("outcome event_time_utc must carry UTC offset")
    return parsed


def build_weekly_shadow_performance(
    outcomes: Iterable[DatedShadowOutcome],
    *,
    starting_balance_eur: float,
    fixed_risk_eur: float,
) -> tuple[WeeklyShadowPerformance, ...]:
    """Aggregate chronological dated SHADOW outcomes into Europe/Berlin ISO weeks."""
    items = tuple(outcomes)
    if len({item.decision_id for item in items}) != len(items):
        raise ValueError("dated SHADOW outcomes must have unique decision_id values")
    for item in items:
        if item.execution_capability != "NONE" or item.order_execution_enabled:
            raise ValueError("dated SHADOW outcomes must preserve NO_ORDER")
        if not item.simulated_only or item.broker_balance:
            raise ValueError("weekly SHADOW performance requires simulated-only outcomes")

    chronological = sorted(items, key=lambda item: _parse_utc(item.event_time_utc))
    groups: dict[tuple[int, int], list[DatedShadowOutcome]] = {}
    for item in chronological:
        local = _parse_utc(item.event_time_utc).astimezone(_BERLIN)
        iso = local.isocalendar()
        groups.setdefault((iso.year, iso.week), []).append(item)

    reports: list[WeeklyShadowPerformance] = []
    balance = float(starting_balance_eur)
    for (iso_year, iso_week), group in groups.items():
        r_values = [float(item.r_result) for item in group]
        ledger = simulate_fixed_risk_cash_ledger(
            r_values,
            starting_balance_eur=balance,
            fixed_risk_eur=fixed_risk_eur,
        )
        balance = ledger.final_balance_eur
        net_r = float(sum(r_values))
        wins = sum(value > 0.0 for value in r_values)
        losses = sum(value < 0.0 for value in r_values)
        flats = sum(value == 0.0 for value in r_values)
        source_shas = tuple(item.outcome_sha256 for item in group)
        identity = {
            "schema_version": "DAXLAB_WEEKLY_SHADOW_PERFORMANCE_V1",
            "iso_year": iso_year,
            "iso_week": iso_week,
            "timezone": "Europe/Berlin",
            "source_outcome_sha256_order": list(source_shas),
            "starting_balance_eur": ledger.starting_balance_eur,
            "fixed_risk_eur": ledger.fixed_risk_eur,
            "cash_ledger_sha256": ledger.ledger_sha256,
        }
        digest = hashlib.sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        reports.append(
            WeeklyShadowPerformance(
                iso_year=iso_year,
                iso_week=iso_week,
                week_key=f"{iso_year}-W{iso_week:02d}",
                trades=len(group),
                winning_trades=wins,
                losing_trades=losses,
                flat_trades=flats,
                net_r=net_r,
                average_r_per_trade=None if not group else net_r / len(group),
                cash_ledger=ledger,
                source_outcome_sha256_order=source_shas,
                report_sha256=digest,
            )
        )
    return tuple(reports)
