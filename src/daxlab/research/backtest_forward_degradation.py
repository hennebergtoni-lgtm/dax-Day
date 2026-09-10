"""Descriptive comparison of historical OOS expectations with forward SHADOW evidence.

This module reports metric-by-metric changes only. It deliberately has no composite
score, no pass/fail threshold, and no promotion capability.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math

from daxlab.research.forward_shadow_rolling_summary import ForwardShadowRollingSummary


V112_REFERENCE_ID = "V112_REFERENCE_V1"
V112_REFERENCE_SOURCE = "research/V112_REFERENCE_V1/reference_result.json"
V112_REFERENCE_RESULT_BLOB_SHA = "397af5ae3d17fc1ad427cf6abbfa72f3c7a8564d"
V112_SESSION_OHLC_SHA256 = "e51bba6cb2befe5e7eb0376318e43b096a3e2ecaae3f556019862975c60286a2"
V112_ENGINE_SHA256 = "b3d62e0cad72420d36ade523857d024d4a334298be51a8313069e36614bda888"


@dataclass(frozen=True)
class HistoricalOOSReference:
    reference_id: str
    windows: int
    trades: int
    net_r: float
    positive_windows: int
    negative_windows: int
    flat_windows: int = 0
    source_path: str | None = None
    source_blob_sha: str | None = None
    session_ohlc_sha256: str | None = None
    engine_sha256: str | None = None

    def validate(self) -> None:
        if not self.reference_id.strip():
            raise ValueError("reference_id must be non-empty")
        if self.windows < 1 or self.trades < 1:
            raise ValueError("historical windows and trades must be >= 1")
        if any(value < 0 for value in (self.positive_windows, self.negative_windows, self.flat_windows)):
            raise ValueError("historical window counts must be non-negative")
        if self.positive_windows + self.negative_windows + self.flat_windows != self.windows:
            raise ValueError("historical window counts must sum to windows")
        if not math.isfinite(self.net_r):
            raise ValueError("historical net_r must be finite")


def v11_2_active_reference() -> HistoricalOOSReference:
    """Return the frozen clean V11.2 ACTIVE_REFERENCE declared in the repository.

    Values and source identities are intentionally explicit. Changing this factory is a
    scientific reference change and must be supported by a new audited reference artifact;
    callers cannot silently mutate the canonical V11.2 measurement.
    """
    return HistoricalOOSReference(
        reference_id=V112_REFERENCE_ID,
        windows=81,
        trades=856,
        net_r=-31.309210619787684,
        positive_windows=37,
        negative_windows=44,
        flat_windows=0,
        source_path=V112_REFERENCE_SOURCE,
        source_blob_sha=V112_REFERENCE_RESULT_BLOB_SHA,
        session_ohlc_sha256=V112_SESSION_OHLC_SHA256,
        engine_sha256=V112_ENGINE_SHA256,
    )


@dataclass(frozen=True)
class BacktestForwardDegradationReport:
    historical_reference_id: str
    historical_windows: int
    forward_windows: int
    historical_trades_per_window: float
    forward_trades_per_window: float
    trade_activity_ratio: float
    historical_r_per_trade: float
    forward_r_per_trade: float | None
    r_per_trade_delta: float | None
    historical_positive_window_rate: float
    forward_positive_window_rate: float
    positive_window_rate_delta: float
    historical_negative_window_rate: float
    forward_negative_window_rate: float
    negative_window_rate_delta: float
    forward_signal_to_trade_conversion: float | None
    forward_total_cash_pnl_eur: float
    forward_best_window_share_of_positive_cash: float | None
    source_summary_sha256: str
    historical_source_path: str | None
    historical_source_blob_sha: str | None
    historical_session_ohlc_sha256: str | None
    historical_engine_sha256: str | None
    report_sha256: str
    descriptive_only: bool = True
    composite_score: None = None
    automatic_promotion: bool = False
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def to_payload(self) -> dict[str, object]:
        return {
            "schema_version": "DAXLAB_BACKTEST_FORWARD_DEGRADATION_V1",
            **self.__dict__,
        }


def build_backtest_forward_degradation_report(
    historical: HistoricalOOSReference,
    forward: ForwardShadowRollingSummary,
) -> BacktestForwardDegradationReport:
    """Compare normalized historical OOS and forward SHADOW metrics without judging them."""
    historical.validate()
    if forward.execution_capability != "NONE" or forward.order_execution_enabled:
        raise ValueError("forward summary must preserve NO_ORDER")
    if not forward.simulated_only or forward.broker_balance:
        raise ValueError("forward summary must be SHADOW simulation evidence")
    if forward.window_count < 1:
        raise ValueError("forward summary must contain at least one window")

    hist_trades_per_window = historical.trades / historical.windows
    fwd_trades_per_window = forward.total_allowed_shadow_trades / forward.window_count
    activity_ratio = fwd_trades_per_window / hist_trades_per_window

    hist_r_per_trade = historical.net_r / historical.trades
    if forward.total_allowed_shadow_trades:
        fwd_r_per_trade = forward.total_net_r / forward.total_allowed_shadow_trades
        r_delta = fwd_r_per_trade - hist_r_per_trade
    else:
        fwd_r_per_trade = None
        r_delta = None

    hist_pos = historical.positive_windows / historical.windows
    fwd_pos = forward.positive_cash_windows / forward.window_count
    hist_neg = historical.negative_windows / historical.windows
    fwd_neg = forward.negative_cash_windows / forward.window_count

    identity = {
        "schema_version": "DAXLAB_BACKTEST_FORWARD_DEGRADATION_V1",
        "historical": historical.__dict__,
        "source_summary_sha256": forward.summary_sha256,
        "descriptive_only": True,
        "composite_score": None,
    }
    digest = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    return BacktestForwardDegradationReport(
        historical_reference_id=historical.reference_id.strip(),
        historical_windows=historical.windows,
        forward_windows=forward.window_count,
        historical_trades_per_window=hist_trades_per_window,
        forward_trades_per_window=fwd_trades_per_window,
        trade_activity_ratio=activity_ratio,
        historical_r_per_trade=hist_r_per_trade,
        forward_r_per_trade=fwd_r_per_trade,
        r_per_trade_delta=r_delta,
        historical_positive_window_rate=hist_pos,
        forward_positive_window_rate=fwd_pos,
        positive_window_rate_delta=fwd_pos - hist_pos,
        historical_negative_window_rate=hist_neg,
        forward_negative_window_rate=fwd_neg,
        negative_window_rate_delta=fwd_neg - hist_neg,
        forward_signal_to_trade_conversion=forward.aggregate_signal_to_trade_conversion,
        forward_total_cash_pnl_eur=forward.total_cash_pnl_eur,
        forward_best_window_share_of_positive_cash=forward.best_window_share_of_positive_cash,
        source_summary_sha256=forward.summary_sha256,
        historical_source_path=historical.source_path,
        historical_source_blob_sha=historical.source_blob_sha,
        historical_session_ohlc_sha256=historical.session_ohlc_sha256,
        historical_engine_sha256=historical.engine_sha256,
        report_sha256=digest,
    )
