"""Temporal rolling comparison of frozen historical OOS with ordered forward SHADOW windows.

This module reuses the existing forward summary and backtest-forward degradation layers.
It is descriptive only: no thresholds, no composite score, no promotion, no execution.
Rolling points may overlap and therefore are never claimed to be statistically independent.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Sequence

from daxlab.research.backtest_forward_degradation import (
    BacktestForwardDegradationReport,
    HistoricalOOSReference,
    build_backtest_forward_degradation_report,
)
from daxlab.research.forward_shadow_performance import ForwardShadowPerformanceReport
from daxlab.research.forward_shadow_rolling_summary import summarize_forward_shadow_windows


@dataclass(frozen=True)
class RollingDegradationPoint:
    start_index: int
    end_index: int
    start_window_id: str
    end_window_id: str
    window_ids: tuple[str, ...]
    source_report_sha256_order: tuple[str, ...]
    degradation: BacktestForwardDegradationReport
    point_sha256: str
    descriptive_only: bool = True
    composite_score: None = None
    automatic_promotion: bool = False
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def to_payload(self) -> dict[str, object]:
        return {
            "schema_version": "DAXLAB_ROLLING_BACKTEST_FORWARD_DEGRADATION_POINT_V1",
            "start_index": self.start_index,
            "end_index": self.end_index,
            "start_window_id": self.start_window_id,
            "end_window_id": self.end_window_id,
            "window_ids": list(self.window_ids),
            "source_report_sha256_order": list(self.source_report_sha256_order),
            "degradation": self.degradation.to_payload(),
            "point_sha256": self.point_sha256,
            "descriptive_only": self.descriptive_only,
            "composite_score": self.composite_score,
            "automatic_promotion": self.automatic_promotion,
            "execution_capability": self.execution_capability,
            "order_execution_enabled": self.order_execution_enabled,
        }


@dataclass(frozen=True)
class RollingBacktestForwardDegradationSeries:
    historical_reference_id: str
    rolling_width: int
    source_window_count: int
    source_window_id_order: tuple[str, ...]
    points: tuple[RollingDegradationPoint, ...]
    series_sha256: str
    points_overlap: bool
    monitoring_only: bool = True
    independence_claimed: bool = False
    descriptive_only: bool = True
    composite_score: None = None
    automatic_promotion: bool = False
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def to_payload(self) -> dict[str, object]:
        return {
            "schema_version": "DAXLAB_ROLLING_BACKTEST_FORWARD_DEGRADATION_SERIES_V1",
            "historical_reference_id": self.historical_reference_id,
            "rolling_width": self.rolling_width,
            "source_window_count": self.source_window_count,
            "source_window_id_order": list(self.source_window_id_order),
            "points": [point.to_payload() for point in self.points],
            "series_sha256": self.series_sha256,
            "points_overlap": self.points_overlap,
            "monitoring_only": self.monitoring_only,
            "independence_claimed": self.independence_claimed,
            "descriptive_only": self.descriptive_only,
            "composite_score": self.composite_score,
            "automatic_promotion": self.automatic_promotion,
            "execution_capability": self.execution_capability,
            "order_execution_enabled": self.order_execution_enabled,
        }


def build_rolling_backtest_forward_degradation_series(
    historical: HistoricalOOSReference,
    reports: Sequence[ForwardShadowPerformanceReport],
    *,
    rolling_width: int,
) -> RollingBacktestForwardDegradationSeries:
    """Build a fixed-width rolling descriptive series from ordered SHADOW windows.

    The caller owns chronological ordering. We preserve and hash that order explicitly so
    evidence cannot be silently re-ordered without changing the series identity. Consecutive
    points overlap whenever rolling_width > 1 and more than one point exists; this series is
    monitoring evidence only and makes no statistical-independence claim.
    """
    historical.validate()
    items = tuple(reports)
    if not items:
        raise ValueError("at least one forward SHADOW report is required")
    if rolling_width < 1:
        raise ValueError("rolling_width must be >= 1")
    if rolling_width > len(items):
        raise ValueError("rolling_width cannot exceed number of forward windows")

    window_ids = tuple(item.window_id for item in items)
    if len(set(window_ids)) != len(window_ids):
        raise ValueError("window_id values must be unique")

    points: list[RollingDegradationPoint] = []
    for end in range(rolling_width, len(items) + 1):
        start = end - rolling_width
        window = items[start:end]
        summary = summarize_forward_shadow_windows(window)
        degradation = build_backtest_forward_degradation_report(historical, summary)
        source_hashes = tuple(item.report_sha256 for item in window)
        ids = tuple(item.window_id for item in window)
        identity = {
            "schema_version": "DAXLAB_ROLLING_BACKTEST_FORWARD_DEGRADATION_POINT_V1",
            "historical_reference_id": historical.reference_id,
            "start_index": start,
            "end_index": end - 1,
            "window_ids": ids,
            "source_report_sha256_order": source_hashes,
            "degradation_report_sha256": degradation.report_sha256,
        }
        point_sha = hashlib.sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        points.append(
            RollingDegradationPoint(
                start_index=start,
                end_index=end - 1,
                start_window_id=ids[0],
                end_window_id=ids[-1],
                window_ids=ids,
                source_report_sha256_order=source_hashes,
                degradation=degradation,
                point_sha256=point_sha,
            )
        )

    points_overlap = rolling_width > 1 and len(points) > 1
    series_identity = {
        "schema_version": "DAXLAB_ROLLING_BACKTEST_FORWARD_DEGRADATION_SERIES_V1",
        "historical_reference_id": historical.reference_id,
        "rolling_width": rolling_width,
        "source_window_id_order": window_ids,
        "source_report_sha256_order": [item.report_sha256 for item in items],
        "point_sha256_order": [point.point_sha256 for point in points],
        "points_overlap": points_overlap,
        "monitoring_only": True,
        "independence_claimed": False,
    }
    series_sha = hashlib.sha256(
        json.dumps(series_identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    return RollingBacktestForwardDegradationSeries(
        historical_reference_id=historical.reference_id,
        rolling_width=rolling_width,
        source_window_count=len(items),
        source_window_id_order=window_ids,
        points=tuple(points),
        series_sha256=series_sha,
        points_overlap=points_overlap,
    )
