"""Fail-closed gate for forward SHADOW stability evidence.

All thresholds are explicit caller inputs. The gate never promotes a strategy,
submits orders, or changes execution authorization.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math

from daxlab.research.forward_shadow_rolling_summary import ForwardShadowRollingSummary

PASS = "PASS"
BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class ForwardStabilityThresholds:
    min_windows: int
    min_allowed_trades: int
    min_signal_to_trade_conversion: float
    max_consecutive_negative_windows: int
    max_best_window_share_of_positive_cash: float

    def validate(self) -> None:
        if self.min_windows < 1:
            raise ValueError("min_windows must be >= 1")
        if self.min_allowed_trades < 1:
            raise ValueError("min_allowed_trades must be >= 1")
        if not math.isfinite(self.min_signal_to_trade_conversion) or not 0.0 <= self.min_signal_to_trade_conversion <= 1.0:
            raise ValueError("min_signal_to_trade_conversion must be within [0, 1]")
        if self.max_consecutive_negative_windows < 0:
            raise ValueError("max_consecutive_negative_windows must be >= 0")
        if (
            not math.isfinite(self.max_best_window_share_of_positive_cash)
            or not 0.0 <= self.max_best_window_share_of_positive_cash <= 1.0
        ):
            raise ValueError("max_best_window_share_of_positive_cash must be within [0, 1]")

    def to_payload(self) -> dict[str, object]:
        return {
            "min_windows": self.min_windows,
            "min_allowed_trades": self.min_allowed_trades,
            "min_signal_to_trade_conversion": self.min_signal_to_trade_conversion,
            "max_consecutive_negative_windows": self.max_consecutive_negative_windows,
            "max_best_window_share_of_positive_cash": self.max_best_window_share_of_positive_cash,
        }


@dataclass(frozen=True)
class ForwardStabilityGateResult:
    status: str
    blockers: tuple[str, ...]
    thresholds: ForwardStabilityThresholds
    source_summary_sha256: str
    gate_sha256: str
    automatic_promotion: bool = False
    research_only: bool = True
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def to_payload(self) -> dict[str, object]:
        return {
            "schema_version": "DAXLAB_FORWARD_STABILITY_GATE_V1",
            "status": self.status,
            "blockers": list(self.blockers),
            "thresholds": self.thresholds.to_payload(),
            "source_summary_sha256": self.source_summary_sha256,
            "gate_sha256": self.gate_sha256,
            "automatic_promotion": self.automatic_promotion,
            "research_only": self.research_only,
            "execution_capability": self.execution_capability,
            "order_execution_enabled": self.order_execution_enabled,
        }


def evaluate_forward_stability_gate(
    summary: ForwardShadowRollingSummary,
    thresholds: ForwardStabilityThresholds,
) -> ForwardStabilityGateResult:
    thresholds.validate()
    if summary.execution_capability != "NONE" or summary.order_execution_enabled:
        raise ValueError("summary must preserve NO_ORDER")
    if not summary.simulated_only or summary.broker_balance:
        raise ValueError("summary must be SHADOW simulation evidence")

    blockers: list[str] = []
    if summary.window_count < thresholds.min_windows:
        blockers.append("INSUFFICIENT_WINDOWS")
    if summary.total_allowed_shadow_trades < thresholds.min_allowed_trades:
        blockers.append("INSUFFICIENT_ALLOWED_TRADES")

    conversion = summary.aggregate_signal_to_trade_conversion
    if conversion is None:
        blockers.append("NO_SIGNAL_TO_TRADE_CONVERSION")
    elif conversion < thresholds.min_signal_to_trade_conversion:
        blockers.append("SIGNAL_TO_TRADE_CONVERSION_TOO_LOW")

    if summary.max_consecutive_negative_windows > thresholds.max_consecutive_negative_windows:
        blockers.append("NEGATIVE_WINDOW_STREAK_TOO_LONG")

    concentration = summary.best_window_share_of_positive_cash
    if concentration is None:
        blockers.append("NO_POSITIVE_CASH_WINDOWS")
    elif concentration > thresholds.max_best_window_share_of_positive_cash:
        blockers.append("BEST_WINDOW_CONCENTRATION_TOO_HIGH")

    status = PASS if not blockers else BLOCKED
    identity = {
        "schema_version": "DAXLAB_FORWARD_STABILITY_GATE_V1",
        "source_summary_sha256": summary.summary_sha256,
        "thresholds": thresholds.to_payload(),
        "status": status,
        "blockers": blockers,
    }
    digest = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return ForwardStabilityGateResult(
        status=status,
        blockers=tuple(blockers),
        thresholds=thresholds,
        source_summary_sha256=summary.summary_sha256,
        gate_sha256=digest,
    )
