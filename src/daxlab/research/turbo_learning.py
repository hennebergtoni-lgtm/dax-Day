"""L: causal incident/autopsy analysis, not autonomous repair or policy change."""
from __future__ import annotations

from dataclasses import asdict, dataclass

from daxlab.research.no_trade_analysis import NoTradeEvidence, classify_no_trade
from daxlab.research.turbo_contract import (
    Provenance, authorize, count, finite, read_utc, token, tokens,
)

TRIGGERS = frozenset({'REPEATED', 'CROSS_OWNER', 'SPECIAL_CASE', 'CONTRACT_DRIFT',
                     'FOLLOW_ON_DEFECTS', 'HOST_LOOPS', 'ERROR_DISPLACED', 'OWNERSHIP_UNCLEAR',
                     'MASKING_BOUNDARY', 'FIXTURE_DRIFT', 'CONFLICTING_EVIDENCE',
                     'OPERATOR_UNLOCATABLE', 'SAFETY'})


@dataclass(frozen=True, slots=True)
class Incident:
    incident_id: str
    symptom: str
    immediate_cause: str
    root_cause: str
    systemic_cause: str
    failure_class: str
    affected_owners: tuple[str, ...]
    provenance: Provenance
    triggers: tuple[str, ...] = ()

    def __post_init__(self):
        for item in (self.incident_id, self.symptom, self.immediate_cause, self.root_cause,
                     self.systemic_cause, self.failure_class):
            token(item)
        tokens(self.affected_owners, required=True)
        tokens(self.triggers)
        if not set(self.triggers) <= TRIGGERS:
            raise ValueError('UNKNOWN_ARCHITECTURE_TRIGGER')
        self.provenance.__post_init__()


def analyze_incident(incident: Incident, history=(), *, contract_inadequate=False,
                     benefit_supported=True, local_fix_sufficient=False) -> dict:
    authorize('L', 'RUN_RESEARCH')
    incident.__post_init__()
    if any(type(v) is not bool for v in (contract_inadequate, benefit_supported, local_fix_sufficient)):
        raise ValueError('ARCHITECTURE_DECISION_BOOL')
    if contract_inadequate and local_fix_sufficient:
        raise ValueError('ARCHITECTURE_CONTRADICTION')
    previous = sorted({row.incident_id for row in history
                       if row.failure_class == incident.failure_class
                       and set(row.affected_owners) == set(incident.affected_owners)
                       and row.incident_id != incident.incident_id})
    triggers = set(incident.triggers)
    if previous:
        triggers.add('REPEATED')
    if len(incident.affected_owners) > 1:
        triggers.add('CROSS_OWNER')
    if not benefit_supported or incident.root_cause == 'UNKNOWN':
        decision = 'NO_CHANGE'
    elif contract_inadequate and triggers:
        decision = 'REDESIGN'
    elif local_fix_sufficient:
        decision = 'REPAIR'
    elif triggers - {'SAFETY'}:
        decision = 'REFACTOR'
    else:
        decision = 'REPAIR'
    return {'decision': decision, 'architecture_review_required': bool(triggers),
            'triggers': sorted(triggers), 'prior_incidents': previous,
            'cause': asdict(incident), 'automatic_repair': False}


@dataclass(frozen=True, slots=True)
class DecisionCase:
    case_id: str
    kind: str
    provenance: Provenance
    knowledge_cutoff_at: str
    feature_available_at: str
    regime: str
    structure: str
    entry_context: str
    filter_states: tuple[tuple[str, bool], ...]
    signal: str
    admission: str
    decision: str
    blocker: str
    costs_r: float
    risk_context: str
    source_fresh: bool
    evidence_quality: str
    strategy_fingerprint: str
    outcome_observed_at: str | None = None
    outcome_kind: str = 'UNOBSERVED'
    net_r: float | None = None
    mfe_r: float | None = None
    mae_r: float | None = None
    duration_seconds: float | None = None
    later_path_ref: str | None = None

    def __post_init__(self):
        from daxlab.runtime.bot_helper_contract import require_sha
        for value in (self.case_id, self.regime, self.structure, self.entry_context, self.signal,
                      self.admission, self.decision, self.blocker, self.risk_context,
                      self.evidence_quality):
            token(value)
        if self.kind not in {'TRADE', 'NO_TRADE', 'REJECTED_CANDIDATE'}:
            raise ValueError('AUTOPSY_KIND')
        if self.outcome_kind not in {'UNOBSERVED', 'ACTUAL', 'SIMULATED', 'OPPORTUNITY'}:
            raise ValueError('AUTOPSY_OUTCOME_SCOPE')
        if self.kind != 'TRADE' and self.outcome_kind == 'ACTUAL':
            raise ValueError('HYPOTHETICAL_FILL_IS_NOT_ACTUAL')
        if self.outcome_kind == 'ACTUAL' and self.provenance.evidence_scope != 'REAL_BROKER_EXECUTION':
            raise ValueError('ACTUAL_REQUIRES_EXECUTION_EVIDENCE')
        self.provenance.__post_init__()
        require_sha(self.strategy_fingerprint)
        if read_utc(self.feature_available_at) > read_utc(self.knowledge_cutoff_at):
            raise ValueError('LOOKAHEAD_FEATURE')
        if read_utc(self.provenance.observed_at) > read_utc(self.knowledge_cutoff_at):
            raise ValueError('LOOKAHEAD_PROVENANCE')
        finite(self.costs_r, 0)
        if type(self.source_fresh) is not bool:
            raise ValueError('FRESHNESS_BOOL')
        if type(self.filter_states) is not tuple or len(self.filter_states) > 128:
            raise ValueError('FILTER_STATES')
        tokens(tuple(row[0] for row in self.filter_states))
        for key, value in self.filter_states:
            token(key)
            if type(value) is not bool:
                raise ValueError('FILTER_STATE_BOOL')
        for value in (self.net_r, self.mfe_r, self.mae_r, self.duration_seconds):
            if value is not None:
                finite(value)
        if self.duration_seconds is not None:
            finite(self.duration_seconds, 0)
        if any(v is not None for v in (self.net_r, self.mfe_r, self.mae_r,
                                      self.duration_seconds, self.later_path_ref)) and (self.outcome_observed_at is None
                or self.outcome_kind == 'UNOBSERVED'):
            raise ValueError('OUTCOME_PROVENANCE_REQUIRED')
        if self.outcome_observed_at and read_utc(self.outcome_observed_at) <= read_utc(self.knowledge_cutoff_at):
            raise ValueError('POST_DECISION_ZONE_REQUIRED')
        if self.later_path_ref:
            require_sha(self.later_path_ref)


@dataclass(frozen=True, slots=True)
class CausalAlternative:
    case_id: str
    available_at: str
    replay_ref: str
    mechanism: str
    falsifier: str
    alternative_decision: str

    def __post_init__(self):
        from daxlab.runtime.bot_helper_contract import require_sha
        for value in (self.case_id, self.mechanism, self.falsifier, self.alternative_decision):
            token(value)
        require_sha(self.replay_ref)
        read_utc(self.available_at)


def autopsy(case: DecisionCase, alternative: CausalAlternative | None = None) -> dict:
    case.__post_init__()
    result = {'case_id': case.case_id, 'action': 'NO_CHANGE', 'hypothesis': None,
              'outcome_scope': case.outcome_kind, 'post_decision_research': True}
    if case.kind != 'TRADE':
        result['counterfactual'] = classify_no_trade(NoTradeEvidence(
            case.case_id, case.blocker, case.net_r, case.regime, case.structure)).value
        result['action'] = 'FILTER_REVIEW' if case.net_r is not None and case.net_r > 0 else 'NO_CHANGE'
    elif case.net_r is not None and case.net_r < 0 and alternative is not None:
        alternative.__post_init__()
        if alternative.case_id != case.case_id or read_utc(alternative.available_at) > read_utc(case.knowledge_cutoff_at):
            raise ValueError('CAUSAL_ALTERNATIVE_MISMATCH')
        if alternative.alternative_decision != case.decision and case.source_fresh:
            result.update(action='HYPOTHESIS', hypothesis=asdict(alternative))
    return result


@dataclass(frozen=True, slots=True)
class Lesson:
    incident: Incident
    candidate_fixes: tuple[str, ...]
    rejected_alternatives: tuple[str, ...]
    decision: str
    chosen_solution: str
    tests: tuple[str, ...]
    real_evidence: tuple[str, ...]
    generalized_lesson: str
    reusable_rule: str
    introduced_head: str
    last_seen: str
    superseded_by: str | None = None

    def __post_init__(self):
        from daxlab.runtime.bot_helper_contract import require_sha
        self.incident.__post_init__()
        if self.decision not in {'REPAIR', 'REFACTOR', 'REDESIGN', 'NO_CHANGE'}:
            raise ValueError('LESSON_DECISION')
        for v in (self.candidate_fixes, self.tests):
            tokens(v, required=True)
        tokens(self.rejected_alternatives)
        tokens(self.real_evidence)
        if self.real_evidence and not self.incident.provenance.evidence_scope.startswith('REAL_'):
            raise ValueError('LESSON_REAL_EVIDENCE_SCOPE')
        for v in (self.chosen_solution, self.generalized_lesson, self.reusable_rule):
            token(v)
        require_sha(self.introduced_head, 40)
        if read_utc(self.last_seen) < read_utc(self.incident.provenance.observed_at):
            raise ValueError('LESSON_TIME_ORDER')
        if self.superseded_by is not None:
            token(self.superseded_by)

    def to_payload(self):
        self.__post_init__()
        return {**asdict(self), 'failure_class': self.incident.failure_class,
                'affected_owners': list(self.incident.affected_owners),
                'contract_fingerprint': self.incident.provenance.data_contract,
                'freshness': self.incident.provenance.valid_until}

    @classmethod
    def from_payload(cls, payload):
        from daxlab.research.turbo_contract import digest
        values = dict(payload)
        for key in ('failure_class', 'affected_owners', 'contract_fingerprint', 'freshness'):
            values.pop(key)
        incident = dict(values['incident'])
        incident['provenance'] = Provenance.from_payload(incident['provenance'])
        for key in ('affected_owners', 'triggers'):
            incident[key] = tuple(incident[key])
        values['incident'] = Incident(**incident)
        for key in ('candidate_fixes', 'rejected_alternatives', 'tests', 'real_evidence'):
            values[key] = tuple(values[key])
        result = cls(**values)
        if digest(result.to_payload()) != digest(payload):
            raise ValueError('LESSON_PROJECTION_MISMATCH')
        return result


def learning_horizon(*, safety: bool, technical: bool, occurrences: int,
                     periods: int) -> str:
    count(occurrences)
    count(periods)
    if safety or technical:
        return 'INCIDENT'
    if occurrences >= 20 and periods >= 3:
        return 'RESEARCH_CYCLE'
    return 'PATTERN'


def value_governor(*, safety: bool, decision_sensitive: bool, external_gap: bool,
                   cheap_screen_available: bool, economic_relevance: int) -> str:
    count(economic_relevance, 0, 3)
    if any(type(v) is not bool for v in (safety, decision_sensitive, external_gap, cheap_screen_available)):
        raise ValueError('GOVERNOR_BOOL')
    if safety:
        return 'RUN_NOW'
    if external_gap:
        return 'DEFER'
    if not decision_sensitive or economic_relevance == 0:
        return 'STOP'
    return 'CHEAP_SCREEN_FIRST' if cheap_screen_available else 'RUN_NOW'


def complexity_governor(*, new_owners: int, new_dependencies: int, new_stores: int,
                        new_runtime_authority: bool, benefit_supported: bool) -> str:
    if type(new_runtime_authority) is not bool or type(benefit_supported) is not bool:
        raise ValueError('COMPLEXITY_BOOL')
    for v in (new_owners, new_dependencies, new_stores):
        count(v)
    if new_runtime_authority or new_stores or new_owners > 3 or new_dependencies:
        return 'BENEFIT_DOES_NOT_JUSTIFY_COMPLEXITY'
    return 'ACCEPTABLE' if benefit_supported else 'MORE_EVIDENCE_REQUIRED'


@dataclass(frozen=True, slots=True)
class InvestigationAssessment:
    safety: bool
    decision_sensitive: bool
    external_gap: bool
    cheap_screen_available: bool
    severity: int
    frequency: int
    blast_radius: int
    recurrence: int
    strategic_relevance: int
    learning_value: int
    economic_relevance: int
    cross_owner_scope: int
    evidence_gap: int
    implementation_cost: int
    test_cost: int

    def __post_init__(self):
        for name, value in asdict(self).items():
            if name in {'safety', 'decision_sensitive', 'external_gap', 'cheap_screen_available'}:
                if type(value) is not bool:
                    raise ValueError('ASSESSMENT_BOOL')
            else:
                count(value, 0, 3)


def assess_investigation(assessment: InvestigationAssessment) -> dict:
    assessment.__post_init__()
    decision = value_governor(safety=assessment.safety,
        decision_sensitive=assessment.decision_sensitive, external_gap=assessment.external_gap,
        cheap_screen_available=assessment.cheap_screen_available,
        economic_relevance=max(assessment.economic_relevance, assessment.learning_value,
                               assessment.strategic_relevance))
    benefit = max(assessment.severity, assessment.blast_radius, assessment.recurrence,
                  assessment.strategic_relevance, assessment.learning_value, assessment.economic_relevance)
    cost = max(assessment.implementation_cost, assessment.test_cost)
    if not assessment.safety and decision == 'RUN_NOW' and cost > benefit:
        decision = 'DEFER'
    return {'decision': decision, 'assessment': asdict(assessment),
            'comparison': 'ORDINAL_NOT_CREDIT_OR_PNL_FORECAST',
            'stop_rule': 'NO_DECISION_CHANGE_OR_EXTERNAL_GAP',
            'safety_override': assessment.safety}


def assess_complexity(*, new_owners: int, new_dependencies: int, new_stores: int,
                      new_runtime_authority: bool, benefit_supported: bool,
                      code_growth: int, new_contracts: int, new_failure_modes: int,
                      operator_burden: int, research_degrees_of_freedom: int,
                      evidence_value: int) -> dict:
    dimensions = dict(code_growth=code_growth, new_contracts=new_contracts,
        new_failure_modes=new_failure_modes, operator_burden=operator_burden,
        research_degrees_of_freedom=research_degrees_of_freedom, evidence_value=evidence_value)
    for value in dimensions.values():
        count(value, 0, 3)
    decision = complexity_governor(new_owners=new_owners, new_dependencies=new_dependencies,
        new_stores=new_stores, new_runtime_authority=new_runtime_authority,
        benefit_supported=benefit_supported)
    if decision == 'ACCEPTABLE' and max(v for k, v in dimensions.items() if k != 'evidence_value') > evidence_value:
        decision = 'BENEFIT_DOES_NOT_JUSTIFY_COMPLEXITY'
    return {'decision': decision, 'compared_to': 'NO_CHANGE', 'dimensions': dimensions,
            'new_owners': new_owners, 'new_dependencies': new_dependencies, 'new_stores': new_stores}
