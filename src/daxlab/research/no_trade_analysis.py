"""Deterministic diagnostics for NO_TRADE protection and opportunity cost."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import StrEnum
from math import isfinite


class NoTradeOutcome(StrEnum):
    PROTECTED_LOSS = "PROTECTED_LOSS"
    MISSED_WINNER = "MISSED_WINNER"
    NEUTRAL = "NEUTRAL"
    UNOBSERVABLE = "UNOBSERVABLE"


@dataclass(frozen=True, slots=True)
class NoTradeEvidence:
    observation_id: str
    blocker: str
    hypothetical_r: float | None = None
    regime: str | None = None
    structure: str | None = None

    def __post_init__(self) -> None:
        if self.hypothetical_r is not None and not isfinite(self.hypothetical_r):
            raise ValueError("hypothetical_r must be finite when supplied")
        if not self.observation_id:
            raise ValueError("observation_id is required")
        if not self.blocker:
            raise ValueError("blocker is required")


@dataclass(frozen=True, slots=True)
class NoTradeSummary:
    observations: int
    protected_losses: int
    missed_winners: int
    neutral: int
    unobservable: int
    protected_r: float
    missed_r: float
    net_counterfactual_r: float
    blocker_counts: tuple[tuple[str, int], ...]


def classify_no_trade(evidence: NoTradeEvidence) -> NoTradeOutcome:
    """Classify counterfactual evidence without changing the underlying filter."""
    if evidence.hypothetical_r is None:
        return NoTradeOutcome.UNOBSERVABLE
    if evidence.hypothetical_r < 0:
        return NoTradeOutcome.PROTECTED_LOSS
    if evidence.hypothetical_r > 0:
        return NoTradeOutcome.MISSED_WINNER
    return NoTradeOutcome.NEUTRAL


def summarize_no_trades(rows: list[NoTradeEvidence]) -> NoTradeSummary:
    ids = [row.observation_id for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate observation_id in NO_TRADE evidence")

    blockers: Counter[str] = Counter()
    protected_losses = missed_winners = neutral = unobservable = 0
    protected_r = missed_r = 0.0

    for row in rows:
        blockers[row.blocker] += 1
        outcome = classify_no_trade(row)
        if outcome is NoTradeOutcome.PROTECTED_LOSS:
            protected_losses += 1
            assert row.hypothetical_r is not None
            protected_r += abs(row.hypothetical_r)
        elif outcome is NoTradeOutcome.MISSED_WINNER:
            missed_winners += 1
            assert row.hypothetical_r is not None
            missed_r += row.hypothetical_r
        elif outcome is NoTradeOutcome.NEUTRAL:
            neutral += 1
        else:
            unobservable += 1

    return NoTradeSummary(
        observations=len(rows),
        protected_losses=protected_losses,
        missed_winners=missed_winners,
        neutral=neutral,
        unobservable=unobservable,
        protected_r=protected_r,
        missed_r=missed_r,
        net_counterfactual_r=protected_r - missed_r,
        blocker_counts=tuple(sorted(blockers.items())),
    )
