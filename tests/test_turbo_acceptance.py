"""Frozen U01–U40 assertions. Pass variants change data, time, IDs and fault order."""
from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone
import json
import os
import socket

import pytest

from daxlab.domain.market import InstrumentId
from daxlab.research.registry import TurboLedger
from daxlab.research.turbo_contract import Provenance, RIGHTS, authorize, digest
from daxlab.research.turbo_experiment import (
    CHECKS, STAGES, Challenger, DonorCard, FilterCard, Hypothesis,
    audit_filters, causal_prefix_probe, check_trial_accounting, dark_compare,
    filter_inventory, recursive_probe,
)
from daxlab.research.turbo_judge import CheckResult, SealedEvaluation, judge
from daxlab.research.turbo_learning import (
    CausalAlternative, DecisionCase, Incident, Lesson, analyze_incident, autopsy,
    complexity_governor, value_governor,
)
from daxlab.research.turbo_risk import (
    HARD_CATEGORIES, Opportunity, RiskResearchSpec, evaluate_opportunity,
    evaluate_risk_research, future_button_contract,
)
from daxlab.research.variant_trial_registry import declare_trial
from daxlab.runtime.bot_helper_contract import HelperSubject
from daxlab.runtime.readiness import project_partial_evidence

HEAD = 'ae0efbcaff5650f9e8a8f31bc8fd603cfae212a2'
ANCHOR = '9491a5922eac4abc6984618585778317dd249600'
PASS = int(os.environ.get('TURBO_ACCEPTANCE_PASS', '1'))
NOW = datetime(2026, 9, 15+PASS, 10, tzinfo=timezone.utc)


def stamp(seconds=0):
    return (NOW+timedelta(seconds=seconds)).isoformat()


@pytest.fixture(autouse=True)
def forbidden_side_effects(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('FORBIDDEN_RESEARCH_SIDE_EFFECT')
    monkeypatch.setattr(socket, 'create_connection', forbidden)
    monkeypatch.setattr(socket.socket, 'connect', forbidden)
    monkeypatch.setattr(os, 'system', forbidden)


def provenance(**changes):
    subject = HelperSubject(digest(['run', PASS]), 'REPLAY', 'REPLAY', None,
        InstrumentId('DAX'), digest('market'), NOW.date().isoformat(), HEAD, digest('config'))
    return replace(Provenance(HEAD, ANCHOR, digest('build'), digest('config'), digest('M5'),
        'SYNTHETIC', stamp(-5), stamp(-4), stamp(500), subject, (digest('raw'),)), **changes)


def incident(id='one', **changes):
    return replace(Incident(f'{id}-{PASS}', 'SYMPTOM', 'IMMEDIATE', 'ROOT', 'SYSTEMIC',
                            'CONTRACT', ('E',), provenance()), **changes)


def case(i=0, **changes):
    return replace(DecisionCase(f'case-{PASS}-{i}', 'TRADE', provenance(), stamp(), stamp(-10),
        'TREND' if PASS == 1 else 'RANGE', 'OR', 'BREAKOUT', (('f1', i % 2 == 0), ('f2', i % 2 == 0)),
        'SIGNAL', 'ALLOW', 'CANDIDATE', 'NONE', 0.1, 'FIXED_CASH', True,
        'SYNTHETIC', digest('strategy'), stamp(10+i), 'SIMULATED',
        (2.5 if i % 2 == 0 else -1.0) * (1 if PASS == 1 else 0.8)), **changes)


def hypothesis(**changes):
    window = (digest(['dataset', PASS]), stamp(-19), stamp(-10))
    return replace(Hypothesis(f'h-{PASS}', 'E-proposer', 'MECHANISM', 'FALSIFIER', 'REGIME',
        (f't-{PASS}',), 'family', (digest(window),), stamp(-20), stamp(-10), provenance(),
        holdout_windows=(window,)), **changes)


def declarations(spec):
    rows = []
    for trial in spec.trial_ids:
        rows.append(declare_trial(rows, trial_id=trial, experiment_id='experiment',
            hypothesis_trial_id=spec.hypothesis_id, family_id=spec.family_id,
            variant_key=trial, parameters={'threshold': PASS}, declared_at_utc=stamp(-20),
            declaration_mode='PREDECLARED', source_commit=spec.provenance.evidence_head))
    return tuple(rows)


def challenger():
    c = Challenger(hypothesis(), digest('champion'))
    for stage in STAGES[1:]:
        c = c.advance(stage=stage, evidence_ref=digest(stage), champion_fingerprint=c.champion_fingerprint)
    return c


def evaluation(*failed, unknown=()):
    c = challenger()
    checks = tuple(CheckResult(n, 'FAIL' if n in failed else 'UNKNOWN' if n in unknown else 'PASS',
                               digest(n), 'EXECUTED_SYNTHETIC_TEST') for n in CHECKS)
    return c, SealedEvaluation.build(c, digest('accounting'), provenance(), checks)


def verdict(*failed, unknown=()):
    c, b = evaluation(*failed, unknown=unknown)
    return judge(c, b, reviewer_id='G-reviewer', expected_accounting_ref=digest('accounting'), now=stamp())


def partial(observations, **changes):
    args = dict(gate_id=10, gate_contract_version='M01-2244', composite_status='WAITING_EXTERNAL',
                required_dimensions=('market_v4', 'quantity_step'), observations=observations,
                expected=provenance(), now=stamp(), required_scope='SYNTHETIC')
    return project_partial_evidence(**(args | changes))


def opportunity(**changes):
    return replace(Opportunity(stamp(), stamp(-10), provenance(), 'TREND' if PASS == 1 else 'RANGE',
        (('REGIME', 2), ('STRUCTURE', 2), ('ENTRY', 2)), 100, 40, 'PASS', 'PASS', 'PASS',
        tuple((k, 'PASS') for k in HARD_CATEGORIES), 0, 0.0), **changes)


def risk_spec(**changes):
    return replace(RiskResearchSpec(f'risk-{PASS}', stamp(-20), stamp(-10), 2.,
        (('candidate', 3.),), 1000., 600., 20., 100., 0., 8, 30, 2, PASS), **changes)


def risk_report(spec=None, gross=None, cost=None):
    gross = gross or ((2.0, -0.5, 1.5, 0.5) if PASS == 1 else (1.5, 0.5, -0.5, 2.0))*8
    cost = cost or (0.1,)*len(gross)
    return evaluate_risk_research(spec or risk_spec(), gross_r=gross, cost_r=cost,
        regimes=tuple('TREND' if i % 2 else 'RANGE' for i in range(len(gross))),
        splits=tuple('OOS' if i < len(gross)//2 else 'WF' for i in range(len(gross))),
        provenance=provenance())


def test_U01_repair():
    assert analyze_incident(incident())['decision'] == 'REPAIR'


def test_U02_cross_owner_refactor():
    r = analyze_incident(incident(affected_owners=('B', 'O')))
    assert r['architecture_review_required'] and r['decision'] == 'REFACTOR'


def test_U03_unjustified_redesign():
    assert analyze_incident(incident(triggers=('CONTRACT_DRIFT',)), contract_inadequate=True,
                            benefit_supported=False)['decision'] == 'NO_CHANGE'


def test_U04_pattern():
    r = analyze_incident(incident('two'), (incident(),))
    assert r['prior_incidents'] == [f'one-{PASS}'] and 'REPEATED' in r['triggers']


def test_U05_donor():
    d = DonorCard('LOOKAHEAD', 'FREQTRADE', 'PREFIX_INVARIANCE', 'E', ('CAUSALITY',),
        ('FALSE_NEGATIVE',), 'LOW', 'LOW', 'ADAPT', ('https://www.freqtrade.io/en/stable/lookahead-analysis/',))
    assert d.decision == 'ADAPT'
    with pytest.raises(ValueError):
        replace(d, evidence_links=())


def test_U06_variance():
    assert autopsy(case(net_r=-1))['hypothesis'] is None


def test_U07_causal_alternative():
    c = case(net_r=-1)
    a = CausalAlternative(c.case_id, stamp(-1), digest('causal-replay'), 'COST_VETO', 'OOS_FAIL', 'NO_TRADE')
    assert autopsy(c, a)['action'] == 'HYPOTHESIS'
    with pytest.raises(ValueError):
        autopsy(c, replace(a, available_at=stamp(1)))


def test_U08_good_rejection():
    r = autopsy(case(kind='REJECTED_CANDIDATE', outcome_kind='OPPORTUNITY', net_r=2))
    assert r['action'] == 'FILTER_REVIEW' and r['hypothesis'] is None


def test_U09_bad_rejection():
    assert autopsy(case(kind='NO_TRADE', outcome_kind='OPPORTUNITY', net_r=-1))['counterfactual'] == 'PROTECTED_LOSS'


def test_U10_overlap():
    cards = tuple(FilterCard(k, 'TUNABLE_RESEARCH_FILTER', 'ENTRY', k, 'E') for k in ('f1', 'f2'))
    r = audit_filters(tuple(case(i) for i in range(12)), cards, trial_family='family')
    assert r['overlap']['pairs'][0]['jaccard_blocked'] == 1
    assert r['stack']['stages'][1]['redundant_in_stack'] is True
    assert len(filter_inventory()) >= 11
    with pytest.raises(ValueError):
        audit_filters((case(),), (FilterCard('f1', 'PROTECTED_INVARIANT', 'RISK', 'RISK', 'S'),), trial_family='f')


def test_U11_oos_veto():
    assert verdict('OOS', 'COST_2')['verdict'] == 'REJECT'


def test_U12_top_trade():
    assert verdict(unknown=('TOP_TRADES',))['verdict'] == 'MORE_EVIDENCE_REQUIRED'


def test_U13_lookahead():
    assert causal_prefix_probe(lambda v: [sum(v)]*len(v), (1., 2., 3., float(PASS)), cutoff=2)['status'] == 'FAIL'
    assert causal_prefix_probe(lambda v: [sum(v[:i+1]) for i in range(len(v))], (1., 2., 3., 4.), cutoff=2)['status'] == 'PASS'


def test_U14_recursive():
    assert recursive_probe(lambda v: [sum(v)], ((1., 2., 3.), (2., 3.)), tolerance=0)['status'] == 'FAIL'


def test_U15_champion():
    c = Challenger(hypothesis(), digest('champion'))
    with pytest.raises(ValueError):
        c.advance(stage='TESTABLE_SPEC', evidence_ref=digest('test'), champion_fingerprint=digest('changed'))
    assert c.champion_fingerprint == digest('champion')


def test_U16_rights():
    forbidden = {'PROMOTE', 'DEPLOY', 'MUTATE_RUNTIME', 'CHANGE_RISK', 'CHANGE_FILTERS', 'EXECUTE_ORDER'}
    assert forbidden <= RIGHTS
    for role in ('L', 'E', 'G'):
        for right in forbidden:
            with pytest.raises(PermissionError):
                authorize(role, right)


def test_U17_independent():
    c, b = evaluation()
    with pytest.raises(PermissionError):
        judge(c, b, reviewer_id=c.hypothesis.proposer_id,
              expected_accounting_ref=b.accounting_ref, now=stamp())


def test_U18_lesson_reuse(tmp_path):
    ledger = TurboLedger(tmp_path)
    a = Lesson(incident('a'), ('FIX',), (), 'REPAIR', 'FIX', ('test',), (),
               'CONTRACT_BOUNDARY', 'REUSE', HEAD, stamp())
    b = replace(a, incident=incident('b', provenance=replace(provenance(), observed_at=stamp(-6))))
    head = ledger.append_lesson(a, expected_head='0'*64)
    ledger.append_lesson(b, expected_head=head)
    assert len(ledger.prior_lessons(failure_class='CONTRACT', affected_owners=('E',), contract_fingerprint=digest('M5'))) == 2


def test_U19_heads():
    p = provenance()
    assert p.evidence_head == HEAD and p.continuity_anchor == ANCHOR and HEAD != ANCHOR


def test_U20_partial():
    r = partial((('market_v4', 'VERIFIED', provenance()),))
    assert r['composite_status'] == 'WAITING_EXTERNAL'
    assert r['dimensions'][0]['status'] == 'VERIFIED'


def test_U21_reuse():
    r = partial((('market_v4', 'VERIFIED', provenance()),))
    assert r['remaining_gaps'] == ['quantity_step'] and r['next_smallest_gap'] == 'quantity_step'


def test_U22_value():
    args = dict(safety=False, decision_sensitive=False, external_gap=False,
                cheap_screen_available=False, economic_relevance=0)
    assert value_governor(**args) == 'STOP'
    assert value_governor(**(args | {'safety': True})) == 'RUN_NOW'


def test_U23_complexity():
    assert complexity_governor(new_owners=6, new_dependencies=1, new_stores=1,
        new_runtime_authority=False, benefit_supported=True) == 'BENEFIT_DOES_NOT_JUSTIFY_COMPLEXITY'


def test_U24_multi_fault():
    faults = ['OOS', 'SAFETY', 'COST_2']
    if PASS == 2:
        faults.reverse()
    assert verdict(*faults)['failed_checks'] == sorted(faults)


def test_U25_all_trials():
    s = hypothesis(trial_ids=('a', 'b'))
    d = declarations(s)
    assert check_trial_accounting(s, d, (('a', 'FAIL'), ('b', 'ABANDONED')), budget=2)
    with pytest.raises(ValueError):
        check_trial_accounting(s, d, (('a', 'PASS'),), budget=2)
    with pytest.raises(ValueError):
        check_trial_accounting(s, d, (('a', 'PASS'), ('b', 'FAIL')), budget=1)


def test_U26_restart_tamper(tmp_path):
    ledger = TurboLedger(tmp_path)
    head = ledger.declare_hypothesis(hypothesis(hypothesis_id='a'), expected_head='0'*64)
    assert TurboLedger(tmp_path).read(expected_head=head)[0]['hash'] == head
    with pytest.raises(ValueError):
        ledger.append(role='E', kind='HYPOTHESIS', record_id='a', body={}, expected_head=head)
    path = tmp_path/'00000000.json'
    payload = json.loads(path.read_text())
    payload['body']['id'] = 'tampered'
    path.write_text(json.dumps(payload))
    with pytest.raises(ValueError):
        ledger.read(expected_head=head)


def test_U27_determinism():
    assert risk_report() == risk_report()


def test_U28_no_effects():
    result = evaluate_opportunity(opportunity())
    assert result['execution_capability'] == 'NONE'
    assert result['order_execution_enabled'] is False
    assert result['runtime_actuation'] is False


def test_U29_dark():
    original = {'value': 1}
    def ch(values, state):
        state['value'] = 9
        return [sum(values)]
    r = dark_compare((1, PASS), champion_state=original, challenger_state={},
                     champion=ch, challenger=ch)
    assert original == {'value': 1} and r['champion_fingerprint'] == digest(original)


def test_U30_bad_provenance():
    p = provenance()
    variants = [replace(p, evidence_scope='CI'), replace(p, valid_until=stamp(-1)),
                replace(p, data_contract=digest('wrong')), replace(p, superseded_by=digest('new')),
                replace(p, subject=replace(p.subject, run_id=digest('wrong'))),
                replace(p, evidence_head='b'*40, subject=replace(p.subject, code_head='b'*40))]
    if PASS == 2:
        variants.reverse()
    for bad in variants:
        assert not partial((('market_v4', 'VERIFIED', bad),))['dimensions'][0]['reusable']


def test_U31_turbo_research():
    before = digest(asdict(opportunity()))
    assert evaluate_opportunity(opportunity())['opportunity_mode'] == 'TURBO_CANDIDATE'
    assert digest(asdict(opportunity())) == before


def test_U32_sample():
    assert evaluate_opportunity(opportunity(historical_sample=3))['opportunity_mode'] == 'INSUFFICIENT_EVIDENCE'


def test_U33_oos():
    assert evaluate_opportunity(opportunity(oos_wf_status='FAIL'))['opportunity_mode'] == 'NORMAL_ONLY'
    r = risk_report(gross=(-1.,)*32)
    assert 'OOS' in r['candidates'][0]['failures'] and r['candidates'][0]['verdict'] == 'REJECT'


def test_U34_cost():
    r = risk_report(gross=(1.2,)*32, cost=(1.,)*32)
    assert {'COST_1.5', 'COST_2.0'} <= set(r['candidates'][0]['failures'])


def test_U35_survival():
    r = risk_report(risk_spec(max_drawdown=0.001))
    assert 'TAIL_SURVIVAL' in r['candidates'][0]['failures']


def test_U36_hard_veto():
    for category in HARD_CATEGORIES:
        for status in ('FAIL', 'UNKNOWN'):
            checks = tuple((k, status if k == category else 'PASS') for k in HARD_CATEGORIES)
            assert evaluate_opportunity(opportunity(hard_checks=checks))['opportunity_mode'] == 'TURBO_BLOCKED'
    assert evaluate_opportunity(opportunity(hard_checks=()))['opportunity_mode'] == 'TURBO_BLOCKED'


def test_U37_no_revenge():
    for loss in (1, 3, 50):
        for dd in (0, 1, 100):
            assert evaluate_opportunity(opportunity(loss_streak=loss, drawdown=dd))['opportunity_mode'] == 'NORMAL_ONLY'


def test_U38_five_x():
    r = risk_report(risk_spec(candidates=(('five_x', 10.),), max_drawdown=0.01))
    assert r['candidates'][0]['verdict'] == 'REJECT'
    with pytest.raises(ValueError):
        risk_spec(candidates=(('five_x', 100.),))


def test_U39_no_arming():
    r = future_button_contract('TURBO_ARMED')
    assert r['effective_state'] == 'TURBO_OFF' and r['actuation_available'] is False
    assert r['runtime_actuation'] is False


def test_U40_uncertainty():
    r = evaluate_opportunity(opportunity(contradictions=('COST_DRIFT',)))
    assert r['opportunity_mode'] == 'INSUFFICIENT_EVIDENCE' and r['falsifiers']
    assert r['uncertainty_class'] == 'CONDITIONAL_RESEARCH_ONLY'
    text = json.dumps(r).upper()
    assert not any(word in text for word in ('GUARANTEED', "CAN'T LOSE", 'SURE WIN', 'CAN ONLY GO WELL'))


@pytest.mark.parametrize('bad', [float('nan'), float('inf'), True, '1', -1])
def test_numeric_boundaries(bad):
    with pytest.raises(ValueError):
        risk_spec(baseline_cash_risk=bad)


def test_oos_reuse_and_seal_tamper():
    h = hypothesis(exploratory=False)
    with pytest.raises(ValueError):
        check_trial_accounting(h, declarations(h), ((h.trial_ids[0], 'PASS'),), budget=1,
                               previously_consumed_holdouts=h.holdout_ids)
    _, bundle = evaluation()
    with pytest.raises(ValueError):
        replace(bundle, accounting_ref=digest('tamper'))
