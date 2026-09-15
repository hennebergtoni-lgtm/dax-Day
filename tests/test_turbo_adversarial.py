"""Independent negative/property/integration oracles, not reducer-derived expectations."""
from dataclasses import asdict
import ast
from pathlib import Path

import pytest
from hypothesis import given, strategies as st

from daxlab.research.registry import TurboLedger
from daxlab.research.turbo_contract import digest
from daxlab.research.turbo_experiment import (
    CHECKS, FilterCard, audit_filters, candidate_rule_inventory, causal_prefix_probe,
)
from daxlab.research.turbo_judge import CheckResult, judge, judge_risk_report
from daxlab.research.turbo_learning import Lesson, learning_horizon
from daxlab.research.turbo_risk import HARD_CATEGORIES, evaluate_opportunity
from daxlab.operator.read_model import project_turbo_research
from test_turbo_acceptance import (
    HEAD, PASS, case, evaluation, hypothesis, incident, opportunity, partial,
    provenance, risk_report, risk_spec, stamp,
    forbidden_side_effects as forbidden_side_effects,
)


def test_full_lesson_persistence_and_holdout_consumption(tmp_path):
    ledger = TurboLedger(tmp_path)
    lesson = Lesson(incident(), ('LOCAL_FIX',), ('REWRITE',), 'REPAIR', 'LOCAL_FIX',
        ('test_contract',), (), 'SEPARATE_CONTRACTS', 'CHECK_OWNER_FIRST', HEAD, stamp())
    h = ledger.append_lesson(lesson, expected_head='0'*64)
    h = ledger.declare_hypothesis(hypothesis(exploratory=False), expected_head=h)
    with pytest.raises(ValueError, match='HOLDOUT_ALREADY'):
        ledger.declare_hypothesis(hypothesis(hypothesis_id='different', exploratory=False), expected_head=h)
    assert len(TurboLedger(tmp_path).read(expected_head=h)) == 2
    assert learning_horizon(safety=True, technical=False, occurrences=1, periods=1) == 'INCIDENT'
    assert learning_horizon(safety=False, technical=False, occurrences=3, periods=1) == 'PATTERN'
    assert learning_horizon(safety=False, technical=False, occurrences=50, periods=4) == 'RESEARCH_CYCLE'


@pytest.mark.parametrize('secret', ['Bearer test-token', 'postgresql://u:p@db/name',
                                   '-----BEGIN PRIVATE KEY-----', 'password=example'])
def test_secret_values_not_only_keys(tmp_path, secret):
    with pytest.raises(ValueError):
        TurboLedger(tmp_path).append(role='E', kind='RESULT', record_id='x',
            body={'innocent': [secret]}, expected_head='0'*64)
    assert not list(tmp_path.glob('*.json'))


def test_truncation_and_stale_writer_lock(tmp_path):
    ledger = TurboLedger(tmp_path)
    h = ledger.append(role='E', kind='RESULT', record_id='a', body={}, expected_head='0'*64)
    (tmp_path/'00000000.json').unlink()
    with pytest.raises(ValueError, match='CHECKPOINT'):
        ledger.read(expected_head=h)
    (tmp_path/'writer.lock').touch()
    with pytest.raises(FileExistsError):
        ledger.append(role='E', kind='RESULT', record_id='b', body={}, expected_head='0'*64)


def test_partial_conflicts_and_unknown_dimensions():
    p = provenance()
    result = partial((('market_v4', 'VERIFIED', p), ('market_v4', 'BLOCKED', p)))
    assert result['dimensions'][0]['status'] == 'BLOCKED'
    assert len(result['dimensions'][0]['observations']) == 2
    with pytest.raises(ValueError):
        partial((('extra', 'VERIFIED', p),))
    result = partial((('market_v4', 'VERIFIED', p), ('quantity_step', 'VERIFIED', p)))
    assert result['composite_status'] == 'WAITING_EXTERNAL'
    assert result['composite_reassessment_required'] is True


def test_single_filter_and_chronological_universe():
    card = FilterCard('f1', 'TUNABLE_RESEARCH_FILTER', 'ENTRY', 'f1', 'E')
    result = audit_filters(tuple(case(i) for i in range(8)), (card,), trial_family='f')
    assert result['overlap']['status'] == 'SINGLE_FILTER'
    assert result['filters'][0]['bad_trade_pass_through'] == 0
    from daxlab.runtime.candidate_config import Cand001Config
    assert len(candidate_rule_inventory()) == len(asdict(Cand001Config()))


def test_judge_forged_green_independently_vetoed():
    c, b = evaluation()
    result = judge(c, b, reviewer_id='independent', expected_accounting_ref=b.accounting_ref,
                   now=stamp(), independent_checks=(CheckResult('LOOKAHEAD', 'FAIL', digest('actual'), 'PREFIX_CHANGED'),))
    assert result['verdict'] == 'REJECT' and 'INDEPENDENT_LOOKAHEAD' in result['failed_checks']
    result = judge(c, b, reviewer_id='independent', expected_accounting_ref=b.accounting_ref, now=stamp())
    assert 'INDEPENDENT_LOOKAHEAD' in result['missing_checks']


def test_judge_missing_every_required_check():
    from daxlab.research.turbo_judge import SealedEvaluation
    c, b = evaluation()
    empty = SealedEvaluation.build(c, b.accounting_ref, b.provenance, ())
    r = judge(c, empty, reviewer_id='independent', expected_accounting_ref=b.accounting_ref, now=stamp())
    assert set(CHECKS) <= set(r['missing_checks'])


def test_risk_report_reproduction_rejects_changed_results():
    spec = risk_spec()
    gross = ((2.0, -0.5, 1.5, 0.5) if PASS == 1 else (1.5, 0.5, -0.5, 2.0))*8
    cost = (0.1,)*len(gross)
    args = dict(spec=spec, report=risk_report(spec, gross, cost), gross_r=gross, cost_r=cost,
        regimes=tuple('TREND' if i % 2 else 'RANGE' for i in range(len(gross))),
        splits=tuple('OOS' if i < 16 else 'WF' for i in range(len(gross))),
        provenance=provenance(), proposer_id='E', reviewer_id='G')
    result = judge_risk_report(**args)
    assert result['judgments'][0]['verdict'] == 'MORE_EVIDENCE_REQUIRED'
    args['report']['candidates'][0]['incremental_median_net_cash'] += 1
    with pytest.raises(ValueError, match='REPRODUCTION'):
        judge_risk_report(**args)


@given(st.lists(st.floats(min_value=-100, max_value=100, allow_nan=False,
                         allow_infinity=False), min_size=4, max_size=20))
def test_prefix_oracle(values):
    # Every future perturbation must leave prefix-only cumulative sums unchanged.
    data = tuple(values)
    r = causal_prefix_probe(lambda v: [sum(v[:i+1]) for i in range(len(v))], data, cutoff=2)
    assert r['status'] == 'PASS'


@given(st.integers(0, 100), st.floats(min_value=0, max_value=1000, allow_nan=False),
       st.integers(1, 100), st.floats(min_value=0, max_value=1000, allow_nan=False))
def test_loss_drawdown_monotone(loss, dd, extra_loss, extra_dd):
    a = evaluate_opportunity(opportunity(loss_streak=loss, drawdown=dd))
    b = evaluate_opportunity(opportunity(loss_streak=loss+extra_loss, drawdown=dd+extra_dd))
    ranks = {'TURBO_BLOCKED': 0, 'INSUFFICIENT_EVIDENCE': 0, 'NORMAL_ONLY': 1,
             'BOOST_CANDIDATE': 2, 'TURBO_CANDIDATE': 3}
    assert ranks[b['opportunity_mode']] <= ranks[a['opportunity_mode']]


def test_operator_no_hidden_actuation_or_provider_payload():
    p = evaluate_opportunity(opportunity())
    view = project_turbo_research(p | {'untrusted_provider_body': 'not-projected'})
    assert 'untrusted_provider_body' not in view
    assert view['activation_button'] is False and view['execution_status'] == 'DISABLED'
    with pytest.raises(ValueError):
        project_turbo_research(p | {'runtime_actuation': True})


def test_source_boundary_no_runtime_importing_learning():
    root = Path(__file__).resolve().parents[1]
    # Existing runtime helpers/candidate/risk behavior stays byte-identical in git
    # and no Turbo source references broker write APIs or productive authority.
    for path in (root/'src/daxlab/research').glob('turbo_*.py'):
        tree = ast.parse(path.read_text())
        imports = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
        assert not any(n and n.startswith(('daxlab.adapters.ig', 'MetaTrader5')) for n in imports)
        calls = [n.func.attr for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)]
        assert not set(calls) & {'order_send', 'submit_order', 'cancel_order', 'modify_order', 'release_slot'}
    for path in (root/'src/daxlab/runtime').glob('candidate_*.py'):
        assert 'turbo_' not in path.read_text()


def test_all_unknown_hard_categories_fail_closed():
    r = evaluate_opportunity(opportunity(hard_checks=tuple((k, 'UNKNOWN') for k in HARD_CATEGORIES)))
    assert set(r['hard_blockers']) == set(HARD_CATEGORIES)


@pytest.mark.parametrize('field', ['baseline_cash_risk', 'initial_capital', 'capital_floor',
                                  'max_drawdown', 'max_floor_hit_rate', 'min_gain_per_added_drawdown'])
def test_all_risk_numbers_reject_nonfinite(field):
    with pytest.raises(ValueError):
        risk_spec(**{field: float('nan')})


def test_pattern_owner_order_and_repeated_delivery():
    from daxlab.research.turbo_learning import analyze_incident
    first = incident('first', affected_owners=('B', 'O'))
    later = incident('later', affected_owners=('O', 'B'))
    assert analyze_incident(later, (first,))['prior_incidents'] == [first.incident_id]
    assert analyze_incident(first, (first,))['prior_incidents'] == []


def test_certainty_label_cannot_be_echoed():
    with pytest.raises(ValueError, match='CERTAINTY'):
        opportunity(regime='GUARANTEED')
