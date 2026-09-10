"""Descriptive risk observations for a simulated SHADOW cash ledger.

No thresholds or trading actions are defined here. The report only exposes evidence that
can later support a separately predeclared risk policy.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from daxlab.research.shadow_cash_ledger import ShadowCashLedger


@dataclass(frozen=True, slots=True)
class ShadowRiskObservation:
    ledger_sha256: str
    processed_trades: int
    return_pct: float
    max_drawdown_eur: float
    max_drawdown_pct_of_peak: float
    peak_balance_eur: float
    minimum_balance_eur: float
    capital_halt_observed: bool
    report_sha256: str
    descriptive_only: bool = True
    threshold_defined: bool = False
    automatic_halt: bool = False
    automatic_promotion: bool = False
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False


def build_shadow_risk_observation(ledger: ShadowCashLedger) -> ShadowRiskObservation:
    payload = ledger.to_payload()
    if payload["execution_capability"] != "NONE" or payload["order_execution_enabled"]:
        raise ValueError("SHADOW ledger must preserve NO_ORDER")
    if not payload["simulated_only"] or payload["broker_balance"]:
        raise ValueError("risk observation requires simulated-only ledger")

    capital_halt = ledger.processed_trades < ledger.requested_trades or ledger.status != "COMPLETE"
    identity = {
        "schema_version": "DAXLAB_SHADOW_RISK_OBSERVATION_V1",
        "ledger_sha256": ledger.ledger_sha256,
        "processed_trades": ledger.processed_trades,
        "return_pct": ledger.return_pct,
        "max_drawdown_eur": ledger.max_drawdown_eur,
        "max_drawdown_pct_of_peak": ledger.max_drawdown_pct_of_peak,
        "peak_balance_eur": ledger.peak_balance_eur,
        "minimum_balance_eur": ledger.minimum_balance_eur,
        "capital_halt_observed": capital_halt,
    }
    digest = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return ShadowRiskObservation(
        ledger_sha256=ledger.ledger_sha256,
        processed_trades=ledger.processed_trades,
        return_pct=ledger.return_pct,
        max_drawdown_eur=ledger.max_drawdown_eur,
        max_drawdown_pct_of_peak=ledger.max_drawdown_pct_of_peak,
        peak_balance_eur=ledger.peak_balance_eur,
        minimum_balance_eur=ledger.minimum_balance_eur,
        capital_halt_observed=capital_halt,
        report_sha256=digest,
    )
