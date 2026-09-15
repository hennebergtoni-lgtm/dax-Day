"""E research-only opportunity labels and fixed-cash risk comparisons.

There is intentionally no quantity, RiskRequest, ExecutionIntent, arming method,
broker adapter or runtime policy mutation. Labels never choose cash risk.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

from daxlab.research.boost001 import FixedCashResearchConfig, fixed_cash_tail_research, simulate_fixed_cash
from daxlab.research.failure_analysis import trade_sequence_dna
from daxlab.research.turbo_contract import (
    Provenance, count, digest, finite, read_utc, research_payload, token, tokens,
)

HARD_CATEGORIES = ('ACCOUNT_SURVIVAL', 'TOTAL_EXPOSURE', 'DAY_LOSS', 'WEEK_LOSS',
                   'DRAWDOWN_STOP', 'MARGIN', 'PROTECTION', 'INSTRUMENT_ACCOUNT',
                   'DATA_FRESHNESS', 'INVENTORY', 'TRANSPORT', 'RECONCILIATION',
                   'KILL_SWITCH', 'LIVE_BLOCK', 'PTC', 'BROKER_ECONOMICS')
FUTURE_REQUIREMENTS = ('RISK_RESEARCH_PROMOTION', 'STEP2239', 'STEP2240',
                       'BROKER_ECONOMICS', 'INDEPENDENT_G', 'HUMAN_AUTHORIZATION',
                       'TTL', 'MARKET_INSTRUMENT_SESSION_SCOPE', 'EXPLICIT_MAXIMUM',
                       'PTC', 'KILL_SWITCH', 'CLEAR_INVENTORY', 'FRESH_DATA',
                       'NO_LOSS_CHASING', 'NO_MARTINGALE')


@dataclass(frozen=True, slots=True)
class RiskResearchSpec:
    hypothesis_id: str
    declared_at: str
    holdout_available_at: str
    baseline_cash_risk: float
    candidates: tuple[tuple[str, float], ...]
    initial_capital: float
    capital_floor: float
    hard_research_cash_cap: float
    max_drawdown: float
    max_floor_hit_rate: float
    minimum_sample: int
    paths: int
    block_length: int
    seed: int
    min_gain_per_added_drawdown: float = 1.0

    def __post_init__(self):
        token(self.hypothesis_id)
        if read_utc(self.declared_at) >= read_utc(self.holdout_available_at):
            raise ValueError('RISK_PREDECLARATION_REQUIRED')
        for v in (self.baseline_cash_risk, self.initial_capital, self.hard_research_cash_cap,
                  self.max_drawdown):
            finite(v, 0.000001)
        finite(self.capital_floor, 0)
        finite(self.max_floor_hit_rate, 0)
        finite(self.min_gain_per_added_drawdown, 0)
        if self.max_floor_hit_rate > 1 or self.capital_floor >= self.initial_capital:
            raise ValueError('RISK_ENVELOPE_INVALID')
        if self.baseline_cash_risk > self.hard_research_cash_cap:
            raise ValueError('BASELINE_EXCEEDS_ENVELOPE')
        if type(self.candidates) is not tuple or not 1 <= len(self.candidates) <= 12:
            raise ValueError('RISK_CANDIDATE_BOUND')
        tokens(tuple(k for k, _ in self.candidates))
        if len({cash for _, cash in self.candidates}) != len(self.candidates):
            raise ValueError('DUPLICATE_RISK_TRIAL')
        for label, cash in self.candidates:
            token(label)
            finite(cash, self.baseline_cash_risk)
            if cash > self.hard_research_cash_cap:
                raise ValueError('RESEARCH_HARD_CAP')
        count(self.minimum_sample, 2)
        count(self.paths, 1, 10000)
        count(self.block_length, 1)
        count(self.seed)

    @property
    def fingerprint(self):
        return digest(asdict(self))


def evaluate_risk_research(spec: RiskResearchSpec, *, gross_r: tuple[float, ...],
                           cost_r: tuple[float, ...], regimes: tuple[str, ...],
                           splits: tuple[str, ...], provenance: Provenance) -> dict:
    spec.__post_init__()
    provenance.__post_init__()
    if provenance.evidence_scope not in {'SYNTHETIC', 'REPLAY'}:
        raise ValueError('RISK_RESEARCH_SCOPE')
    if read_utc(provenance.observed_at) < read_utc(spec.holdout_available_at):
        raise ValueError('RISK_RESULT_PRECEDES_HOLDOUT')
    n = len(gross_r)
    if n < 2 or len(cost_r) != n or len(regimes) != n or len(splits) != n:
        raise ValueError('RISK_DATA_ALIGNMENT')
    if n*spec.paths*3*(len(spec.candidates)+1) > 1_000_000:
        raise ValueError('RISK_WORK_BUDGET')
    if spec.block_length > n:
        raise ValueError('RISK_BLOCK_LENGTH')
    for v in gross_r:
        finite(v)
    for v in cost_r:
        finite(v, 0)
    if not set(splits) <= {'IS', 'OOS', 'WF'} or not {'OOS', 'WF'} <= set(splits):
        raise ValueError('RISK_OOS_WF_REQUIRED')
    for regime in regimes:
        token(regime)
    source = digest({'gross': gross_r, 'cost': cost_r, 'regimes': regimes, 'splits': splits,
                     'provenance': provenance.fingerprint})
    net = [g-c for g, c in zip(gross_r, cost_r)]
    # Never let IS profits hide an OOS/WF failure.
    oos = [r for r, s in zip(net, splits) if s in {'OOS', 'WF'}]
    validation_gross = [g for g, s in zip(gross_r, splits) if s in {'OOS', 'WF'}]
    validation_cost = [c for c, s in zip(cost_r, splits) if s in {'OOS', 'WF'}]
    def model(cash):
        cfg = FixedCashResearchConfig(spec.initial_capital, cash, spec.capital_floor, len(oos))
        return fixed_cash_tail_research(validation_gross, validation_cost, cfg,
            source_sha256=source, paths=spec.paths, seed=spec.seed,
            mode='CIRCULAR_BLOCK', block_length=min(spec.block_length, len(oos)))
    baseline = model(spec.baseline_cash_risk)
    results = []
    for label, cash in spec.candidates:
        tail = model(cash)
        failures = []
        if len(oos) < spec.minimum_sample:
            failures.append('SAMPLE')
        for split in ('OOS', 'WF'):
            if sum(s == split for s in splits) < spec.minimum_sample:
                failures.append(split+'_SAMPLE')
            if sum(r for r, s in zip(net, splits) if s == split) <= 0:
                failures.append(split)
        stresses = tail['cost_stresses']
        for factor in ('1.5', '2.0'):
            if stresses[factor]['final_capital']['median'] <= spec.initial_capital:
                failures.append('COST_' + factor)
        if any(v['max_cash_drawdown']['worst_observed'] > spec.max_drawdown
               or v['floor_hit_rate'] > spec.max_floor_hit_rate for v in stresses.values()):
            failures.append('TAIL_SURVIVAL')
        incremental = stresses['1.0']['final_capital']['median'] - baseline['cost_stresses']['1.0']['final_capital']['median']
        if incremental <= 0:
            failures.append('NO_INCREMENTAL_ECONOMIC_VALUE')
        added_dd = max(0, stresses['2.0']['max_cash_drawdown']['worst_observed']
                       - baseline['cost_stresses']['2.0']['max_cash_drawdown']['worst_observed'])
        if incremental < added_dd * spec.min_gain_per_added_drawdown:
            failures.append('ECONOMIC_GAIN_DOES_NOT_JUSTIFY_DRAWDOWN')
        dna = trade_sequence_dna(oos)
        if dna['top_winner_removal']['1']['net_r_after_removal'] <= 0:
            failures.append('TOP_TRADE_DEPENDENCY')
        concentrated = max(regimes.count(r) for r in set(regimes)) / n
        cfg = FixedCashResearchConfig(spec.initial_capital, cash, spec.capital_floor, len(oos))
        observed = simulate_fixed_cash(oos, cfg)
        results.append(dict(label=label, cash_risk_hypothesis=cash, failures=failures,
            verdict='REJECT' if failures else 'MORE_EVIDENCE_REQUIRED',
            conditional_candidate=not failures, incremental_median_net_cash=incremental,
            incremental_stressed_drawdown=added_dd,
            regime_concentration=concentrated, sequence=dna, observed_path=observed, tail=tail))
    return research_payload('TURBO_RISK_RESEARCH', spec=asdict(spec), spec_fingerprint=spec.fingerprint,
        source_fingerprint=source, provenance=asdict(provenance), sample_size=len(oos),
        baseline=baseline, candidates=results,
        inference='CONDITIONAL_RESEARCH_NOT_EDGE_OR_SURVIVAL_PROOF',
        cost_cash_scaling_assumption='EXPLICIT_LINEAR_R_SCALING_NO_LIQUIDITY_OR_MARGIN_MODEL',
        g_judgment='REQUIRED_SEPARATELY', no_quantity=True)


@dataclass(frozen=True, slots=True)
class Opportunity:
    knowledge_cutoff_at: str
    feature_available_at: str
    provenance: Provenance
    regime: str
    quality: tuple[tuple[str, int], ...]
    historical_sample: int
    minimum_sample: int
    oos_wf_status: str
    cost_status: str
    tail_status: str
    hard_checks: tuple[tuple[str, str], ...]
    loss_streak: int
    drawdown: float
    contradictions: tuple[str, ...] = ()

    def __post_init__(self):
        self.provenance.__post_init__()
        token(self.regime)
        if read_utc(self.feature_available_at) > read_utc(self.knowledge_cutoff_at):
            raise ValueError('OPPORTUNITY_LOOKAHEAD')
        if read_utc(self.provenance.generated_at) > read_utc(self.knowledge_cutoff_at):
            raise ValueError('RESEARCH_NOT_YET_KNOWN')
        count(self.historical_sample)
        count(self.minimum_sample, 2)
        count(self.loss_streak)
        finite(self.drawdown, 0)
        tokens(self.contradictions)
        if type(self.quality) is not tuple or {k for k, _ in self.quality} != {'REGIME', 'STRUCTURE', 'ENTRY'} or len(self.quality) != 3:
            raise ValueError('OPPORTUNITY_QUALITY_SCHEMA')
        for _, v in self.quality:
            count(v, 0, 2)
        for v in (self.oos_wf_status, self.cost_status, self.tail_status):
            if v not in {'PASS', 'FAIL', 'UNKNOWN'}:
                raise ValueError('OPPORTUNITY_EVIDENCE_STATUS')
        if type(self.hard_checks) is not tuple or len({k for k, _ in self.hard_checks}) != len(self.hard_checks):
            raise ValueError('OPPORTUNITY_DUPLICATE_HARD_CHECK')
        if any(k not in HARD_CATEGORIES or v not in {'PASS', 'FAIL', 'UNKNOWN'} for k, v in self.hard_checks):
            raise ValueError('OPPORTUNITY_HARD_CHECK_SCHEMA')


def evaluate_opportunity(observation: Opportunity) -> dict:
    observation.__post_init__()
    checks = dict(observation.hard_checks)
    blockers = [key for key in HARD_CATEGORIES if checks.get(key) != 'PASS']
    if not observation.provenance.matches(observation.provenance,
            now=observation.knowledge_cutoff_at, scopes=('SYNTHETIC', 'REPLAY')):
        blockers.append('EVIDENCE_NOT_FRESH_RESEARCH')
    statuses = (observation.oos_wf_status, observation.cost_status, observation.tail_status)
    if blockers or observation.tail_status == 'FAIL':
        mode = 'TURBO_BLOCKED'
    elif observation.loss_streak or observation.drawdown > 0:
        mode = 'NORMAL_ONLY'
    elif observation.historical_sample < observation.minimum_sample or 'UNKNOWN' in statuses:
        mode = 'INSUFFICIENT_EVIDENCE'
    elif 'FAIL' in statuses:
        mode = 'NORMAL_ONLY'
    elif observation.contradictions:
        mode = 'INSUFFICIENT_EVIDENCE'
    else:
        minimum = min(v for _, v in observation.quality)
        mode = 'TURBO_CANDIDATE' if minimum == 2 else 'BOOST_CANDIDATE' if minimum == 1 else 'NORMAL_ONLY'
    return research_payload('OPPORTUNITY', opportunity_mode=mode,
        observation_fingerprint=digest(asdict(observation)), provenance=asdict(observation.provenance),
        why='CAUSAL_QUALITY_SCREEN_NOT_POSITION_SIZING',
        supporting_dimensions=[k for k, v in observation.quality if v == 2],
        contradicting_dimensions=list(observation.contradictions),
        sample_adequacy={'observed': observation.historical_sample, 'required': observation.minimum_sample},
        evidence_scope=observation.provenance.evidence_scope, regime_binding=observation.regime,
        oos_wf_status=observation.oos_wf_status, cost_sensitivity=observation.cost_status,
        tail_risk_status=observation.tail_status, hard_blockers=blockers,
        uncertainty_class='CONDITIONAL_RESEARCH_ONLY',
        falsifiers=['OOS_DEGRADATION', 'COST_EDGE_LOSS', 'TAIL_BREACH', 'REGIME_DRIFT'],
        g_status='REQUIRED_SEPARATELY', confidence_to_size_mapping=False)


def future_button_contract(state: str) -> dict:
    if state not in {'TURBO_OFF', 'TURBO_AVAILABLE', 'TURBO_RECOMMENDED', 'TURBO_ARMED', 'TURBO_BLOCKED'}:
        raise ValueError('TURBO_BUTTON_STATE')
    return research_payload('FUTURE_BUTTON_CONTRACT', research_state=state,
                            effective_state='TURBO_OFF', actuation_available=False,
                            unmet_separate_requirements=list(FUTURE_REQUIREMENTS))
