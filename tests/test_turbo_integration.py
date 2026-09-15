"""Cross-owner evidence flow and independent raw-input oracles."""
from dataclasses import asdict, replace
from datetime import timedelta

import pytest

from daxlab.research.registry import TurboLedger
from daxlab.research.turbo_contract import Provenance, digest
from daxlab.research.turbo_experiment import (
    ChampionIdentity, Challenger, STAGES, CHECKS, audit_filters, FilterCard,
    decision_rule_inventory, execute_risk_trial_family, replay_cand001_decisions,
    run_attack_matrix, statistical_diagnostics, walk_forward_plan,
)
from daxlab.research.turbo_judge import (
    CheckResult, SealedEvaluation, judge, reproduce_core_checks, review_opportunity,
)
from daxlab.research.turbo_risk import evaluate_opportunity
from daxlab.operator.read_model import project_turbo_research
from daxlab.runtime.candidate_pipeline import Cand001PipelineState
from daxlab.runtime.candidate_config import Cand001Config
from daxlab.runtime.decision import stable_fingerprint
from test_candidate_pipeline import bar
from test_turbo_acceptance import (
    HEAD, PASS, case, declarations, hypothesis, opportunity, partial, provenance, risk_spec, stamp,
    forbidden_side_effects as forbidden_side_effects,
)


def test_exact_provenance_roundtrip_future_generated_not_reusable():
    p = provenance()
    assert Provenance.from_payload(asdict(p)) == p
    future = replace(p, generated_at=stamp(1))
    assert partial((('market_v4', 'VERIFIED', future),))['dimensions'][0]['reusable'] is False
    with pytest.raises((ValueError, TypeError)):
        Provenance.from_payload(asdict(p) | {'new_green_flag': True})


def test_all_outcome_dimensions_require_post_decision_zone():
    for field in ('mfe_r', 'mae_r', 'duration_seconds'):
        with pytest.raises(ValueError, match='OUTCOME_PROVENANCE'):
            case(net_r=None, outcome_kind='UNOBSERVED', outcome_observed_at=None, **{field: 1.})


def test_filter_universe_does_not_mix_order_subject_or_outcome_scope():
    card = FilterCard('f1', 'TUNABLE_RESEARCH_FILTER', 'ENTRY', 'f1', 'E')
    with pytest.raises(ValueError, match='NONCHRONOLOGICAL'):
        audit_filters((case(0, knowledge_cutoff_at=stamp(1)), case(1)), (card,), trial_family='f')
    with pytest.raises(ValueError, match='OUTCOME_MISMATCH'):
        audit_filters((case(0), case(1, outcome_kind='OPPORTUNITY')), (card,), trial_family='f')
    inventory = decision_rule_inventory()
    assert len(inventory) == len({c.filter_id for c in inventory})
    for c in inventory:
        if c.layer in {'ADMISSION', 'RISK'}:
            assert c.classification == 'PROTECTED_INVARIANT'
    assert all(c.parameters for c in inventory if c.filter_id.startswith('cand001.'))


def test_real_candidate_owner_isolated_and_replayed():
    shift = timedelta(days=PASS)
    candles = tuple(replace(c, event_time=c.event_time+shift, close_time=c.close_time+shift,
                            received_at=c.received_at+shift) for c in (
        bar(9, 0, open_price=100, high_price=102, low_price=99, close_price=101),
        bar(9, 5, open_price=101, high_price=103, low_price=98, close_price=102),
        bar(9, 10, open_price=102, high_price=103, low_price=99, close_price=101),
        bar(9, 15, open_price=102, high_price=105, low_price=101, close_price=104)))
    state = Cand001PipelineState()
    before = stable_fingerprint(state)
    first = replay_cand001_decisions(candles, initial_state=state)
    second = replay_cand001_decisions(candles, initial_state=state)
    assert first == second and len(first['decision_ids']) == 4
    assert state == Cand001PipelineState() and stable_fingerprint(state) == before
    assert first['champion_config'] == stable_fingerprint(Cand001Config())
    assert first['order_execution_enabled'] is False


def test_attack_matrix_does_not_mask_later_faults():
    attacks = [('MISSING_BAR', (1,)), ('DUPLICATE_BAR', (2,)), ('COST_2', (3,))]
    if PASS == 2:
        attacks.reverse()
    def evaluate(name, values):
        if name == 'MISSING_BAR':
            raise OverflowError('not persisted')
        return ('FAIL' if name == 'DUPLICATE_BAR' else 'PASS', digest(values))
    result = run_attack_matrix(tuple(attacks), evaluate)
    assert {r['attack']: r['status'] for r in result['rows']} == {
        'MISSING_BAR': 'UNKNOWN', 'DUPLICATE_BAR': 'FAIL', 'COST_2': 'PASS'}
    assert result['complete'] is False


def test_existing_statistics_and_walk_forward_owners():
    days = tuple(f'2026-08-{i:02}' for i in range(1, 31))
    plan = walk_forward_plan(days, train=10, oos=5, step=5)
    assert len(plan['windows']) == 4
    assert set(plan['windows'][0]['train']).isdisjoint(plan['windows'][0]['oos'])
    with pytest.raises(ValueError, match='OVERLAPPING'):
        walk_forward_plan(days, train=10, oos=5, step=2)
    matrix = tuple(tuple(row) for row in zip(*[(1.+i*.03, (-1.)**i*.2, .5+i*.02) for i in range(12)]))
    report = statistical_diagnostics(pbo_matrix=matrix)
    assert report['results']['PBO']['schema_version'] == 'DAXLAB_CLASSICAL_PBO_V1'
    assert report['results']['DSR']['status'] == report['results']['SPA']['status'] == 'UNKNOWN'


def test_rehashed_renamed_overlapping_holdout_is_still_consumed(tmp_path):
    ledger = TurboLedger(tmp_path)
    first = hypothesis(exploratory=False)
    pin = ledger.declare_hypothesis(first, expected_head='0'*64)
    window = (digest('different-dataset-alias'), stamp(-18), stamp(-10))
    second = replace(first, hypothesis_id='renamed', holdout_windows=(window,), holdout_ids=(digest(window),))
    with pytest.raises(ValueError, match='PERIOD_ALREADY_CONSUMED'):
        ledger.declare_hypothesis(second, expected_head=pin)


def test_malformed_typed_ledger_body_rejected_before_write(tmp_path):
    ledger = TurboLedger(tmp_path)
    for role, kind in (('L', 'LESSON'), ('E', 'HYPOTHESIS')):
        with pytest.raises(ValueError, match='BODY_SCHEMA'):
            ledger.append(role=role, kind=kind, record_id='incomplete', body={}, expected_head='0'*64)
    assert not list(tmp_path.glob('*.json'))


def test_risk_family_journals_every_candidate_before_results(tmp_path):
    from daxlab.research.turbo_learning import InvestigationAssessment
    spec = risk_spec(candidates=(('bounded', 3.), ('five_x', 10.)), max_drawdown=8.)
    h = hypothesis(hypothesis_id=spec.hypothesis_id, layer='RISK_RESEARCH',
        trial_ids=('bounded', 'five_x'), provenance=replace(provenance(), evidence_refs=(spec.fingerprint,)))
    ledger = TurboLedger(tmp_path)
    assessment = InvestigationAssessment(False, True, False, True, 1, 1, 1, 1, 2, 2, 3, 1, 1, 1, 1)
    inputs = dict(gross_r=(2., -.5, 1.5, .5)*8, cost_r=(.1,)*32,
                  regimes=('TREND',)*32, splits=('OOS',)*16+('WF',)*16)
    stopped = execute_risk_trial_family(ledger, h, spec, declarations=declarations(h), expected_head='0'*64,
        assessment=replace(assessment, decision_sensitive=False), **inputs)
    assert stopped['status'] == 'NOT_RUN' and ledger.read() == ()
    report = execute_risk_trial_family(ledger, h, spec, declarations=declarations(h), expected_head='0'*64,
        assessment=assessment, **inputs)
    rows = ledger.read(expected_head=report['ledger_head'])
    assert [r['kind'] for r in rows] == ['HYPOTHESIS', 'TRIAL', 'TRIAL', 'RESULT']
    assert len(report['result']['candidates']) == 2
    assert report['result']['candidates'][1]['verdict'] == 'REJECT'
    with pytest.raises(ValueError, match='DUPLICATE'):
        execute_risk_trial_family(ledger, h, spec, declarations=declarations(h), expected_head=report['ledger_head'],
            assessment=assessment, **inputs)


def test_g_raw_input_reproduction_and_operator_binding():
    h = hypothesis(minimum_sample=8)
    champion = ChampionIdentity(HEAD, digest('config'), digest('strategy'), digest('data'), digest('cost'), digest('risk'))
    core = reproduce_core_checks(h, oos_gross_r=(2., -.5)*8, oos_cost_r=(.1,)*16,
        causal_values=(1., 2., 3., float(PASS)), cutoff=2,
        evaluator=lambda v: [sum(v[:i+1]) for i in range(len(v))],
        champion_before=champion, champion_after=champion)
    assert all(c.status == 'PASS' for c in core)
    c = Challenger(h, champion.fingerprint)
    for stage in STAGES[1:]:
        c = c.advance(stage=stage, evidence_ref=digest(stage), champion_fingerprint=champion.fingerprint)
    checks = core + tuple(CheckResult(n, 'PASS', digest(n), 'SYNTHETIC_TEST') for n in CHECKS if n not in {x.name for x in core})
    bundle = SealedEvaluation.build(c, digest('all-trials'), h.provenance, checks)
    verdict = judge(c, bundle, reviewer_id='G-independent', expected_accounting_ref=bundle.accounting_ref,
                    now=stamp(), independent_checks=core)
    assert verdict['verdict'] == 'MORE_EVIDENCE_REQUIRED'  # synthetic is not confirmatory
    o = opportunity()
    report = evaluate_opportunity(o)
    with pytest.raises(ValueError, match='BINDING'):
        project_turbo_research(report, judgment=verdict)
    review = review_opportunity(o, report=report, proposer_id='E', reviewer_id='G')
    assert project_turbo_research(report, judgment=review)['g_status'] == 'MORE_EVIDENCE_REQUIRED'
    with pytest.raises(ValueError, match='BINDING'):
        project_turbo_research(evaluate_opportunity(replace(o, loss_streak=1)), judgment=review)


def test_promotion_entrance_binds_actual_journal_and_exact_experiment(tmp_path):
    from daxlab.research.promotion import build_turbo_review_artifact, PromotionState
    from daxlab.research.turbo_experiment import check_trial_accounting
    from daxlab.research.turbo_judge import publish_judgment
    from test_nextgen_research_promotion import build_experiment
    # Synthetic conformance fixture exercising the REPLAY-contract path. This
    # test does NOT make its generated returns real-market or profitability proof.
    experiment = build_experiment()
    p = provenance(evidence_head=experiment.source_commit, evidence_scope='REPLAY',
        config_fingerprint=experiment.config_fingerprint,
        subject=replace(provenance().subject, code_head=experiment.source_commit,
                        config_fingerprint=experiment.config_fingerprint),
        evidence_refs=(experiment.experiment_fingerprint,))
    h = hypothesis(provenance=p, exploratory=False, minimum_sample=8)
    identity = ChampionIdentity(HEAD, digest('config'), digest('strategy'), digest('data'), digest('cost'), digest('risk'))
    core = reproduce_core_checks(h, oos_gross_r=(2., -.5)*8, oos_cost_r=(.1,)*16,
        causal_values=(1., 2., 3., 4.), cutoff=2,
        evaluator=lambda v: [sum(v[:i+1]) for i in range(len(v))],
        champion_before=identity, champion_after=identity)
    c = Challenger(h, identity.fingerprint)
    for stage in STAGES[1:]:
        c = c.advance(stage=stage, evidence_ref=digest(stage), champion_fingerprint=identity.fingerprint)
    ds = declarations(h)
    outcomes = tuple((t, 'PASS') for t in h.trial_ids)
    accounting = check_trial_accounting(h, ds, outcomes, budget=len(ds))
    checks = core + tuple(CheckResult(n, 'PASS', digest(n), 'SYNTHETIC_CONFORMANCE') for n in CHECKS if n not in {x.name for x in core})
    b = SealedEvaluation.build(c, accounting, p, checks)
    ledger = TurboLedger(tmp_path)
    with pytest.raises(ValueError, match='JOURNAL_BINDING'):
        publish_judgment(ledger, c, b, reviewer_id='G', expected_head='0'*64, now=stamp(), independent_checks=core)
    pin = ledger.declare_hypothesis(h, expected_head='0'*64)
    for d in ds:
        pin = ledger.append(role='E', kind='TRIAL', record_id='trial.'+d.trial_id, body=asdict(d), expected_head=pin)
    pin = ledger.publish_evaluation(c, b, outcomes=outcomes, expected_head=pin)
    with pytest.raises(ValueError, match='EVALUATION_BINDING'):
        build_turbo_review_artifact(experiment=build_experiment(fill='OTHER'), challenger=c, bundle=b,
            reviewer_id='G', accounting_ref=accounting, now=stamp(), independent_checks=core,
            ledger=ledger, ledger_head=pin)
    artifact, pin = build_turbo_review_artifact(experiment=experiment, challenger=c, bundle=b,
        reviewer_id='G', accounting_ref=accounting, now=stamp(), independent_checks=core,
        ledger=ledger, ledger_head=pin)
    assert artifact.promotion_state is PromotionState.REVIEW_READY
    assert artifact.execution_capability == 'NONE' and artifact.order_execution_authorized is False
    assert ledger.read(expected_head=pin)[-1]['kind'] == 'JUDGMENT'
