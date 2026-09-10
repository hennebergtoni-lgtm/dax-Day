"""Leave-one-filter-out diagnostics for simplifying filter stacks.

The module compares a full stack with variants where exactly one filter is
removed. It never removes filters automatically and never changes execution
authorization.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Sequence

from daxlab.research.filter_stack_cash_impact import (
    COMPLETE_COMPARISON,
    FilterStackCashImpact,
    evaluate_filter_stack_cash_impact,
)


@dataclass(frozen=True)
class RemovalImpact:
    removed_filter_id: str
    comparison_status: str
    full_stack_cash_pnl_eur: float
    reduced_stack_cash_pnl_eur: float
    cash_pnl_delta_reduced_minus_full_eur: float
    final_balance_delta_reduced_minus_full_eur: float
    max_drawdown_delta_reduced_minus_full_eur: float
    trade_survival_delta_reduced_minus_full: float
    additional_surviving_trades: int
    reduced_stack_sha256: str


@dataclass(frozen=True)
class BackwardEliminationReport:
    full_stack_sha256: str
    full_stack_cash_impact_sha256: str
    removals: tuple[RemovalImpact, ...]
    report_sha256: str
    automatic_removal: bool = False
    research_only: bool = True
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def to_payload(self) -> dict[str, object]:
        return {
            "schema_version": "DAXLAB_BACKWARD_FILTER_ELIMINATION_V1",
            "full_stack_sha256": self.full_stack_sha256,
            "full_stack_cash_impact_sha256": self.full_stack_cash_impact_sha256,
            "removals": [asdict(item) for item in self.removals],
            "report_sha256": self.report_sha256,
            "automatic_removal": self.automatic_removal,
            "research_only": self.research_only,
            "execution_capability": self.execution_capability,
            "order_execution_enabled": self.order_execution_enabled,
        }


def evaluate_backward_filter_elimination(
    baseline_r: Sequence[float],
    filters: Sequence[tuple[str, Sequence[bool]]],
    *,
    starting_balance_eur: float,
    fixed_risk_eur: float,
) -> BackwardEliminationReport:
    items = tuple((str(filter_id), tuple(bool(v) for v in mask)) for filter_id, mask in filters)
    if not items:
        raise ValueError("at least one filter is required")
    ids = [filter_id.strip() for filter_id, _ in items]
    if any(not filter_id for filter_id in ids):
        raise ValueError("filter_id must be non-empty")
    if len(set(ids)) != len(ids):
        raise ValueError("filter_id values must be unique")

    full = evaluate_filter_stack_cash_impact(
        baseline_r,
        items,
        starting_balance_eur=starting_balance_eur,
        fixed_risk_eur=fixed_risk_eur,
    )

    removals: list[RemovalImpact] = []
    for remove_index, (removed_id, _) in enumerate(items):
        reduced_filters = tuple(item for index, item in enumerate(items) if index != remove_index)
        reduced: FilterStackCashImpact
        if reduced_filters:
            reduced = evaluate_filter_stack_cash_impact(
                baseline_r,
                reduced_filters,
                starting_balance_eur=starting_balance_eur,
                fixed_risk_eur=fixed_risk_eur,
            )
        else:
            # Keep the comparison contract intact by using an all-True neutral mask.
            neutral = (("__NO_FILTERS__", tuple(True for _ in baseline_r)),)
            reduced = evaluate_filter_stack_cash_impact(
                baseline_r,
                neutral,
                starting_balance_eur=starting_balance_eur,
                fixed_risk_eur=fixed_risk_eur,
            )

        status = (
            COMPLETE_COMPARISON
            if full.comparison_status == COMPLETE_COMPARISON
            and reduced.comparison_status == COMPLETE_COMPARISON
            else "INCOMPLETE_CAPITAL_PATH"
        )
        full_surviving = full.stack.final_kept_trades
        reduced_surviving = reduced.stack.final_kept_trades
        removals.append(
            RemovalImpact(
                removed_filter_id=removed_id,
                comparison_status=status,
                full_stack_cash_pnl_eur=full.filtered_ledger.cash_pnl_eur,
                reduced_stack_cash_pnl_eur=reduced.filtered_ledger.cash_pnl_eur,
                cash_pnl_delta_reduced_minus_full_eur=(
                    reduced.filtered_ledger.cash_pnl_eur - full.filtered_ledger.cash_pnl_eur
                ),
                final_balance_delta_reduced_minus_full_eur=(
                    reduced.filtered_ledger.final_balance_eur - full.filtered_ledger.final_balance_eur
                ),
                max_drawdown_delta_reduced_minus_full_eur=(
                    reduced.filtered_ledger.max_drawdown_eur - full.filtered_ledger.max_drawdown_eur
                ),
                trade_survival_delta_reduced_minus_full=(
                    reduced.stack.final_survival_ratio - full.stack.final_survival_ratio
                ),
                additional_surviving_trades=reduced_surviving - full_surviving,
                reduced_stack_sha256=reduced.stack.stack_sha256,
            )
        )

    identity = {
        "schema_version": "DAXLAB_BACKWARD_FILTER_ELIMINATION_V1",
        "full_stack_sha256": full.stack.stack_sha256,
        "full_stack_cash_impact_sha256": full.impact_sha256,
        "removals": [asdict(item) for item in removals],
    }
    digest = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return BackwardEliminationReport(
        full_stack_sha256=full.stack.stack_sha256,
        full_stack_cash_impact_sha256=full.impact_sha256,
        removals=tuple(removals),
        report_sha256=digest,
    )
