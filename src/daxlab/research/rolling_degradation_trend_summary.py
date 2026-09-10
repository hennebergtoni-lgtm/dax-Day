"""Descriptive endpoint trend summary for rolling Backtest→Forward degradation evidence.

This module compares the first and latest rolling degradation points only. It does not
infer statistical significance, define thresholds, promote strategies, or enable execution.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from daxlab.research.rolling_backtest_forward_degradation import (
    RollingBacktestForwardDegradationSeries,
)


@dataclass(frozen=True)
class RollingDegradationTrendSummary:
    historical_reference_id: str
    point_count: int
    first_end_window_id: str
    latest_end_window_id: str
    first_trade_activity_ratio: float
    latest_trade_activity_ratio: float
    trade_activity_ratio_delta: float
    first_forward_r_per_trade: float | None
    latest_forward_r_per_trade: float | None
    forward_r_per_trade_delta: float | None
    first_positive_window_rate: float
    latest_positive_window_rate: float
    positive_window_rate_delta: float
    first_negative_window_rate: float
    latest_negative_window_rate: float
    negative_window_rate_delta: float
    first_signal_to_trade_conversion: float | None
    latest_signal_to_trade_conversion: float | None
    signal_to_trade_conversion_delta: float | None
    first_cash_pnl_eur: float
    latest_cash_pnl_eur: float
    cash_pnl_eur_delta: float
    source_series_sha256: str
    summary_sha256: str
    monitoring_only: bool = True
    statistical_significance_claimed: bool = False
    automatic_promotion: bool = False
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def to_payload(self) -> dict[str, object]:
        return {
            "schema_version": "DAXLAB_ROLLING_DEGRADATION_TREND_SUMMARY_V1",
            **self.__dict__,
        }


def _optional_delta(first: float | None, latest: float | None) -> float | None:
    if first is None or latest is None:
        return None
    return latest - first


def build_rolling_degradation_trend_summary(
    series: RollingBacktestForwardDegradationSeries,
) -> RollingDegradationTrendSummary:
    if series.execution_capability != "NONE" or series.order_execution_enabled:
        raise ValueError("rolling series must preserve NO_ORDER")
    if not series.monitoring_only or series.independence_claimed:
        raise ValueError("rolling series must preserve monitoring-only governance")
    if not series.points:
        raise ValueError("rolling series must contain at least one point")

    first = series.points[0]
    latest = series.points[-1]
    first_d = first.degradation
    latest_d = latest.degradation

    identity = {
        "schema_version": "DAXLAB_ROLLING_DEGRADATION_TREND_SUMMARY_V1",
        "source_series_sha256": series.series_sha256,
        "first_point_sha256": first.point_sha256,
        "latest_point_sha256": latest.point_sha256,
        "monitoring_only": True,
        "statistical_significance_claimed": False,
    }
    digest = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    return RollingDegradationTrendSummary(
        historical_reference_id=series.historical_reference_id,
        point_count=len(series.points),
        first_end_window_id=first.end_window_id,
        latest_end_window_id=latest.end_window_id,
        first_trade_activity_ratio=first_d.trade_activity_ratio,
        latest_trade_activity_ratio=latest_d.trade_activity_ratio,
        trade_activity_ratio_delta=latest_d.trade_activity_ratio - first_d.trade_activity_ratio,
        first_forward_r_per_trade=first_d.forward_r_per_trade,
        latest_forward_r_per_trade=latest_d.forward_r_per_trade,
        forward_r_per_trade_delta=_optional_delta(first_d.forward_r_per_trade, latest_d.forward_r_per_trade),
        first_positive_window_rate=first_d.forward_positive_window_rate,
        latest_positive_window_rate=latest_d.forward_positive_window_rate,
        positive_window_rate_delta=latest_d.forward_positive_window_rate - first_d.forward_positive_window_rate,
        first_negative_window_rate=first_d.forward_negative_window_rate,
        latest_negative_window_rate=latest_d.forward_negative_window_rate,
        negative_window_rate_delta=latest_d.forward_negative_window_rate - first_d.forward_negative_window_rate,
        first_signal_to_trade_conversion=first_d.forward_signal_to_trade_conversion,
        latest_signal_to_trade_conversion=latest_d.forward_signal_to_trade_conversion,
        signal_to_trade_conversion_delta=_optional_delta(
            first_d.forward_signal_to_trade_conversion,
            latest_d.forward_signal_to_trade_conversion,
        ),
        first_cash_pnl_eur=first_d.forward_total_cash_pnl_eur,
        latest_cash_pnl_eur=latest_d.forward_total_cash_pnl_eur,
        cash_pnl_eur_delta=latest_d.forward_total_cash_pnl_eur - first_d.forward_total_cash_pnl_eur,
        source_series_sha256=series.series_sha256,
        summary_sha256=digest,
    )
