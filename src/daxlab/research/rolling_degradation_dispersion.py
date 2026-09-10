"""Descriptive range diagnostics for rolling Backtest→Forward SHADOW degradation evidence.

Reports observed minima, maxima and ranges across rolling monitoring points. It defines no
thresholds, statistical significance, promotion decision, or execution capability.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from daxlab.research.rolling_backtest_forward_degradation import (
    RollingBacktestForwardDegradationSeries,
)


@dataclass(frozen=True)
class MetricRange:
    minimum: float | None
    maximum: float | None
    span: float | None
    observed_count: int

    def to_payload(self) -> dict[str, object]:
        return {
            "minimum": self.minimum,
            "maximum": self.maximum,
            "span": self.span,
            "observed_count": self.observed_count,
        }


@dataclass(frozen=True)
class RollingDegradationDispersionReport:
    historical_reference_id: str
    point_count: int
    trade_activity_ratio: MetricRange
    forward_r_per_trade: MetricRange
    positive_window_rate: MetricRange
    negative_window_rate: MetricRange
    signal_to_trade_conversion: MetricRange
    cash_pnl_eur: MetricRange
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
            "schema_version": "DAXLAB_ROLLING_DEGRADATION_DISPERSION_V1",
            "historical_reference_id": self.historical_reference_id,
            "point_count": self.point_count,
            "trade_activity_ratio": self.trade_activity_ratio.to_payload(),
            "forward_r_per_trade": self.forward_r_per_trade.to_payload(),
            "positive_window_rate": self.positive_window_rate.to_payload(),
            "negative_window_rate": self.negative_window_rate.to_payload(),
            "signal_to_trade_conversion": self.signal_to_trade_conversion.to_payload(),
            "cash_pnl_eur": self.cash_pnl_eur.to_payload(),
            "source_series_sha256": self.source_series_sha256,
            "report_sha256": self.report_sha256,
            "monitoring_only": self.monitoring_only,
            "statistical_significance_claimed": self.statistical_significance_claimed,
            "composite_score": self.composite_score,
            "automatic_promotion": self.automatic_promotion,
            "execution_capability": self.execution_capability,
            "order_execution_enabled": self.order_execution_enabled,
        }


def _metric_range(values: list[float | None]) -> MetricRange:
    observed = [float(value) for value in values if value is not None]
    if not observed:
        return MetricRange(None, None, None, 0)
    minimum = min(observed)
    maximum = max(observed)
    return MetricRange(minimum, maximum, maximum - minimum, len(observed))


def build_rolling_degradation_dispersion_report(
    series: RollingBacktestForwardDegradationSeries,
) -> RollingDegradationDispersionReport:
    if series.execution_capability != "NONE" or series.order_execution_enabled:
        raise ValueError("rolling series must preserve NO_ORDER")
    if not series.monitoring_only or series.independence_claimed:
        raise ValueError("rolling series must preserve monitoring-only governance")
    if not series.points:
        raise ValueError("rolling series must contain at least one point")

    degradations = [point.degradation for point in series.points]
    trade_activity = _metric_range([item.trade_activity_ratio for item in degradations])
    r_per_trade = _metric_range([item.forward_r_per_trade for item in degradations])
    positive_rate = _metric_range([item.forward_positive_window_rate for item in degradations])
    negative_rate = _metric_range([item.forward_negative_window_rate for item in degradations])
    conversion = _metric_range([item.forward_signal_to_trade_conversion for item in degradations])
    cash = _metric_range([item.forward_total_cash_pnl_eur for item in degradations])

    identity = {
        "schema_version": "DAXLAB_ROLLING_DEGRADATION_DISPERSION_V1",
        "source_series_sha256": series.series_sha256,
        "point_sha256_order": [point.point_sha256 for point in series.points],
        "monitoring_only": True,
        "statistical_significance_claimed": False,
    }
    digest = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    return RollingDegradationDispersionReport(
        historical_reference_id=series.historical_reference_id,
        point_count=len(series.points),
        trade_activity_ratio=trade_activity,
        forward_r_per_trade=r_per_trade,
        positive_window_rate=positive_rate,
        negative_window_rate=negative_rate,
        signal_to_trade_conversion=conversion,
        cash_pnl_eur=cash,
        source_series_sha256=series.series_sha256,
        report_sha256=digest,
    )
