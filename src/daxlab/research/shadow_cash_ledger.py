from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Sequence


COMPLETE = "COMPLETE"
CAPITAL_INSUFFICIENT = "CAPITAL_INSUFFICIENT"
NEGATIVE_BALANCE_AFTER_TRADE = "NEGATIVE_BALANCE_AFTER_TRADE"


@dataclass(frozen=True)
class ShadowCashLedger:
    mode: str
    starting_balance_eur: float
    fixed_risk_eur: float
    requested_trades: int
    processed_trades: int
    unprocessed_trades: int
    status: str
    halted_trade_index: int | None
    trade_r: tuple[float, ...]
    trade_pnl_eur: tuple[float, ...]
    equity_curve_eur: tuple[float, ...]
    final_balance_eur: float
    cash_pnl_eur: float
    return_pct: float
    peak_balance_eur: float
    minimum_balance_eur: float
    max_drawdown_eur: float
    max_drawdown_pct_of_peak: float
    ledger_sha256: str

    def to_payload(self) -> dict[str, object]:
        return {
            "schema_version": "DAXLAB_SHADOW_CASH_LEDGER_V1",
            "mode": self.mode,
            "starting_balance_eur": self.starting_balance_eur,
            "fixed_risk_eur": self.fixed_risk_eur,
            "requested_trades": self.requested_trades,
            "processed_trades": self.processed_trades,
            "unprocessed_trades": self.unprocessed_trades,
            "status": self.status,
            "halted_trade_index": self.halted_trade_index,
            "trade_r": list(self.trade_r),
            "trade_pnl_eur": list(self.trade_pnl_eur),
            "equity_curve_eur": list(self.equity_curve_eur),
            "final_balance_eur": self.final_balance_eur,
            "cash_pnl_eur": self.cash_pnl_eur,
            "return_pct": self.return_pct,
            "peak_balance_eur": self.peak_balance_eur,
            "minimum_balance_eur": self.minimum_balance_eur,
            "max_drawdown_eur": self.max_drawdown_eur,
            "max_drawdown_pct_of_peak": self.max_drawdown_pct_of_peak,
            "ledger_sha256": self.ledger_sha256,
            "simulated_only": True,
            "broker_balance": False,
            "execution_capability": "NONE",
            "order_execution_enabled": False,
        }


def _drawdown_stats(equity: Sequence[float]) -> tuple[float, float, float]:
    peak = float(equity[0])
    peak_balance = peak
    max_dd = 0.0
    max_dd_pct = 0.0
    for balance in equity:
        value = float(balance)
        peak = max(peak, value)
        peak_balance = max(peak_balance, peak)
        drawdown = peak - value
        drawdown_pct = drawdown / peak if peak > 0.0 else math.inf
        max_dd = max(max_dd, drawdown)
        max_dd_pct = max(max_dd_pct, drawdown_pct)
    return peak_balance, max_dd, max_dd_pct


def simulate_fixed_risk_cash_ledger(
    trade_r: Sequence[float],
    *,
    starting_balance_eur: float,
    fixed_risk_eur: float,
) -> ShadowCashLedger:
    """Translate a chronological R sequence into a simulated fixed-risk EUR ledger.

    This is a SHADOW/research accounting view only. It never reads or mutates a
    broker account and never submits orders. A trade is not processed if the
    pre-trade simulated balance is below the fixed EUR risk budget.
    """
    start = float(starting_balance_eur)
    risk = float(fixed_risk_eur)
    values = tuple(float(value) for value in trade_r)
    if not math.isfinite(start) or start <= 0.0:
        raise ValueError("starting_balance_eur must be finite and positive")
    if not math.isfinite(risk) or risk <= 0.0:
        raise ValueError("fixed_risk_eur must be finite and positive")
    if risk > start:
        raise ValueError("fixed_risk_eur cannot exceed starting balance")
    if any(not math.isfinite(value) for value in values):
        raise ValueError("trade_r must contain only finite values")

    balance = start
    equity = [start]
    processed_r: list[float] = []
    pnl_values: list[float] = []
    status = COMPLETE
    halted: int | None = None

    for index, r_value in enumerate(values):
        if balance < risk:
            status = CAPITAL_INSUFFICIENT
            halted = index
            break
        pnl = r_value * risk
        balance += pnl
        processed_r.append(r_value)
        pnl_values.append(pnl)
        equity.append(balance)
        if balance < 0.0:
            status = NEGATIVE_BALANCE_AFTER_TRADE
            halted = index
            break

    peak_balance, max_dd, max_dd_pct = _drawdown_stats(equity)
    cash_pnl = balance - start
    return_pct = cash_pnl / start
    identity = {
        "schema_version": "DAXLAB_SHADOW_CASH_LEDGER_V1",
        "mode": "FIXED_RISK_EUR",
        "starting_balance_eur": start,
        "fixed_risk_eur": risk,
        "requested_trade_r": list(values),
        "processed_trade_r": processed_r,
        "trade_pnl_eur": pnl_values,
        "equity_curve_eur": equity,
        "status": status,
        "halted_trade_index": halted,
    }
    ledger_sha256 = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    return ShadowCashLedger(
        mode="FIXED_RISK_EUR",
        starting_balance_eur=start,
        fixed_risk_eur=risk,
        requested_trades=len(values),
        processed_trades=len(processed_r),
        unprocessed_trades=len(values) - len(processed_r),
        status=status,
        halted_trade_index=halted,
        trade_r=tuple(processed_r),
        trade_pnl_eur=tuple(pnl_values),
        equity_curve_eur=tuple(equity),
        final_balance_eur=balance,
        cash_pnl_eur=cash_pnl,
        return_pct=return_pct,
        peak_balance_eur=peak_balance,
        minimum_balance_eur=float(min(equity)),
        max_drawdown_eur=max_dd,
        max_drawdown_pct_of_peak=max_dd_pct,
        ledger_sha256=ledger_sha256,
    )
