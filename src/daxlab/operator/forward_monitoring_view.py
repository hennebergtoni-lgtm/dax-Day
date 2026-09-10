"""Read-only operator contract for Forward SHADOW monitoring.

Transforms the verified rolling degradation monitoring view into a small dashboard payload.
No trading decision, threshold, promotion, paper or live execution is introduced here.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from daxlab.research.rolling_degradation_monitoring_view import (
    RollingDegradationMonitoringView,
)


@dataclass(frozen=True)
class ForwardMonitoringOperatorView:
    historical_reference_id: str
    source_series_sha256: str
    point_count: int
    trend_summary_sha256: str
    dispersion_report_sha256: str
    extremes_report_sha256: str
    monitoring_view_sha256: str
    payload_sha256: str
    mode: str = "SHADOW"
    monitoring_only: bool = True
    read_only: bool = True
    statistical_significance_claimed: bool = False
    composite_score: None = None
    automatic_promotion: bool = False
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def to_payload(self) -> dict[str, object]:
        return {
            "schema_version": "DAXLAB_FORWARD_MONITORING_OPERATOR_VIEW_V1",
            "historical_reference_id": self.historical_reference_id,
            "source_series_sha256": self.source_series_sha256,
            "point_count": self.point_count,
            "component_evidence": {
                "trend_summary_sha256": self.trend_summary_sha256,
                "dispersion_report_sha256": self.dispersion_report_sha256,
                "extremes_report_sha256": self.extremes_report_sha256,
                "monitoring_view_sha256": self.monitoring_view_sha256,
            },
            "payload_sha256": self.payload_sha256,
            "mode": self.mode,
            "monitoring_only": self.monitoring_only,
            "read_only": self.read_only,
            "statistical_significance_claimed": self.statistical_significance_claimed,
            "composite_score": self.composite_score,
            "automatic_promotion": self.automatic_promotion,
            "execution_capability": self.execution_capability,
            "order_execution_enabled": self.order_execution_enabled,
        }


def build_forward_monitoring_operator_view(
    view: RollingDegradationMonitoringView,
) -> ForwardMonitoringOperatorView:
    if view.execution_capability != "NONE" or view.order_execution_enabled:
        raise ValueError("monitoring view must preserve NO_ORDER")
    if not view.monitoring_only:
        raise ValueError("monitoring view must remain monitoring-only")
    if view.statistical_significance_claimed:
        raise ValueError("monitoring view must not claim statistical significance")
    if view.composite_score is not None or view.automatic_promotion:
        raise ValueError("monitoring view must not score or auto-promote")

    identity = {
        "schema_version": "DAXLAB_FORWARD_MONITORING_OPERATOR_VIEW_V1",
        "historical_reference_id": view.historical_reference_id,
        "source_series_sha256": view.source_series_sha256,
        "point_count": view.point_count,
        "trend_summary_sha256": view.trend.summary_sha256,
        "dispersion_report_sha256": view.dispersion.report_sha256,
        "extremes_report_sha256": view.extremes.report_sha256,
        "monitoring_view_sha256": view.view_sha256,
        "mode": "SHADOW",
        "read_only": True,
        "execution_capability": "NONE",
        "order_execution_enabled": False,
    }
    digest = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    return ForwardMonitoringOperatorView(
        historical_reference_id=view.historical_reference_id,
        source_series_sha256=view.source_series_sha256,
        point_count=view.point_count,
        trend_summary_sha256=view.trend.summary_sha256,
        dispersion_report_sha256=view.dispersion.report_sha256,
        extremes_report_sha256=view.extremes.report_sha256,
        monitoring_view_sha256=view.view_sha256,
        payload_sha256=digest,
    )
