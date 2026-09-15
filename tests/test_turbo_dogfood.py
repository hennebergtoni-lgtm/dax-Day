"""Historical reconstruction plus risk A-G and partial-gate dogfood."""
from dataclasses import replace
from pathlib import Path
import sys

import pytest

from daxlab.research.turbo_learning import InvestigationAssessment, assess_investigation, assess_complexity
from daxlab.research.turbo_risk import HARD_CATEGORIES, evaluate_opportunity
from test_turbo_acceptance import (PASS, opportunity, partial, provenance, stamp,
    forbidden_side_effects as forbidden_side_effects)

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))


def test_historical_fifteen_lessons_roundtrip(tmp_path):
    from run_turbo_acceptance import historical_dogfood
    result = historical_dogfood(tmp_path/'lessons', pass_number=PASS, generated_at=stamp())
    assert result['status'] == 'PASS' and len(result['cases']) == 15
    assert result['fresh_host_proof'] is False
    assert all(c['observed_at_historical'] is None for c in result['cases'])
    assert len(list((tmp_path/'lessons').glob('*.json'))) == 15


@pytest.mark.parametrize('scenario,expected', [('A', 'TURBO_CANDIDATE'), ('B', 'NORMAL_ONLY'),
    ('C', 'TURBO_BLOCKED'), ('D', 'NORMAL_ONLY'), ('E', 'TURBO_BLOCKED'),
    ('F', 'TURBO_BLOCKED'), ('G', 'INSUFFICIENT_EVIDENCE')])
def test_risk_dogfood_A_G(scenario, expected):
    changes = {
        'A': {}, 'B': {'oos_wf_status': 'FAIL'}, 'C': {'tail_status': 'FAIL'},
        'D': {'loss_streak': 3, 'quality': (('REGIME', 0), ('STRUCTURE', 1), ('ENTRY', 0))},
        'E': {'provenance': replace(provenance(), valid_until=stamp(-1))},
        'F': {'hard_checks': tuple((k, 'UNKNOWN' if k == 'BROKER_ECONOMICS' else 'PASS') for k in HARD_CATEGORIES)},
        'G': {'contradictions': ('COST_REGIME_CONFLICT',)},
    }
    report = evaluate_opportunity(opportunity(**changes[scenario]))
    assert report['opportunity_mode'] == expected
    assert report['runtime_actuation'] is False and report['order_execution_enabled'] is False
    assert report['uncertainty_class'] and report['falsifiers']


def test_partial_host_fact_not_laundered_from_reconstruction():
    p = replace(provenance(), evidence_scope='LOCAL_TEST', valid_until=None)
    report = partial((('market_v4', 'VERIFIED', p),), required_scope='REAL_BROKER_READ')
    assert report['composite_status'] == 'WAITING_EXTERNAL'
    assert report['dimensions'][0]['status'] == 'UNKNOWN'
    assert report['dimensions'][0]['observations'][0]['status'] == 'VERIFIED'
    assert report['dimensions'][0]['observations'][0]['evidence_head'] == p.evidence_head
    root = Path(__file__).resolve().parents[1]
    current = (root/'docs/ACCELERATION_M01_DEMO_READINESS_MATRIX.md').read_text()
    assert 'WAITING_EXTERNAL' in current and 'ae0efbcaff5650f9e8a8f31bc8fd603cfae212a2' in current


def test_historical_real_subtruth_preserved_without_freshness_fabrication():
    from daxlab.research.turbo_contract import HistoricalClaim, digest
    from test_turbo_acceptance import HEAD, ANCHOR
    claim = HistoricalClaim('market_v4', HEAD, ANCHOR, 'REAL_BROKER_READ', digest('closeout'), '2026-09-15')
    report = partial((), historical_claims=(claim,), required_scope='REAL_BROKER_READ')
    assert report['dimensions'][0]['historical_truth_status'] == 'VERIFIED'
    assert report['dimensions'][0]['reusable'] is False
    assert report['composite_status'] == 'WAITING_EXTERNAL'
    assert report['next_smallest_gap'] == 'quantity_step'
    for bad in (replace(claim, evidence_scope='CI'), replace(claim, evidence_head='b'*40),
                replace(claim, observed_date='2099-01-01')):
        r = partial((), historical_claims=(bad,), required_scope='REAL_BROKER_READ')
        assert r['dimensions'][0]['historical_truth_status'] is None


def test_full_ordinal_governors_no_cost_forecast():
    base = InvestigationAssessment(False, False, False, False, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 3)
    assert assess_investigation(base)['decision'] == 'STOP'
    assert assess_investigation(replace(base, safety=True))['decision'] == 'RUN_NOW'
    assert assess_investigation(replace(base, decision_sensitive=True, economic_relevance=1))['decision'] == 'DEFER'
    report = assess_complexity(new_owners=0, new_dependencies=0, new_stores=0,
        new_runtime_authority=False, benefit_supported=True, code_growth=1,
        new_contracts=1, new_failure_modes=1, operator_burden=3,
        research_degrees_of_freedom=3, evidence_value=1)
    assert report['decision'] == 'BENEFIT_DOES_NOT_JUSTIFY_COMPLEXITY'
    assert report['compared_to'] == 'NO_CHANGE'


def test_harness_missing_or_skipped_required_case_not_green():
    from run_turbo_acceptance import acceptance_groups
    assert acceptance_groups([])['U01']['status'] == 'NOT_EXECUTED'
    cases = [{'module': 'test_turbo_acceptance', 'test': 'test_U01_repair', 'status': 'SKIPPED'}]
    assert acceptance_groups(cases)['U01']['status'] == 'INCOMPLETE'
