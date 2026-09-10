"""Explicit, research-only readiness gate for filter candidates.

This module does not promote a candidate into paper or live trading.  Every
threshold must be supplied by the caller; there are deliberately no defaults.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math


@dataclass(frozen=True)
class ReadinessThresholds:
    min_changed_decisions: int
    min_trade_survival: float
    min_cash_delta_eur: float
    max_drawdown_worsening_eur: float

    def __post_init__(self) -> None:
        if self.min_changed_decisions < 1:
            raise ValueError("min_changed_decisions must be >= 1")
        if not 0.0 <= self.min_trade_survival <= 1.0:
            raise ValueError("min_trade_survival must be in [0, 1]")
        for value in (self.min_cash_delta_eur, self.max_drawdown_worsening_eur):
            if not math.isfinite(value):
                raise ValueError("thresholds must be finite")
        if self.max_drawdown_worsening_eur < 0:
            raise ValueError("max_drawdown_worsening_eur must be >= 0")


@dataclass(frozen=True)
class FilterCandidateEvidence:
    candidate_id: str
    activation_status: str
    changed_decisions: int
    trade_survival: float
    cash_delta_eur: float
    drawdown_delta_eur: float
    comparison_status: str
    pareto_dominated: bool


@dataclass(frozen=True)
class FilterCandidateReadiness:
    status: str
    blockers: tuple[str, ...]
    candidate_id: str
    evidence_hash: str
    research_only: bool = True
    automatic_promotion: bool = False
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False


def _canonical_hash(evidence: FilterCandidateEvidence, thresholds: ReadinessThresholds) -> str:
    payload = {
        "evidence": asdict(evidence),
        "thresholds": asdict(thresholds),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def evaluate_filter_candidate_readiness(
    evidence: FilterCandidateEvidence,
    thresholds: ReadinessThresholds,
) -> FilterCandidateReadiness:
    """Return research readiness without changing any trading authorization."""
    if not evidence.candidate_id.strip():
        raise ValueError("candidate_id must be non-empty")
    if evidence.changed_decisions < 0:
        raise ValueError("changed_decisions must be >= 0")
    if not 0.0 <= evidence.trade_survival <= 1.0:
        raise ValueError("trade_survival must be in [0, 1]")
    if not math.isfinite(evidence.cash_delta_eur) or not math.isfinite(evidence.drawdown_delta_eur):
        raise ValueError("cash/drawdown deltas must be finite")

    blockers: list[str] = []
    if evidence.activation_status != "ACTIVATED":
        blockers.append("FILTER_NOT_ACTIVATED")
    if evidence.changed_decisions < thresholds.min_changed_decisions:
        blockers.append("INSUFFICIENT_DECISION_EFFECT")
    if evidence.comparison_status != "COMPLETE_COMPARISON":
        blockers.append("INCOMPLETE_CAPITAL_PATH")
    if evidence.trade_survival < thresholds.min_trade_survival:
        blockers.append("TRADE_SURVIVAL_TOO_LOW")
    if evidence.cash_delta_eur < thresholds.min_cash_delta_eur:
        blockers.append("CASH_DELTA_BELOW_PROTOCOL")
    # Positive drawdown_delta_eur means the candidate drawdown worsened.
    if evidence.drawdown_delta_eur > thresholds.max_drawdown_worsening_eur:
        blockers.append("DRAWDOWN_WORSENING_ABOVE_PROTOCOL")
    if evidence.pareto_dominated:
        blockers.append("PARETO_DOMINATED")

    return FilterCandidateReadiness(
        status="RESEARCH_READY" if not blockers else "NOT_RESEARCH_READY",
        blockers=tuple(blockers),
        candidate_id=evidence.candidate_id,
        evidence_hash=_canonical_hash(evidence, thresholds),
    )
