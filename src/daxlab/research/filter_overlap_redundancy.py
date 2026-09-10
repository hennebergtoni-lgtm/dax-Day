"""Pairwise overlap diagnostics for restrictive filter masks.

A keep mask uses True=trade survives and False=trade blocked.  This module is
research-only and does not automatically remove filters.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from itertools import combinations
from typing import Sequence


@dataclass(frozen=True)
class FilterMask:
    filter_id: str
    keep_mask: tuple[bool, ...]


@dataclass(frozen=True)
class PairOverlap:
    filter_a: str
    filter_b: str
    blocked_a: int
    blocked_b: int
    blocked_intersection: int
    blocked_union: int
    jaccard_blocked: float
    containment_a_in_b: float
    containment_b_in_a: float


@dataclass(frozen=True)
class FilterOverlapReport:
    n_trades: int
    pairs: tuple[PairOverlap, ...]
    report_sha256: str
    automatic_removal: bool = False
    research_only: bool = True
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def to_payload(self) -> dict[str, object]:
        return {
            "schema_version": "DAXLAB_FILTER_OVERLAP_REDUNDANCY_V1",
            "n_trades": self.n_trades,
            "pairs": [asdict(pair) for pair in self.pairs],
            "report_sha256": self.report_sha256,
            "automatic_removal": self.automatic_removal,
            "research_only": self.research_only,
            "execution_capability": self.execution_capability,
            "order_execution_enabled": self.order_execution_enabled,
        }


def _containment(intersection: int, blocked_count: int) -> float:
    # Empty blocked set has no evidence of containment/redundancy.
    return 0.0 if blocked_count == 0 else intersection / blocked_count


def evaluate_filter_overlap(filters: Sequence[FilterMask]) -> FilterOverlapReport:
    items = tuple(filters)
    if len(items) < 2:
        raise ValueError("at least two filters are required")
    ids = [item.filter_id.strip() for item in items]
    if any(not item for item in ids):
        raise ValueError("filter_id must be non-empty")
    if len(set(ids)) != len(ids):
        raise ValueError("filter_id values must be unique")

    n_trades = len(items[0].keep_mask)
    if any(len(item.keep_mask) != n_trades for item in items):
        raise ValueError("all keep masks must have identical length")

    pairs: list[PairOverlap] = []
    for a, b in combinations(items, 2):
        blocked_a_set = {i for i, keep in enumerate(a.keep_mask) if not keep}
        blocked_b_set = {i for i, keep in enumerate(b.keep_mask) if not keep}
        intersection = len(blocked_a_set & blocked_b_set)
        union = len(blocked_a_set | blocked_b_set)
        jaccard = 0.0 if union == 0 else intersection / union
        pairs.append(
            PairOverlap(
                filter_a=a.filter_id,
                filter_b=b.filter_id,
                blocked_a=len(blocked_a_set),
                blocked_b=len(blocked_b_set),
                blocked_intersection=intersection,
                blocked_union=union,
                jaccard_blocked=jaccard,
                containment_a_in_b=_containment(intersection, len(blocked_a_set)),
                containment_b_in_a=_containment(intersection, len(blocked_b_set)),
            )
        )

    identity = {
        "schema_version": "DAXLAB_FILTER_OVERLAP_REDUNDANCY_V1",
        "filters": [
            {"filter_id": item.filter_id, "keep_mask": list(item.keep_mask)} for item in items
        ],
        "pairs": [asdict(pair) for pair in pairs],
    }
    digest = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return FilterOverlapReport(n_trades=n_trades, pairs=tuple(pairs), report_sha256=digest)
