"""Locate observed best/worst rolling Backtest→Forward SHADOW monitoring points.

This module records where metric extremes occur in the ordered rolling series. It is
monitoring-only and defines no threshold, significance claim, promotion, or execution.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from daxlab.research.rolling_backtest_forward_degradation import (
    RollingBacktestForwardDegradationSeries,
)


@dataclass(frozen=True)
class ExtremeLocation:
    minimum_value: float | None
    minimum_point_index: int | None
    minimum_end_window_id: str | None
    maximum_value: float | None
    maximum_point_index: int | None
    maximum_end_window_id: str | None
    observed_count: int

    def to_payload(self) -> dict[str, object]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class RollingDegradationExtremeLocationReport:
    historical_reference_id: str
    point_count: int
    forward_r_per_trade: ExtremeLocation
    cash_pnl_eur: ExtremeLocation
    trade_activity_ratio: ExtremeLocation
    source_series_sha256: str
    report_sha256: str
    monitoring_only: bool = True
    statistical_significance_claimed: bool = False
    composite_score: None = None
    automatic_promotion: bool = False
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def to_payload(self) -> dict[str, object]:
        return {
            "schema_version": "DAXLAB_ROLLING_DEGRADATION_EXTREME_LOCATION_V1",
            "historical_reference_id": self.historical_reference_id,
            "point_count": self.point_count,
            "forward_r_per_trade": self.forward_r_per_trade.to_payload(),
            "cash_pnl_eur": self.cash_pnl_eur.to_payload(),
            "trade_activity_ratio": self.trade_activity_ratio.to_payload(),
            "source_series_sha256": self.source_series_sha256,
            "report_sha256": self.report_sha256,
            "monitoring_only": self.monitoring_only,
            "statistical_significance_claimed": self.statistical_significance_claimed,
            "composite_score": self.composite_score,
            "automatic_promotion": self.automatic_promotion,
            "execution_capability": self.execution_capability,
            "order_execution_enabled": self.order_execution_enabled,
        }


def _extreme_location(values: list[tuple[int, str, float | None]]) -> ExtremeLocation:
    observed = [(index, window_id, float(value)) for index, window_id, value in values if value is not None]
    if not observed:
        return ExtremeLocation(None, None, None, None, None, None, 0)
    minimum = min(observed, key=lambda item: (item[2], item[0]))
    maximum = max(observed, key=lambda item: (item[2], -item[0]))
    return ExtremeLocation(
        minimum_value=minimum[2],
        minimum_point_index=minimum[0],
        minimum_end_window_id=minimum[1],
        maximum_value=maximum[2],
        maximum_point_index=maximum[0],
        maximum_end_window_id=maximum[1],
        observed_count=len(observed),
    )


def build_rolling_degradation_extreme_location_report(
    series: RollingBacktestForwardDegradationSeries,
) -> RollingDegradationExtremeLocationReport:
    if series.execution_capability != "NONE" or series.order_execution_enabled:
        raise ValueError("rolling series must preserve NO_ORDER")
    if not series.monitoring_only or series.independence_claimed:
        raise ValueError("rolling series must preserve monitoring-only governance")
    if not series.points:
        raise ValueError("rolling series must contain at least one point")

    indexed = list(enumerate(series.points))
    r_per_trade = _extreme_location(
        [(index, point.end_window_id, point.degradation.forward_r_per_trade) for index, point in indexed]
    )
    cash = _extreme_location(
        [(index, point.end_window_id, point.degradation.forward_total_cash_pnl_eur) for index, point in indexed]
    )
    activity = _extreme_location(
        [(index, point.end_window_id, point.degradation.trade_activity_ratio) for index, point in indexed]
    )

    identity = {
        "schema_version": "DAXLAB_ROLLING_DEGRADATION_EXTREME_LOCATION_V1",
        "source_series_sha256": series.series_sha256,
        "point_sha256_order": [point.point_sha256 for point in series.points],
        "monitoring_only": True,
        "statistical_significance_claimed": False,
    }
    digest = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    return RollingDegradationExtremeLocationReport(
        historical_reference_id=series.historical_reference_id,
        point_count=len(series.points),
        forward_r_per_trade=r_per_trade,
        cash_pnl_eur=cash,
        trade_activity_ratio=activity,
        source_series_sha256=series.series_sha256,
        report_sha256=digest,
    )
