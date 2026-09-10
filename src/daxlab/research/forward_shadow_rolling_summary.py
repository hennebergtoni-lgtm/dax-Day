"""Deterministic aggregation of forward SHADOW performance windows.

This module summarizes already-built SHADOW reports. It does not generate
signals, submit orders, or read broker balances.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Sequence

from daxlab.research.forward_shadow_performance import ForwardShadowPerformanceReport


@dataclass(frozen=True)
class ForwardShadowRollingSummary:
    window_count: int
    positive_cash_windows: int
    negative_cash_windows: int
    flat_cash_windows: int
    no_signal_windows: int
    total_generated_signals: int
    total_allowed_shadow_trades: int
    total_blocked_signals: int
    aggregate_signal_to_trade_conversion: float | None
    total_net_r: float
    total_cash_pnl_eur: float
    best_window_id: str | None
    best_window_cash_pnl_eur: float | None
    worst_window_id: str | None
    worst_window_cash_pnl_eur: float | None
    best_window_share_of_positive_cash: float | None
    summary_sha256: str
    simulated_only: bool = True
    broker_balance: bool = False
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def to_payload(self) -> dict[str, object]:
        return {
            "schema_version": "DAXLAB_FORWARD_SHADOW_ROLLING_SUMMARY_V1",
            "window_count": self.window_count,
            "positive_cash_windows": self.positive_cash_windows,
            "negative_cash_windows": self.negative_cash_windows,
            "flat_cash_windows": self.flat_cash_windows,
            "no_signal_windows": self.no_signal_windows,
            "total_generated_signals": self.total_generated_signals,
            "total_allowed_shadow_trades": self.total_allowed_shadow_trades,
            "total_blocked_signals": self.total_blocked_signals,
            "aggregate_signal_to_trade_conversion": self.aggregate_signal_to_trade_conversion,
            "total_net_r": self.total_net_r,
            "total_cash_pnl_eur": self.total_cash_pnl_eur,
            "best_window_id": self.best_window_id,
            "best_window_cash_pnl_eur": self.best_window_cash_pnl_eur,
            "worst_window_id": self.worst_window_id,
            "worst_window_cash_pnl_eur": self.worst_window_cash_pnl_eur,
            "best_window_share_of_positive_cash": self.best_window_share_of_positive_cash,
            "summary_sha256": self.summary_sha256,
            "simulated_only": self.simulated_only,
            "broker_balance": self.broker_balance,
            "execution_capability": self.execution_capability,
            "order_execution_enabled": self.order_execution_enabled,
        }


def summarize_forward_shadow_windows(
    reports: Sequence[ForwardShadowPerformanceReport],
) -> ForwardShadowRollingSummary:
    items = tuple(reports)
    if not items:
        raise ValueError("at least one forward SHADOW report is required")
    window_ids = [item.window_id for item in items]
    if len(set(window_ids)) != len(window_ids):
        raise ValueError("window_id values must be unique")
    if any(item.execution_capability != "NONE" or item.order_execution_enabled for item in items):
        raise ValueError("all inputs must preserve NO_ORDER")
    if any(not item.simulated_only or item.broker_balance for item in items):
        raise ValueError("all inputs must be SHADOW simulation reports")

    cash = [float(item.cash_ledger.cash_pnl_eur) for item in items]
    generated = sum(item.generated_signals for item in items)
    allowed = sum(item.allowed_shadow_trades for item in items)
    blocked = sum(item.blocked_signals for item in items)
    conversion = None if generated == 0 else allowed / generated

    positive = sum(value > 0.0 for value in cash)
    negative = sum(value < 0.0 for value in cash)
    flat = sum(value == 0.0 for value in cash)
    no_signal = sum(item.generated_signals == 0 for item in items)

    best_index = max(range(len(items)), key=lambda i: cash[i])
    worst_index = min(range(len(items)), key=lambda i: cash[i])
    positive_cash_total = sum(value for value in cash if value > 0.0)
    best_share = None if positive_cash_total <= 0.0 else max(cash[best_index], 0.0) / positive_cash_total

    identity = {
        "schema_version": "DAXLAB_FORWARD_SHADOW_ROLLING_SUMMARY_V1",
        "report_sha256_order": [item.report_sha256 for item in items],
        "window_id_order": window_ids,
    }
    digest = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    return ForwardShadowRollingSummary(
        window_count=len(items),
        positive_cash_windows=positive,
        negative_cash_windows=negative,
        flat_cash_windows=flat,
        no_signal_windows=no_signal,
        total_generated_signals=generated,
        total_allowed_shadow_trades=allowed,
        total_blocked_signals=blocked,
        aggregate_signal_to_trade_conversion=conversion,
        total_net_r=float(sum(item.net_r for item in items)),
        total_cash_pnl_eur=float(sum(cash)),
        best_window_id=items[best_index].window_id,
        best_window_cash_pnl_eur=cash[best_index],
        worst_window_id=items[worst_index].window_id,
        worst_window_cash_pnl_eur=cash[worst_index],
        best_window_share_of_positive_cash=best_share,
        summary_sha256=digest,
    )
