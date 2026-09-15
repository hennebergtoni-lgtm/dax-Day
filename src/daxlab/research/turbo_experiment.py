"""E: experiments, filter governance and diagnostic adversaries. No promotion."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from copy import deepcopy

from daxlab.research.filter_efficiency import evaluate_filter_efficiency
from daxlab.research.filter_overlap_redundancy import FilterMask, evaluate_filter_overlap
from daxlab.research.filter_stack_ablation import evaluate_filter_stack
from daxlab.research.turbo_contract import (
    Provenance, authorize, count, digest, finite, read_utc, require_sha,
    research_payload, token, tokens,
)
from daxlab.research.variant_trial_registry import TrialDeclaration, verify_trial_chain

STAGES = ('HYPOTHESIS', 'TESTABLE_SPEC', 'DATA_CAUSALITY_CHECK', 'BACKTEST', 'OOS',
          'WALK_FORWARD', 'COST_STRESS', 'ROBUSTNESS', 'SHADOW', 'DARK_PARALLEL',
          'CHAMPION_COMPARE')
CHECKS = ('OOS', 'WF', 'COST_1_5', 'COST_2', 'DRAWDOWN', 'LOSS_STREAK', 'TOP_TRADES',
          'PLATEAU', 'REGIME', 'SAMPLE', 'LOOKAHEAD', 'RECURSIVE', 'LEAKAGE',
          'MULTIPLE_TESTING', 'PBO', 'DSR', 'SPA', 'SAFETY', 'COMPLEXITY', 'REPRODUCIBLE')


@dataclass(frozen=True, slots=True)
class Hypothesis:
    hypothesis_id: str
    proposer_id: str
    mechanism: str
    falsifier: str
    layer: str
    trial_ids: tuple[str, ...]
    family_id: str
    holdout_ids: tuple[str, ...]
    declared_at: str
    data_available_at: str
    provenance: Provenance
    exploratory: bool = True
    minimum_sample: int = 40
    minimum_oos_net_r: float = 0.0
    holdout_windows: tuple[tuple[str, str, str], ...] = ()

    def __post_init__(self):
        for value in (self.hypothesis_id, self.proposer_id, self.mechanism, self.falsifier,
                      self.layer, self.family_id):
            token(value)
        if self.layer not in {'REGIME', 'STRUCTURE', 'ENTRY', 'RISK_RESEARCH'}:
            raise ValueError('HYPOTHESIS_PROTECTED_LAYER')
        tokens(self.trial_ids, required=True)
        tokens(self.holdout_ids, required=True)
        if type(self.exploratory) is not bool:
            raise ValueError('HYPOTHESIS_MODE')
        count(self.minimum_sample, 2)
        finite(self.minimum_oos_net_r)
        if not self.exploratory and read_utc(self.declared_at) >= read_utc(self.data_available_at):
            raise ValueError('HOLDOUT_ALREADY_SEEN')
        if type(self.holdout_windows) is not tuple or len(self.holdout_windows) > 64:
            raise ValueError('HOLDOUT_WINDOWS')
        for dataset, start, end in self.holdout_windows:
            require_sha(dataset)
            if read_utc(start) >= read_utc(end) or read_utc(end) > read_utc(self.data_available_at):
                raise ValueError('HOLDOUT_WINDOW_TIME')
        if not self.exploratory and (not self.holdout_windows
                or self.holdout_ids != tuple(digest(w) for w in self.holdout_windows)):
            raise ValueError('CONTENT_BOUND_HOLDOUT_REQUIRED')
        self.provenance.__post_init__()

    @property
    def fingerprint(self):
        return digest(asdict(self))

    @classmethod
    def from_payload(cls, payload):
        values = dict(payload)
        values['provenance'] = Provenance.from_payload(values['provenance'])
        for key in ('trial_ids', 'holdout_ids'):
            values[key] = tuple(values[key])
        values['holdout_windows'] = tuple(tuple(w) for w in values['holdout_windows'])
        result = cls(**values)
        if digest(asdict(result)) != digest(payload):
            raise ValueError('HYPOTHESIS_SCHEMA')
        return result


def check_trial_accounting(spec: Hypothesis, declarations: tuple[TrialDeclaration, ...],
                           outcomes: tuple[tuple[str, str], ...], *, budget: int,
                           previously_consumed_holdouts: tuple[str, ...] = ()) -> str:
    authorize('E', 'RUN_RESEARCH')
    spec.__post_init__()
    count(budget, 1, 256)
    verify_trial_chain(declarations)
    ids = tuple(d.trial_id for d in declarations)
    if set(ids) != set(spec.trial_ids) or len(ids) > budget:
        raise ValueError('TRIAL_FAMILY_ACCOUNTING')
    if any(d.family_id != spec.family_id or d.hypothesis_trial_id != spec.hypothesis_id
           or read_utc(d.declared_at_utc) > read_utc(spec.data_available_at)
           or d.source_commit != spec.provenance.evidence_head
           or (not spec.exploratory and d.declaration_mode != 'PREDECLARED') for d in declarations):
        raise ValueError('TRIAL_DECLARATION_BINDING')
    if len(outcomes) != len(ids) or {x[0] for x in outcomes} != set(ids):
        raise ValueError('ALL_TRIALS_REQUIRED')
    if any(status not in {'PASS', 'FAIL', 'ABANDONED'} for _, status in outcomes):
        raise ValueError('TRIAL_OUTCOME_INVALID')
    if not spec.exploratory and set(spec.holdout_ids) & set(previously_consumed_holdouts):
        raise ValueError('OOS_REUSE_FORBIDDEN')
    return digest({'spec': spec.fingerprint, 'trials': [d.record_hash for d in declarations],
                   'outcomes': sorted(outcomes)})


def execute_risk_trial_family(ledger, hypothesis: Hypothesis, risk_spec, *,
                              declarations: tuple[TrialDeclaration, ...], expected_head: str,
                              gross_r: tuple, cost_r: tuple, regimes: tuple, splits: tuple,
                              assessment) -> dict:
    """One bounded E transaction sequence, journalled before computation.

    No automatic retries. An interrupted trial remains declared/UNKNOWN; restart
    cannot silently hide it. G must separately reproduce and append its judgment.
    """
    from daxlab.research.turbo_risk import evaluate_risk_research
    from daxlab.research.turbo_learning import assess_investigation
    hypothesis.__post_init__()
    risk_spec.__post_init__()
    if (hypothesis.layer != 'RISK_RESEARCH' or risk_spec.hypothesis_id != hypothesis.hypothesis_id
            or tuple(k for k, _ in risk_spec.candidates) != hypothesis.trial_ids
            or risk_spec.fingerprint not in hypothesis.provenance.evidence_refs
            or risk_spec.declared_at != hypothesis.declared_at
            or risk_spec.holdout_available_at != hypothesis.data_available_at):
        raise ValueError('RISK_FAMILY_BINDING')
    check_trial_accounting(hypothesis, declarations,
        tuple((k, 'ABANDONED') for k in hypothesis.trial_ids), budget=len(hypothesis.trial_ids))
    governor = assess_investigation(assessment)
    if governor['decision'] in {'STOP', 'DEFER'}:
        return research_payload('RISK_TRIAL_FAMILY', status='NOT_RUN', governor=governor,
                                ledger_head=expected_head, result=None)
    pin = ledger.declare_hypothesis(hypothesis, expected_head=expected_head)
    for declaration in declarations:
        pin = ledger.append(role='E', kind='TRIAL', record_id=hypothesis.hypothesis_id+'.'+declaration.trial_id,
                            body=asdict(declaration), expected_head=pin)
    try:
        result = evaluate_risk_research(risk_spec, gross_r=gross_r, cost_r=cost_r,
            regimes=regimes, splits=splits, provenance=hypothesis.provenance)
    except Exception:
        ledger.append(role='E', kind='RESULT', record_id=hypothesis.hypothesis_id+'.result',
            body=research_payload('RISK_FAMILY_FAILED', status='UNKNOWN',
                trial_ids=list(hypothesis.trial_ids), reason='EVALUATION_FAILED_NO_AUTOMATIC_RETRY'),
            expected_head=pin)
        raise
    outcomes = tuple((c['label'], 'FAIL' if c['failures'] else 'PASS') for c in result['candidates'])
    accounting = check_trial_accounting(hypothesis, declarations, outcomes, budget=len(hypothesis.trial_ids))
    pin = ledger.append(role='E', kind='RESULT', record_id=hypothesis.hypothesis_id+'.result',
                        body=result | {'accounting_ref': accounting}, expected_head=pin)
    return research_payload('RISK_TRIAL_FAMILY', result=result, ledger_head=pin,
                            accounting_ref=accounting, governor=governor)


@dataclass(frozen=True, slots=True)
class FilterCard:
    filter_id: str
    classification: str
    layer: str
    purpose: str
    owner: str
    parameters: tuple[tuple[str, str], ...] = ()
    introduced_at_head: str | None = None
    evidence_at_introduction: tuple[str, ...] = ()
    data_dependencies: tuple[str, ...] = ()
    last_reviewed: str | None = None
    current_research_status: str = 'PROPOSED'

    def __post_init__(self):
        for v in (self.filter_id, self.purpose, self.owner):
            token(v)
        if self.classification not in {'TUNABLE_RESEARCH_FILTER', 'FROZEN_STRATEGY_RULE', 'PROTECTED_INVARIANT'}:
            raise ValueError('FILTER_CLASS')
        if self.layer not in {'REGIME', 'STRUCTURE', 'ENTRY', 'ADMISSION', 'RISK'}:
            raise ValueError('FILTER_LAYER')
        if self.layer in {'ADMISSION', 'RISK'} and self.classification != 'PROTECTED_INVARIANT':
            raise ValueError('PROTECTED_LAYER')
        if self.current_research_status not in {'PROPOSED', 'RESEARCH', 'OOS_WF', 'SHADOW',
                                               'PROMOTION_CANDIDATE', 'REJECTED'}:
            raise ValueError('FILTER_STATUS')
        if self.introduced_at_head:
            require_sha(self.introduced_at_head, 40)
        tokens(self.evidence_at_introduction)
        tokens(self.data_dependencies)


def filter_inventory() -> tuple[FilterCard, ...]:
    from daxlab.research.filter_registry import default_research_registry
    research = tuple(FilterCard(c.key, 'TUNABLE_RESEARCH_FILTER',
                                 'STRUCTURE' if c.key in {'fib001', 'gap001'} else 'REGIME', c.key,
                                 'research.' + c.key) for c in default_research_registry().all())
    return research + tuple(FilterCard(key, cls, layer, key, owner) for key, cls, layer, owner in (
        ('data_safe', 'PROTECTED_INVARIANT', 'ADMISSION', 'runtime.quality'),
        ('or_complete', 'FROZEN_STRATEGY_RULE', 'STRUCTURE', 'runtime.candidate_signal'),
        ('entry_confirmed', 'FROZEN_STRATEGY_RULE', 'ENTRY', 'runtime.candidate_signal'),
        ('session_trade_slot_available', 'PROTECTED_INVARIANT', 'ADMISSION', 'runtime.candidate_admission'),
        ('fixed_cash_risk', 'PROTECTED_INVARIANT', 'RISK', 'domain.risk_policy'),
        ('loss_exposure', 'PROTECTED_INVARIANT', 'RISK', 'domain.loss_admission'),
        ('independent_ptc', 'PROTECTED_INVARIANT', 'RISK', 'runtime.broker_execution_protection')))


def candidate_rule_inventory() -> tuple[FilterCard, ...]:
    """Every immutable CAND-001 config field, including identity/safety rules."""
    from daxlab.runtime.candidate_config import Cand001Config
    values = asdict(Cand001Config())
    strategy_layers = {'regime_policy': 'REGIME', 'structure_rule': 'STRUCTURE',
                       'or_minutes': 'STRUCTURE', 'entry_rule': 'ENTRY',
                       'direction_policy': 'ENTRY', 'stop_rule': 'ENTRY',
                       'target_rule': 'ENTRY', 'reward_risk': 'ENTRY'}
    return tuple(FilterCard('cand001.'+key,
        'FROZEN_STRATEGY_RULE' if key in strategy_layers else 'PROTECTED_INVARIANT',
        strategy_layers.get(key, 'ADMISSION'), key, 'runtime.candidate_config',
        ((key, str(value)),)) for key, value in values.items())


def decision_rule_inventory() -> tuple[FilterCard, ...]:
    """Closed owner catalogs, not a new decision engine or a PnL-tuning list.

    Every source enum/config/policy field is represented, including positive
    states. The purpose is inventory completeness; it does not reinterpret rules.
    """
    from dataclasses import fields
    from daxlab.runtime.candidate_signal import SignalReason
    from daxlab.runtime.candidate_admission import AdmissionStatus
    from daxlab.runtime.contracts import DataQualityState
    from daxlab.domain.risk_policy import FixedCashRiskPolicy
    from daxlab.domain.loss_admission import LossExposurePolicy
    cards = list(filter_inventory() + candidate_rule_inventory())
    for owner, catalog, classification, layer in (
        ('candidate_signal', SignalReason, 'FROZEN_STRATEGY_RULE', 'ENTRY'),
        ('candidate_admission', AdmissionStatus, 'PROTECTED_INVARIANT', 'ADMISSION'),
        ('quality', DataQualityState, 'PROTECTED_INVARIANT', 'ADMISSION')):
        cards.extend(FilterCard(owner+'.'+item.value, classification, layer,
                                item.value, 'runtime.'+owner) for item in catalog)
    for owner, contract in (('risk_policy', FixedCashRiskPolicy), ('loss_admission', LossExposurePolicy)):
        cards.extend(FilterCard(owner+'.'+f.name, 'PROTECTED_INVARIANT', 'RISK',
                                f.name, 'domain.'+owner) for f in fields(contract))
    return tuple(cards)


@dataclass(frozen=True, slots=True)
class ChampionIdentity:
    commit: str
    config: str
    strategy: str
    dataset_assumptions: str
    cost_assumptions: str
    risk_assumptions: str

    def __post_init__(self):
        require_sha(self.commit, 40)
        for key, value in asdict(self).items():
            if key != 'commit':
                require_sha(value)

    @property
    def fingerprint(self):
        return digest(asdict(self))


def audit_filters(cases: tuple, cards: tuple[FilterCard, ...], *, trial_family: str) -> dict:
    authorize('E', 'RUN_RESEARCH')
    token(trial_family)
    if not cases or not cards:
        raise ValueError('FILTER_UNIVERSE_REQUIRED')
    if len({c.case_id for c in cases}) != len(cases):
        raise ValueError('FILTER_DUPLICATE_CANDIDATE')
    if len({c.filter_id for c in cards}) != len(cards):
        raise ValueError('FILTER_DUPLICATE_RULE')
    times = [read_utc(c.knowledge_cutoff_at) for c in cases]
    if times != sorted(times):
        raise ValueError('FILTER_NONCHRONOLOGICAL_UNIVERSE')
    for case in cases:
        case.__post_init__()
        if case.net_r is None:
            raise ValueError('FILTER_OUTCOME_MISSING')
        if (case.strategy_fingerprint, case.provenance.data_contract,
            case.provenance.subject.market_contract_fingerprint) != (
                cases[0].strategy_fingerprint, cases[0].provenance.data_contract,
                cases[0].provenance.subject.market_contract_fingerprint):
            raise ValueError('FILTER_UNIVERSE_MISMATCH')
        if (case.provenance.subject.instrument_id, case.provenance.subject.provider,
            case.provenance.subject.environment, case.outcome_kind) != (
                cases[0].provenance.subject.instrument_id, cases[0].provenance.subject.provider,
                cases[0].provenance.subject.environment, cases[0].outcome_kind):
            raise ValueError('FILTER_SUBJECT_OR_OUTCOME_MISMATCH')
    values = [c.net_r for c in cases]
    masks = []
    diagnostics = []
    for card in cards:
        card.__post_init__()
        if card.classification != 'TUNABLE_RESEARCH_FILTER':
            raise ValueError('PROTECTED_OR_FROZEN_ABLATION_FORBIDDEN')
        mask = tuple(dict(c.filter_states)[card.filter_id] for c in cases)
        masks.append((card.filter_id, mask))
        effect = evaluate_filter_efficiency(values, mask, filter_id=card.filter_id).to_payload()
        effect.update(veto_frequency=1-sum(mask)/len(mask), trial_family=trial_family,
                      outcome_scope='COUNTERFACTUAL_RESEARCH_NOT_ACTUAL_PNL',
                      oos_wf='UNKNOWN_UNTIL_SEPARATE_EVALUATION',
                      parameter_stability='UNKNOWN_UNTIL_PERTURBATION')
        effect['by_regime'] = {r: evaluate_filter_efficiency(
            [c.net_r for c in cases if c.regime == r],
            [mask[i] for i, c in enumerate(cases) if c.regime == r],
            filter_id=card.filter_id).to_payload() for r in sorted({c.regime for c in cases})}
        effect['cost_stress'] = {str(f): evaluate_filter_efficiency(
            [c.net_r-(f-1)*c.costs_r for c in cases], mask,
            filter_id=card.filter_id).to_payload() for f in (1.5, 2.0)}
        kept = [r for r, keep in zip(values, mask) if keep]
        effect['top_trade_removed_r'] = sum(kept)-max(kept, default=0)
        effect['bad_trade_pass_through'] = sum(r < 0 and k for r, k in zip(values, mask))
        effect['false_rejection_proxy'] = sum(r > 0 and not k for r, k in zip(values, mask))
        diagnostics.append(effect)
    return research_payload('FILTER_AUDIT', filters=diagnostics,
        stack=evaluate_filter_stack(values, masks).to_payload(),
        overlap=(asdict(evaluate_filter_overlap([FilterMask(k, v) for k, v in masks]))
                 if len(masks) > 1 else {'pairs': [], 'status': 'SINGLE_FILTER'}),
        candidate_universe=digest([asdict(c) for c in cases]))


@dataclass(frozen=True, slots=True)
class Challenger:
    hypothesis: Hypothesis
    champion_fingerprint: str
    stage: str = 'HYPOTHESIS'
    receipts: tuple[str, ...] = ()

    def __post_init__(self):
        self.hypothesis.__post_init__()
        require_sha(self.champion_fingerprint)
        if self.stage not in STAGES or len(self.receipts) != STAGES.index(self.stage):
            raise ValueError('CHALLENGER_STAGE_SEQUENCE')
        tokens(self.receipts)
        for ref in self.receipts:
            require_sha(ref)

    def advance(self, *, stage: str, evidence_ref: str, champion_fingerprint: str):
        self.__post_init__()
        if champion_fingerprint != self.champion_fingerprint:
            raise ValueError('CHAMPION_CHANGED')
        index = STAGES.index(self.stage)
        if index+1 >= len(STAGES) or stage != STAGES[index+1]:
            raise ValueError('CHALLENGER_STAGE_SKIP')
        require_sha(evidence_ref)
        return Challenger(self.hypothesis, self.champion_fingerprint, stage,
                          self.receipts+(evidence_ref,))


def dark_compare(inputs: tuple, *, champion_state: dict, challenger_state: dict,
                 champion, challenger) -> dict:
    """Trusted offline evaluators, NOT a sandbox for arbitrary/untrusted code.

    Evaluators receive detached data only; no runtime object or broker port.
    They return decision data. Host must deny credentials/network for research.
    """
    before = digest(champion_state)
    original = digest(inputs)
    champion_input, challenger_input = deepcopy(inputs), deepcopy(inputs)
    left = champion(champion_input, deepcopy(champion_state))
    right = challenger(challenger_input, deepcopy(challenger_state))
    if digest(champion_state) != before or digest(inputs) != original:
        raise ValueError('DARK_SHARED_STATE_MUTATION')
    return research_payload('DARK_COMPARE', input_fingerprint=original,
                            champion_fingerprint=before, champion_decisions=left,
                            challenger_decisions=right)


def causal_prefix_probe(evaluator, values: tuple[float, ...], *, cutoff: int) -> dict:
    count(len(values), 2, 100000)
    count(cutoff, 1, len(values)-1)
    for value in values:
        finite(value)
    baseline = tuple(evaluator(values))
    changed = tuple(evaluator(values[:cutoff] + tuple(v*7+13 for v in values[cutoff:])))
    if len(baseline) != len(values) or len(changed) != len(values):
        raise ValueError('CAUSAL_PROBE_ALIGNMENT')
    return {'status': 'PASS' if baseline[:cutoff] == changed[:cutoff] else 'FAIL',
            'check': 'LOOKAHEAD', 'baseline_ref': digest(baseline), 'changed_ref': digest(changed)}


def recursive_probe(evaluator, histories: tuple[tuple[float, ...], ...], *, tolerance: float) -> dict:
    finite(tolerance, 0)
    if not 2 <= len(histories) <= 32 or any(not h or len(h) > 100000 for h in histories):
        raise ValueError('RECURSIVE_PROBE_HISTORY')
    results = [evaluator(h)[-1] for h in histories]
    for value in results:
        finite(value)
    delta = max(results)-min(results)
    return {'check': 'RECURSIVE', 'status': 'PASS' if delta <= tolerance else 'FAIL',
            'observed_delta': delta, 'tolerance': tolerance, 'source_ref': digest(histories)}


ATTACKS = frozenset({'LESS_HISTORY', 'MORE_HISTORY', 'WARMUP', 'SESSION_SHIFT', 'START_SHIFT',
    'REGIME_SPLIT', 'FILTER_SINGLE', 'FILTER_PAIR', 'FILTER_ORDER', 'COST_1_5', 'COST_2',
    'TOP_TRADES', 'ADVERSE_PERIOD', 'LONG_SHORT', 'PARAMETER', 'AGGREGATION', 'DELAYED_ENTRY',
    'MISSING_BAR', 'DUPLICATE_BAR', 'CORRECTED_BAR', 'CAUSAL_CUTOFF', 'TIMESTAMP', 'SESSION_BOUNDARY'})


def run_attack_matrix(attacks: tuple[tuple[str, object], ...], evaluator) -> dict:
    """Bounded predeclared scenarios with per-scenario exception isolation.

    Trusted offline evaluator returns PASS/FAIL/UNKNOWN plus an evidence hash;
    unsupported attacks stay UNKNOWN rather than disappearing or becoming PASS.
    """
    if not attacks or len(attacks) > len(ATTACKS) or len({k for k, _ in attacks}) != len(attacks):
        raise ValueError('ATTACK_MATRIX_BOUND')
    if any(name not in ATTACKS for name, _ in attacks):
        raise ValueError('ATTACK_UNKNOWN')
    rows = []
    for name, inputs in attacks:
        try:
            status, evidence_ref = evaluator(name, deepcopy(inputs))
            if status not in {'PASS', 'FAIL', 'UNKNOWN'}:
                raise ValueError('ATTACK_RESULT_INVALID')
            require_sha(evidence_ref)
            row = {'attack': name, 'status': status, 'evidence_ref': evidence_ref}
        except Exception:
            row = {'attack': name, 'status': 'UNKNOWN', 'reason': 'ATTACK_EVALUATION_FAILED'}
        rows.append(row)
    return research_payload('ADVERSARIAL_MATRIX', rows=rows,
        plan_fingerprint=digest(attacks), complete=all(r['status'] != 'UNKNOWN' for r in rows))


def walk_forward_plan(days: tuple[str, ...], *, train: int, oos: int, step: int) -> dict:
    from daxlab.contracts import WalkForwardSpec
    from daxlab.research.walk_forward import build_walk_forwards
    tokens(days, required=True)
    for n in (train, oos, step):
        count(n, 1)
    if tuple(sorted(days)) != days:
        raise ValueError('WF_DAYS_ORDER')
    if step < oos:
        raise ValueError('WF_OVERLAPPING_HOLDOUT')
    windows = build_walk_forwards(days, WalkForwardSpec(train, oos, step))
    if not windows:
        raise ValueError('WF_INSUFFICIENT_DATA')
    return research_payload('WF_PLAN', windows=[asdict(w) for w in windows],
                            days_fingerprint=digest(days), fitting_on_oos=False)


def statistical_diagnostics(*, pbo_matrix=None, pbo_splits=4, dsr_statistics=None,
                            spa_evidence=None, spa_readiness=None) -> dict:
    """Route to existing statistical owners; unavailable prerequisites stay unknown.

    No p-value voting and no automatic strategy acceptance. SPA readiness is
    owned by the current adapter, not reconstructed from a convenient boolean.
    """
    from daxlab.research.classical_pbo import classical_probability_of_backtest_overfitting
    from daxlab.research.classical_dsr import classical_deflated_sharpe_ratio_from_statistics
    from daxlab.research.arch_spa_adapter import run_experimental_arch_spa
    count(pbo_splits, 2, 12)
    results = {'PBO': {'status': 'UNKNOWN'}, 'DSR': {'status': 'UNKNOWN'}, 'SPA': {'status': 'UNKNOWN'}}
    if pbo_matrix is not None:
        if len(pbo_matrix) > 256 or sum(len(row) for row in pbo_matrix) > 100000:
            raise ValueError('STATISTICS_WORK_BUDGET')
        results['PBO'] = classical_probability_of_backtest_overfitting(pbo_matrix, n_splits=pbo_splits).to_payload()
    if dsr_statistics is not None:
        results['DSR'] = classical_deflated_sharpe_ratio_from_statistics(**dsr_statistics).to_payload()
    if spa_evidence is not None and spa_readiness is not None:
        results['SPA'] = run_experimental_arch_spa(spa_evidence, spa_readiness).to_payload()
    return research_payload('STATISTICAL_DIAGNOSTICS', results=results, automatic_winner=False)


def replay_cand001_decisions(candles: tuple, *, initial_state=None) -> dict:
    """Actual CAND-001 behavior owner reused with detached replay state only."""
    from daxlab.runtime.candidate_config import Cand001Config
    from daxlab.runtime.candidate_pipeline import Cand001PipelineState, process_cand001_candle
    from daxlab.runtime.decision import stable_fingerprint
    initial_state = initial_state or Cand001PipelineState()
    before = stable_fingerprint(initial_state)
    state = deepcopy(initial_state)
    decisions = []
    for candle in candles:
        result = process_cand001_candle(state, candle, observed_at=candle.close_time,
                                        config=Cand001Config())
        state = result.state
        decisions.append(result.decision.decision_id)
    if stable_fingerprint(initial_state) != before:
        raise ValueError('CHAMPION_REPLAY_STATE_MUTATED')
    return research_payload('CAND001_REPLAY', champion_config=stable_fingerprint(Cand001Config()),
        initial_state=before, final_replay_state=stable_fingerprint(state), decision_ids=decisions)


@dataclass(frozen=True, slots=True)
class DonorCard:
    problem: str
    external_approach: str
    principle: str
    owner: str
    benefits: tuple[str, ...]
    risks: tuple[str, ...]
    migration_cost: str
    operational_cost: str
    decision: str
    evidence_links: tuple[str, ...]

    def __post_init__(self):
        from urllib.parse import urlsplit
        for v in (self.problem, self.external_approach, self.principle, self.owner,
                  self.migration_cost, self.operational_cost):
            token(v)
        tokens(self.benefits, required=True)
        tokens(self.risks, required=True)
        if self.decision not in {'REUSE', 'ADAPT', 'REJECT', 'DEFER'}:
            raise ValueError('DONOR_DECISION')
        if not self.evidence_links or len(self.evidence_links) > 8:
            raise ValueError('DONOR_SOURCE_REQUIRED')
        for url in self.evidence_links:
            parsed = urlsplit(url)
            if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.query:
                raise ValueError('DONOR_SOURCE_UNSAFE')
