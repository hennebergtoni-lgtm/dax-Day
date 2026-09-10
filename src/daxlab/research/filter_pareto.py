from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Sequence

from daxlab.research.filter_stack_cash_impact import (
    COMPLETE_COMPARISON,
    FilterStackCashImpact,
)


@dataclass(frozen=True)
class ParetoCandidate:
    candidate_id: str
    impact_sha256: str
    cash_pnl_eur: float
    max_drawdown_eur: float
    trade_survival_ratio: float
    dominated_by: tuple[str, ...]
    non_dominated: bool

    def to_payload(self) -> dict[str, object]:
        return {
            "candidate_id": self.candidate_id,
            "impact_sha256": self.impact_sha256,
            "cash_pnl_eur": self.cash_pnl_eur,
            "max_drawdown_eur": self.max_drawdown_eur,
            "trade_survival_ratio": self.trade_survival_ratio,
            "dominated_by": list(self.dominated_by),
            "non_dominated": self.non_dominated,
        }


@dataclass(frozen=True)
class FilterParetoDiagnostic:
    candidates: tuple[ParetoCandidate, ...]
    frontier_candidate_ids: tuple[str, ...]
    baseline_ledger_sha256: str
    starting_balance_eur: float
    fixed_risk_eur: float
    diagnostic_sha256: str

    def to_payload(self) -> dict[str, object]:
        return {
            "schema_version": "DAXLAB_FILTER_PARETO_DIAGNOSTIC_V1",
            "objectives": {
                "maximize": ["cash_pnl_eur", "trade_survival_ratio"],
                "minimize": ["max_drawdown_eur"],
            },
            "candidates": [candidate.to_payload() for candidate in self.candidates],
            "frontier_candidate_ids": list(self.frontier_candidate_ids),
            "baseline_ledger_sha256": self.baseline_ledger_sha256,
            "starting_balance_eur": self.starting_balance_eur,
            "fixed_risk_eur": self.fixed_risk_eur,
            "diagnostic_sha256": self.diagnostic_sha256,
            "weighted_score_used": False,
            "automatic_winner_selected": False,
            "simulated_only": True,
            "broker_balance": False,
            "execution_capability": "NONE",
            "order_execution_enabled": False,
        }


def _dominates(left: FilterStackCashImpact, right: FilterStackCashImpact) -> bool:
    left_cash = left.filtered_ledger.cash_pnl_eur
    right_cash = right.filtered_ledger.cash_pnl_eur
    left_dd = left.filtered_ledger.max_drawdown_eur
    right_dd = right.filtered_ledger.max_drawdown_eur
    left_survival = left.final_trade_survival_ratio
    right_survival = right.final_trade_survival_ratio
    weak = left_cash >= right_cash and left_dd <= right_dd and left_survival >= right_survival
    strict = left_cash > right_cash or left_dd < right_dd or left_survival > right_survival
    return weak and strict


def evaluate_filter_pareto(
    candidates: Sequence[tuple[str, FilterStackCashImpact]],
) -> FilterParetoDiagnostic:
    """Return the non-dominated filter-stack candidates without scalar weighting."""
    if len(candidates) < 2:
        raise ValueError("at least two candidates are required for Pareto comparison")

    normalized: list[tuple[str, FilterStackCashImpact]] = []
    seen: set[str] = set()
    for raw_id, impact in candidates:
        candidate_id = raw_id.strip()
        if not candidate_id:
            raise ValueError("candidate_id must be non-empty")
        if candidate_id in seen:
            raise ValueError(f"duplicate candidate_id: {candidate_id}")
        seen.add(candidate_id)
        if impact.comparison_status != COMPLETE_COMPARISON:
            raise ValueError(f"candidate {candidate_id} has incomplete capital path")
        normalized.append((candidate_id, impact))

    first = normalized[0][1]
    baseline_hash = first.baseline_ledger.ledger_sha256
    starting_balance = first.baseline_ledger.starting_balance_eur
    fixed_risk = first.baseline_ledger.fixed_risk_eur
    for candidate_id, impact in normalized[1:]:
        if impact.baseline_ledger.ledger_sha256 != baseline_hash:
            raise ValueError(f"candidate {candidate_id} does not share baseline ledger identity")
        if impact.baseline_ledger.starting_balance_eur != starting_balance:
            raise ValueError(f"candidate {candidate_id} uses a different starting balance")
        if impact.baseline_ledger.fixed_risk_eur != fixed_risk:
            raise ValueError(f"candidate {candidate_id} uses a different fixed risk")

    output: list[ParetoCandidate] = []
    for candidate_id, impact in normalized:
        dominators = tuple(
            other_id
            for other_id, other in normalized
            if other_id != candidate_id and _dominates(other, impact)
        )
        output.append(
            ParetoCandidate(
                candidate_id=candidate_id,
                impact_sha256=impact.impact_sha256,
                cash_pnl_eur=impact.filtered_ledger.cash_pnl_eur,
                max_drawdown_eur=impact.filtered_ledger.max_drawdown_eur,
                trade_survival_ratio=impact.final_trade_survival_ratio,
                dominated_by=dominators,
                non_dominated=not dominators,
            )
        )

    frontier = tuple(item.candidate_id for item in output if item.non_dominated)
    identity = {
        "schema_version": "DAXLAB_FILTER_PARETO_DIAGNOSTIC_V1",
        "candidate_order": [candidate_id for candidate_id, _ in normalized],
        "impact_hashes": [impact.impact_sha256 for _, impact in normalized],
        "baseline_ledger_sha256": baseline_hash,
        "starting_balance_eur": starting_balance,
        "fixed_risk_eur": fixed_risk,
        "frontier_candidate_ids": list(frontier),
        "dominated_by": {item.candidate_id: list(item.dominated_by) for item in output},
    }
    diagnostic_sha256 = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return FilterParetoDiagnostic(
        candidates=tuple(output),
        frontier_candidate_ids=frontier,
        baseline_ledger_sha256=baseline_hash,
        starting_balance_eur=starting_balance,
        fixed_risk_eur=fixed_risk,
        diagnostic_sha256=diagnostic_sha256,
    )
