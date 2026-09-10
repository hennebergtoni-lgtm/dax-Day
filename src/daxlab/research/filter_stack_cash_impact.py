from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Sequence

import numpy as np

from daxlab.research.filter_stack_ablation import FilterStackAblation, evaluate_filter_stack
from daxlab.research.shadow_cash_ledger import (
    COMPLETE,
    ShadowCashLedger,
    simulate_fixed_risk_cash_ledger,
)


COMPLETE_COMPARISON = "COMPLETE_COMPARISON"
INCOMPLETE_CAPITAL_PATH = "INCOMPLETE_CAPITAL_PATH"


@dataclass(frozen=True)
class FilterStackCashImpact:
    stack: FilterStackAblation
    baseline_ledger: ShadowCashLedger
    filtered_ledger: ShadowCashLedger
    comparison_status: str
    final_balance_delta_eur: float
    cash_pnl_delta_eur: float
    max_drawdown_delta_eur: float
    final_trade_survival_ratio: float
    impact_sha256: str

    def to_payload(self) -> dict[str, object]:
        return {
            "schema_version": "DAXLAB_FILTER_STACK_CASH_IMPACT_V1",
            "stack": self.stack.to_payload(),
            "baseline_ledger": self.baseline_ledger.to_payload(),
            "filtered_ledger": self.filtered_ledger.to_payload(),
            "comparison_status": self.comparison_status,
            "final_balance_delta_eur": self.final_balance_delta_eur,
            "cash_pnl_delta_eur": self.cash_pnl_delta_eur,
            "max_drawdown_delta_eur": self.max_drawdown_delta_eur,
            "final_trade_survival_ratio": self.final_trade_survival_ratio,
            "impact_sha256": self.impact_sha256,
            "simulated_only": True,
            "broker_balance": False,
            "automatic_keep_drop_decision": None,
            "execution_capability": "NONE",
            "order_execution_enabled": False,
        }


def evaluate_filter_stack_cash_impact(
    baseline_r: Sequence[float],
    filters: Sequence[tuple[str, Sequence[bool]]],
    *,
    starting_balance_eur: float,
    fixed_risk_eur: float,
) -> FilterStackCashImpact:
    """Compare identical fixed-risk EUR accounting before and after a filter stack."""
    baseline_values = tuple(float(value) for value in baseline_r)
    stack = evaluate_filter_stack(baseline_values, filters)

    cumulative_mask = np.ones(len(baseline_values), dtype=bool)
    for _, raw_mask in filters:
        mask = np.asarray(tuple(bool(value) for value in raw_mask), dtype=bool)
        cumulative_mask = np.logical_and(cumulative_mask, mask)
    filtered_r = tuple(
        value for value, keep in zip(baseline_values, cumulative_mask, strict=True) if bool(keep)
    )

    baseline_ledger = simulate_fixed_risk_cash_ledger(
        baseline_values,
        starting_balance_eur=starting_balance_eur,
        fixed_risk_eur=fixed_risk_eur,
    )
    filtered_ledger = simulate_fixed_risk_cash_ledger(
        filtered_r,
        starting_balance_eur=starting_balance_eur,
        fixed_risk_eur=fixed_risk_eur,
    )
    comparison_status = (
        COMPLETE_COMPARISON
        if baseline_ledger.status == COMPLETE and filtered_ledger.status == COMPLETE
        else INCOMPLETE_CAPITAL_PATH
    )

    final_balance_delta = filtered_ledger.final_balance_eur - baseline_ledger.final_balance_eur
    cash_pnl_delta = filtered_ledger.cash_pnl_eur - baseline_ledger.cash_pnl_eur
    max_drawdown_delta = filtered_ledger.max_drawdown_eur - baseline_ledger.max_drawdown_eur

    identity = {
        "schema_version": "DAXLAB_FILTER_STACK_CASH_IMPACT_V1",
        "stack_sha256": stack.stack_sha256,
        "baseline_ledger_sha256": baseline_ledger.ledger_sha256,
        "filtered_ledger_sha256": filtered_ledger.ledger_sha256,
        "comparison_status": comparison_status,
        "final_balance_delta_eur": final_balance_delta,
        "cash_pnl_delta_eur": cash_pnl_delta,
        "max_drawdown_delta_eur": max_drawdown_delta,
        "final_trade_survival_ratio": stack.final_survival_ratio,
    }
    impact_sha256 = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    return FilterStackCashImpact(
        stack=stack,
        baseline_ledger=baseline_ledger,
        filtered_ledger=filtered_ledger,
        comparison_status=comparison_status,
        final_balance_delta_eur=final_balance_delta,
        cash_pnl_delta_eur=cash_pnl_delta,
        max_drawdown_delta_eur=max_drawdown_delta,
        final_trade_survival_ratio=stack.final_survival_ratio,
        impact_sha256=impact_sha256,
    )
