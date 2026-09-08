"""Pure diagnostic primitives for FAIL001 trade/outcome analysis.

These helpers classify supplied evidence. They do not mutate strategy parameters,
select new thresholds, or promote research findings.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from enum import StrEnum
from math import isfinite


class OutcomeClass(StrEnum):
    WIN = "WIN"
    LOSS = "LOSS"
    FLAT = "FLAT"


class FailureTag(StrEnum):
    STOP_OUT = "STOP_OUT"
    ADVERSE_EXCURSION = "ADVERSE_EXCURSION"
    MISSED_FAVORABLE_EXCURSION = "MISSED_FAVORABLE_EXCURSION"
    FALSE_BREAKOUT = "FALSE_BREAKOUT"
    FAILED_RETEST = "FAILED_RETEST"
    COST_SENSITIVE = "COST_SENSITIVE"


@dataclass(frozen=True, slots=True)
class TradeEvidence:
    trade_id: str
    r: float
    mfe_r: float | None = None
    mae_r: float | None = None
    entry_mode: str | None = None
    exit_reason: str | None = None
    structure_result: str | None = None
    or_atr_bucket: str | None = None
    prev_range_bucket: str | None = None
    cost_r_normal: float | None = None
    cost_r_stress_1_5x: float | None = None
    cost_r_stress_2x: float | None = None

    def __post_init__(self) -> None:
        values = (self.r, self.mfe_r, self.mae_r, self.cost_r_normal,
                  self.cost_r_stress_1_5x, self.cost_r_stress_2x)
        if any(value is not None and not isfinite(value) for value in values):
            raise ValueError("trade evidence must contain finite numeric values")


@dataclass(frozen=True, slots=True)
class ClassifiedTrade:
    trade_id: str
    outcome: OutcomeClass
    tags: tuple[FailureTag, ...]


def outcome_class(r_value: float) -> OutcomeClass:
    if r_value > 0:
        return OutcomeClass.WIN
    if r_value < 0:
        return OutcomeClass.LOSS
    return OutcomeClass.FLAT


def _cost_flip(trade: TradeEvidence) -> bool:
    values = (
        trade.cost_r_normal,
        trade.cost_r_stress_1_5x,
        trade.cost_r_stress_2x,
    )
    if any(value is None for value in values):
        return False
    assert all(value is not None for value in values)
    return values[0] > 0 and (values[1] <= 0 or values[2] <= 0)


def classify_trade(trade: TradeEvidence) -> ClassifiedTrade:
    """Apply descriptive, predeclared labels without changing trading rules."""
    tags: list[FailureTag] = []
    outcome = outcome_class(trade.r)

    if outcome is OutcomeClass.LOSS and trade.exit_reason == "stop":
        tags.append(FailureTag.STOP_OUT)
    if trade.mae_r is not None and trade.mae_r <= -1.0:
        tags.append(FailureTag.ADVERSE_EXCURSION)
    if outcome is OutcomeClass.LOSS and trade.mfe_r is not None and trade.mfe_r >= 1.0:
        tags.append(FailureTag.MISSED_FAVORABLE_EXCURSION)
    if trade.entry_mode == "breakout" and trade.structure_result == "false_breakout":
        tags.append(FailureTag.FALSE_BREAKOUT)
    if trade.entry_mode == "retest" and trade.structure_result == "failed_retest":
        tags.append(FailureTag.FAILED_RETEST)
    if _cost_flip(trade):
        tags.append(FailureTag.COST_SENSITIVE)

    return ClassifiedTrade(trade_id=trade.trade_id, outcome=outcome, tags=tuple(tags))


def classify_trades(trades: list[TradeEvidence]) -> tuple[ClassifiedTrade, ...]:
    ids = [trade.trade_id for trade in trades]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate trade_id in failure evidence")
    return tuple(classify_trade(trade) for trade in trades)


def tag_counts(classified: tuple[ClassifiedTrade, ...]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for item in classified:
        counts.update(tag.value for tag in item.tags)
    return dict(sorted(counts.items()))


def loss_concentration(
    trades: list[TradeEvidence], attribute: str
) -> dict[str, tuple[int, float]]:
    """Count losses and total loss-R by an explicitly supplied categorical field."""
    allowed = {"or_atr_bucket", "prev_range_bucket", "entry_mode", "structure_result"}
    if attribute not in allowed:
        raise ValueError(f"unsupported concentration attribute: {attribute}")
    grouped: dict[str, list[float]] = defaultdict(list)
    for trade in trades:
        if trade.r >= 0:
            continue
        key = getattr(trade, attribute) or "UNKNOWN"
        grouped[key].append(trade.r)
    return {
        key: (len(values), sum(values))
        for key, values in sorted(grouped.items())
    }


def excursion_summary(trades: list[TradeEvidence]) -> dict[str, float | int | None]:
    losses = [trade for trade in trades if trade.r < 0]
    mfe = [trade.mfe_r for trade in losses if trade.mfe_r is not None]
    mae = [trade.mae_r for trade in losses if trade.mae_r is not None]
    return {
        "loss_count": len(losses),
        "mean_loss_mfe_r": (sum(mfe) / len(mfe)) if mfe else None,
        "mean_loss_mae_r": (sum(mae) / len(mae)) if mae else None,
        "losses_with_mfe_ge_1r": sum(value >= 1.0 for value in mfe),
    }


def hypothesis_eligible(
    *, observations: int, distinct_periods: int, minimum_observations: int = 20,
    minimum_periods: int = 3,
) -> bool:
    """A conservative research gate, not a strategy-promotion decision."""
    return observations >= minimum_observations and distinct_periods >= minimum_periods
