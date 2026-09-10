"""Consolidated monitoring view for rolling Backtest→Forward SHADOW diagnostics.

This wrapper composes already-derived trend, dispersion and extreme-location reports from
one rolling series. It introduces no new metric, threshold, score, promotion or execution.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from daxlab.research.rolling_backtest_forward_degradation import (
    RollingBacktestForwardDegradationSeries,
)
from daxlab.research.rolling_degradation_dispersion import (
    RollingDegradationDispersionReport,
    build_rolling_degradation_dispersion_report,
)
from daxlab.research.rolling_degradation_extreme_location import (
    RollingDegradationExtremeLocationReport,
    build_rolling_degradation_extreme_location_report,
)
from daxlab.research.rolling_degradation_trend_summary import (
    RollingDegradationTrendSummary,
    build_rolling_degradation_trend_summary,
)


@dataclass(frozen=True)
class RollingDegradationMonitoringView:
    historical_reference_id: str
    source_series_sha256: str
    point_count: int
    trend: RollingDegradationTrendSummary
    dispersion: RollingDegradationDispersionReport
    extremes: RollingDegradationExtremeLocationReport
    view_sha256: str
    monitoring_only: bool = True
    statistical_significance_claimed: bool = False
    composite_score: None = None
    automatic_promotion: bool = False
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def to_payload(self) -> dict[str, object]:
        return {
            "schema_version": "DAXLAB_ROLLING_DEGRADATION_MONITORING_VIEW_V1",
            "historical_reference_id": self.historical_reference_id,
            "source_series_sha256": self.source_series_sha256,
            "point_count": self.point_count,
            "trend": self.trend.to_payload(),
            "dispersion": self.dispersion.to_payload(),
            "extremes": self.extremes.to_payload(),
            "view_sha256": self.view_sha256,
            "monitoring_only": self.monitoring_only,
            "statistical_significance_claimed": self.statistical_significance_claimed,
            "composite_score": self.composite_score,
            "automatic_promotion": self.automatic_promotion,
            "execution_capability": self.execution_capability,
            "order_execution_enabled": self.order_execution_enabled,
        }


def build_rolling_degradation_monitoring_view(
    series: RollingBacktestForwardDegradationSeries,
) -> RollingDegradationMonitoringView:
    if series.execution_capability != "NONE" or series.order_execution_enabled:
        raise ValueError("rolling series must preserve NO_ORDER")
    if not series.monitoring_only or series.independence_claimed:
        raise ValueError("rolling series must preserve monitoring-only governance")

    trend = build_rolling_degradation_trend_summary(series)
    dispersion = build_rolling_degradation_dispersion_report(series)
    extremes = build_rolling_degradation_extreme_location_report(series)

    source_shas = {
        trend.source_series_sha256,
        dispersion.source_series_sha256,
        extremes.source_series_sha256,
    }
    if source_shas != {series.series_sha256}:
        raise ValueError("component reports must share the same rolling source series")
    if any(
        item.execution_capability != "NONE" or item.order_execution_enabled
        for item in (trend, dispersion, extremes)
    ):
        raise ValueError("component reports must preserve NO_ORDER")
    if any(not item.monitoring_only for item in (trend, dispersion, extremes)):
        raise ValueError("component reports must remain monitoring-only")

    identity = {
        "schema_version": "DAXLAB_ROLLING_DEGRADATION_MONITORING_VIEW_V1",
        "source_series_sha256": series.series_sha256,
        "trend_sha256": trend.summary_sha256,
        "dispersion_sha256": dispersion.report_sha256,
        "extremes_sha256": extremes.report_sha256,
    }
    digest = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    return RollingDegradationMonitoringView(
        historical_reference_id=series.historical_reference_id,
        source_series_sha256=series.series_sha256,
        point_count=len(series.points),
        trend=trend,
        dispersion=dispersion,
        extremes=extremes,
        view_sha256=digest,
    )
