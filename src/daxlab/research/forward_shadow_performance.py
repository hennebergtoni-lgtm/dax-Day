"""Compact forward SHADOW performance reporting.

The report accounts for observed SHADOW signals only. It never reads a broker
balance and never submits orders. Allowed signals may carry an observed R result;
blocked signals must carry an explicit block reason.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import hashlib
import json
import math
from typing import Sequence

from daxlab.research.shadow_cash_ledger import ShadowCashLedger, simulate_fixed_risk_cash_ledger


ALLOWED = "ALLOWED"
BLOCKED = "BLOCKED"
COMPLETE = "COMPLETE"
NO_SIGNALS_OBSERVED = "NO_SIGNALS_OBSERVED"


@dataclass(frozen=True)
class ShadowSignalObservation:
    signal_id: str
    status: str
    r_result: float | None = None
    block_reason: str | None = None


@dataclass(frozen=True)
class ForwardShadowPerformanceReport:
    window_id: str
    generated_signals: int
    allowed_shadow_trades: int
    blocked_signals: int
    signal_to_trade_conversion: float | None
    block_reason_counts: tuple[tuple[str, int], ...]
    net_r: float
    winning_trades: int
    losing_trades: int
    flat_trades: int
    cash_ledger: ShadowCashLedger
    status: str
    report_sha256: str
    simulated_only: bool = True
    broker_balance: bool = False
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def to_payload(self) -> dict[str, object]:
        return {
            "schema_version": "DAXLAB_FORWARD_SHADOW_PERFORMANCE_V1",
            "window_id": self.window_id,
            "generated_signals": self.generated_signals,
            "allowed_shadow_trades": self.allowed_shadow_trades,
            "blocked_signals": self.blocked_signals,
            "signal_to_trade_conversion": self.signal_to_trade_conversion,
            "block_reason_counts": dict(self.block_reason_counts),
            "net_r": self.net_r,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "flat_trades": self.flat_trades,
            "cash_ledger": self.cash_ledger.to_payload(),
            "status": self.status,
            "report_sha256": self.report_sha256,
            "simulated_only": self.simulated_only,
            "broker_balance": self.broker_balance,
            "execution_capability": self.execution_capability,
            "order_execution_enabled": self.order_execution_enabled,
        }


def build_forward_shadow_performance_report(
    window_id: str,
    observations: Sequence[ShadowSignalObservation],
    *,
    starting_balance_eur: float,
    fixed_risk_eur: float,
) -> ForwardShadowPerformanceReport:
    """Build one deterministic SHADOW performance report for an explicit window."""
    label = window_id.strip()
    if not label:
        raise ValueError("window_id must be non-empty")

    items = tuple(observations)
    signal_ids = [item.signal_id.strip() for item in items]
    if any(not signal_id for signal_id in signal_ids):
        raise ValueError("signal_id must be non-empty")
    if len(set(signal_ids)) != len(signal_ids):
        raise ValueError("signal_id values must be unique within a window")

    allowed_r: list[float] = []
    reasons: Counter[str] = Counter()
    for item in items:
        if item.status not in {ALLOWED, BLOCKED}:
            raise ValueError(f"unsupported signal status: {item.status}")
        if item.status == ALLOWED:
            if item.block_reason is not None:
                raise ValueError("ALLOWED signals cannot have block_reason")
            if item.r_result is None or not math.isfinite(float(item.r_result)):
                raise ValueError("ALLOWED signals require finite r_result")
            allowed_r.append(float(item.r_result))
        else:
            if item.r_result is not None:
                raise ValueError("BLOCKED signals cannot have r_result")
            reason = (item.block_reason or "").strip()
            if not reason:
                raise ValueError("BLOCKED signals require block_reason")
            reasons[reason] += 1

    generated = len(items)
    allowed = len(allowed_r)
    blocked = generated - allowed
    conversion = None if generated == 0 else allowed / generated
    status = NO_SIGNALS_OBSERVED if generated == 0 else COMPLETE

    ledger = simulate_fixed_risk_cash_ledger(
        allowed_r,
        starting_balance_eur=starting_balance_eur,
        fixed_risk_eur=fixed_risk_eur,
    )
    wins = sum(value > 0.0 for value in allowed_r)
    losses = sum(value < 0.0 for value in allowed_r)
    flats = sum(value == 0.0 for value in allowed_r)
    reason_counts = tuple(sorted(reasons.items()))

    identity = {
        "schema_version": "DAXLAB_FORWARD_SHADOW_PERFORMANCE_V1",
        "window_id": label,
        "observations": [asdict(item) for item in items],
        "starting_balance_eur": float(starting_balance_eur),
        "fixed_risk_eur": float(fixed_risk_eur),
        "cash_ledger_sha256": ledger.ledger_sha256,
        "block_reason_counts": list(reason_counts),
    }
    digest = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    return ForwardShadowPerformanceReport(
        window_id=label,
        generated_signals=generated,
        allowed_shadow_trades=allowed,
        blocked_signals=blocked,
        signal_to_trade_conversion=conversion,
        block_reason_counts=reason_counts,
        net_r=float(sum(allowed_r)),
        winning_trades=wins,
        losing_trades=losses,
        flat_trades=flats,
        cash_ledger=ledger,
        status=status,
        report_sha256=digest,
    )
