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


def empirical_distribution(values: list[float]) -> dict[str, object]:
    """Observed linear-interpolated quantiles, never a tail confidence bound."""
    if any(type(v) not in (int, float) or not isfinite(v) for v in values):
        raise ValueError('distribution requires finite numeric observations')
    ordered = sorted(float(v) for v in values)

    def quantile(q: float) -> float | None:
        if not ordered:
            return None
        index = (len(ordered)-1)*q
        lower = int(index)
        upper = min(lower+1, len(ordered)-1)
        return ordered[lower] + (ordered[upper]-ordered[lower])*(index-lower)

    return {'count': len(ordered), 'median': quantile(.5), 'p90': quantile(.9),
            'p95': quantile(.95), 'p99': quantile(.99),
            'worst_observed': max(ordered) if ordered else None,
            'inference_state': 'UNVERIFIED_THRESHOLD' if ordered else 'INSUFFICIENT_SAMPLE',
            'quantile_method': 'EMPIRICAL_LINEAR_INTERPOLATION_NOT_POPULATION_TAIL_BOUND'}


def historical_risk_envelope(preflight) -> dict[str, object]:
    """Describe strict existing detail rows, keeping each WF/variant independent.

    Source MAE is signed non-positive; the risk distribution uses its magnitude.
    Normal ledger net-R cannot reveal gross R, stress costs, gaps or slippage.
    Overlapping positions and cross-WF chains are not invented into one account.
    """
    from datetime import datetime, date
    from daxlab.detail_import import _payload_hash
    from daxlab.detail_artifact_loader import DetailArtifactPreflight
    if not isinstance(preflight, DetailArtifactPreflight) or preflight.detail_kind != 'TRADES':
        raise ValueError('risk envelope requires existing TRADES artifact preflight')
    rows = preflight.planned_rows
    if preflight.observed_rows != len(rows):
        raise ValueError('risk envelope source row-count mismatch')
    if len({r.source_row_id for r in rows}) != len(rows):
        raise ValueError('duplicate risk-envelope source identity')
    groups = defaultdict(list)
    durations = []
    for row in rows:
        if row.detail_kind != 'TRADES' or _payload_hash(row.payload) != row.payload_sha256:
            raise ValueError('risk envelope mutated/non-trade detail row')
        p = row.payload
        if any(type(p[k]) not in (int, float) or not isfinite(p[k]) for k in ('r','mae_r','mfe_r')):
            raise ValueError('risk envelope non-finite excursion/return')
        if p['mae_r'] > 0 or p['mfe_r'] < 0:
            raise ValueError('risk envelope excursion sign mismatch')
        entry, exit_ = (datetime.fromisoformat(str(p[k])) for k in ('entry_time_utc','exit_time_utc'))
        if entry.tzinfo is None or exit_.tzinfo is None or entry.utcoffset().total_seconds() != 0 or exit_.utcoffset().total_seconds() != 0 or exit_ < entry:
            raise ValueError('risk envelope incoherent entry/exit time')
        durations.append((exit_-entry).total_seconds())
        groups[(p['wf'],p['variant_index'])].append(p)
    sequences = []
    drawdowns = []
    sessions = defaultdict(list)
    weeks = defaultdict(list)
    for (wf, variant), items in sorted(groups.items()):
        ordered = sorted(items, key=lambda p: (p['entry_time_utc'],p['exit_time_utc']))
        overlap = any(a['exit_time_utc'] > b['entry_time_utc'] for a,b in zip(ordered,ordered[1:]))
        if overlap:
            sequences.append({'wf':wf, 'variant':variant, 'state':'UNKNOWN_OVERLAPPING_TRADES', 'max_loss_streak':None})
            continue
        streak = maximum = 0
        equity = peak = 0.0
        for p in ordered:
            streak = streak+1 if p['r'] < 0 else 0
            maximum = max(maximum,streak)
            equity += p['r']
            peak = max(peak,equity)
            drawdowns.append(peak-equity)
            sessions[(wf,variant,p['date'])].append(p['r'])
            week = date.fromisoformat(p['date']).isocalendar()[:2]
            weeks[(wf,variant,*week)].append(p['r'])
        sequences.append({'wf':wf, 'variant':variant, 'state':'LOSS_SEQUENCE_OBSERVED', 'max_loss_streak':maximum})

    def strata(items):
        return {'count':len(items), 'mae_magnitude_r':empirical_distribution([-p['mae_r'] for p in items]),
                'mfe_r':empirical_distribution([p['mfe_r'] for p in items]),
                'split_inference':'UNVERIFIED_THRESHOLD'}

    payloads = [r.payload for r in rows]
    result = {
        'schema_version':'DAXLAB_HISTORICAL_RISK_ENVELOPE_V1', 'scope':'STATIC_DERIVED_RESEARCH_NOT_RUNTIME_RISK_OR_BROKER_FACT',
        'source_sha256':preflight.observed_sha256, 'observed_rows':len(rows),
        'evidence_state':'TAIL_RISK_OBSERVED' if rows else 'INSUFFICIENT_SAMPLE',
        **strata(payloads), 'duration_seconds':empirical_distribution(durations),
        'by_side':{side:strata([p for p in payloads if p['side']==side]) for side in ('long','short')},
        'unavailable_splits':{'regime':'UNKNOWN', 'structure':'UNKNOWN', 'setup':'UNKNOWN', 'OR5_OR15':'UNKNOWN_REQUIRES_PINNED_SELECTED_VARIANT_JOIN'},
        'loss_sequences':sequences,
        'max_observed_loss_streak':max((s['max_loss_streak'] for s in sequences if s['max_loss_streak'] is not None),default=None),
        'loss_chain_scope':'WITHIN_NONOVERLAPPING_WF_VARIANT_ONLY_CROSS_WF_UNKNOWN',
        'session_loss_chains':[{'wf':k[0],'variant':k[1],'session_date':k[2],'net_r':sum(v),'trades':len(v)} for k,v in sorted(sessions.items())],
        'weekly_loss_chains':[{'wf':k[0],'variant':k[1],'iso_year':k[2],'iso_week':k[3],'net_r':sum(v),'trades':len(v)} for k,v in sorted(weeks.items())],
        'drawdown_r':empirical_distribution(drawdowns), 'drawdown_scope':'TRADE_BOUNDARY_NET_R_WITHIN_WF_VARIANT_NOT_CASH_DRAWDOWN',
        'cost_stress':{'normal':'SOURCE_NORMAL_NET_R_ONLY', 'stress_1_5x':'UNKNOWN_NO_PER_TRADE_COST_EVIDENCE', 'stress_2x':'UNKNOWN_NO_PER_TRADE_COST_EVIDENCE'},
        'slippage_gap':'UNKNOWN_NOT_DERIVABLE_FROM_MAE_OR_AGGREGATE_NET_R',
        'survival_verdict':'UNVERIFIED_THRESHOLD', 'execution_capability':'NONE', 'order_execution_enabled':False,
    }
    return result
