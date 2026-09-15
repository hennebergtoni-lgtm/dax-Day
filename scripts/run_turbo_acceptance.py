#!/usr/bin/env python3
"""Two separately invoked, source-bound Turbo U01-U40 acceptance passes.

No broker credentials or calls. Historical dogfood records are LOCAL_TEST
reconstructions, never fresh REAL_HOST observations. Artifacts are append-only.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from run_bot_helper_acceptance import read_results, summarize

ROOT = Path(__file__).resolve().parents[1]
ANCHOR = '9491a5922eac4abc6984618585778317dd249600'
HOST_HEAD = 'ae0efbcaff5650f9e8a8f31bc8fd603cfae212a2'
TESTS = tuple(f'tests/test_turbo_{name}.py' for name in ('acceptance', 'adversarial', 'integration', 'dogfood'))


def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def historical_dogfood(destination: Path, *, pass_number: int, generated_at: str) -> dict:
    from daxlab.domain.market import InstrumentId
    from daxlab.research.registry import TurboLedger
    from daxlab.research.turbo_contract import Provenance, digest
    from daxlab.research.turbo_learning import Incident, Lesson, analyze_incident
    from daxlab.runtime.bot_helper_contract import HelperSubject
    source = ROOT/'tests/fixtures/turbo_dogfood_v1.json'
    fixture = json.loads(source.read_text(encoding='utf-8'))
    if (fixture['real_host_evidence_head'] != HOST_HEAD or fixture['continuity_anchor'] != ANCHOR
            or len(fixture['cases']) != 15 or fixture['historical_observed_at'] is not None):
        raise ValueError('DOGFOOD_PROVENANCE')
    ledger = TurboLedger(destination)
    reconstruction_head = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT,
        capture_output=True, text=True, check=True).stdout.strip()
    reconstruction_build = digest(source_snapshot())
    pin, reports, history = '0'*64, [], []
    rows = fixture['cases'] if pass_number == 1 else list(reversed(fixture['cases']))
    for row in rows:
        if not (ROOT/row['source']).is_file() or not (ROOT/row['test']).is_file():
            raise ValueError('DOGFOOD_SOURCE_MISSING')
        subject = HelperSubject(digest([row['id'], pass_number]), 'REPLAY', 'REPLAY', None,
            InstrumentId('DAX'), None, generated_at[:10], reconstruction_head, digest('HISTORICAL_DOCUMENT_RECONSTRUCTION'))
        p = Provenance(reconstruction_head, ANCHOR, reconstruction_build, subject.config_fingerprint,
            digest(['DOCUMENTED_CONTRACT', row['class']]), 'LOCAL_TEST', generated_at, generated_at,
            None, subject, (file_sha(ROOT/row['source']), file_sha(source)))
        incident = Incident(row['id']+f'-p{pass_number}', row['symptom'], row['immediate'],
            row['root'], row['systemic'], row['class'], tuple(row['owners']), p, (row['trigger'],))
        analysis = analyze_incident(incident, history, local_fix_sufficient=row['decision'] == 'REPAIR')
        if analysis['decision'] != row['decision']:
            raise ValueError('DOGFOOD_INDEPENDENT_DECISION_ORACLE')
        lesson = Lesson(incident, ('BOUNDED_OWNER_CHANGE', 'BROAD_REWRITE'), ('BROAD_REWRITE',),
            analysis['decision'], 'BOUNDED_OWNER_CHANGE', (row['test'],), (), row['lesson'],
            row['next_check'], reconstruction_head, generated_at)
        pin = ledger.append_lesson(lesson, expected_head=pin)
        reports.append(dict(case_id=incident.incident_id, decision=analysis['decision'],
            cause_assessment='RETROSPECTIVE_ANALYSIS_NOT_RECOVERED_PROVIDER_PAYLOAD',
            architecture_review=analysis['architecture_review_required'], evidence_refs=list(p.evidence_refs),
            source_path=row['source'], source_test=row['test'], partial_evidence=row['partial'],
            next_smallest_check=row['next_check'], observed_at_historical=None,
            historical_host_head=HOST_HEAD, reconstruction_scope='LOCAL_TEST'))
        history.append(incident)
    restored = TurboLedger(destination).read(expected_head=pin)
    if len(restored) != 15:
        raise ValueError('DOGFOOD_RESTART')
    return {'status': 'PASS', 'cases': reports, 'ledger_head': pin,
            'fixture_sha256': file_sha(source), 'source_host_head': HOST_HEAD,
            'reconstruction_head': reconstruction_head, 'reconstruction_build': reconstruction_build,
            'continuity_anchor': ANCHOR, 'fresh_host_proof': False,
            'historical_facts_preserved': 'RAW_8_OF_8_DERIVED_10_OF_10_REQUIRED_5_OF_5',
            'current_broker_freshness': 'UNKNOWN_NOT_FABRICATED'}


def acceptance_groups(cases):
    return {f'U{i:02}': summarize([c for c in cases
        if c['module'].endswith('test_turbo_acceptance') and c['test'].startswith(f'test_U{i:02}_')])
        for i in range(1, 41)}


def source_snapshot():
    patterns = ('src/daxlab/research/turbo_*.py', 'src/daxlab/research/registry.py',
        'src/daxlab/research/promotion.py', 'src/daxlab/runtime/readiness.py',
        'src/daxlab/operator/read_model.py', 'scripts/run_turbo_acceptance.py',
        'tests/fixtures/turbo_dogfood_v1.json', 'docs/STEP_2242_IG_READ_CONTRACT_CLOSEOUT.md',
        'docs/STEP_2243_IG_DERIVATION_CLOSEOUT.md', 'docs/STEP_2244_MARKET_ECONOMICS_DERIVATION_CLOSEOUT.md',
        'docs/STEP_2238_WINDOWS_HOST_LANE_AUDIT.md', 'docs/ACCELERATION_M01_DEMO_READINESS_MATRIX.md', *TESTS)
    return {str(p.relative_to(ROOT)): file_sha(p) for pattern in patterns for p in ROOT.glob(pattern)}


def protected_snapshot():
    patterns = ('src/daxlab/runtime/candidate_*.py', 'src/daxlab/runtime/bot_helper*.py',
        'src/daxlab/domain/risk*.py', 'src/daxlab/domain/loss_admission.py',
        'src/daxlab/adapters/ig*.py', 'src/daxlab/strategies/*.py',
        'src/daxlab/research/boost001.py', 'src/daxlab/research/risk_profile_sizing.py')
    return {str(p.relative_to(ROOT)): file_sha(p) for pattern in patterns for p in ROOT.glob(pattern)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--pass-name', choices=('pass1', 'pass2'), required=True)
    args = parser.parse_args()
    destination = args.output_dir.resolve()/args.pass_name
    destination.mkdir(parents=True, exist_ok=False)
    from daxlab.runtime.atomic_json import atomic_write_json
    from daxlab.research.turbo_contract import digest
    number = int(args.pass_name[-1])
    started = datetime.now(timezone.utc).isoformat()
    atomic_write_json(destination/'attempt.json', {'status': 'STARTED_NOT_ACCEPTED',
        'pass': args.pass_name, 'started_at': started, 'execution_capability': 'NONE'}, overwrite=False)
    env = {k: v for k, v in os.environ.items() if not any(x in k.upper() for x in
        ('TOKEN', 'PASSWORD', 'SECRET', 'DATABASE_URL', 'API_KEY', 'IG_DEMO', 'IG_LIVE'))}
    env.update(PYTHONPATH=os.pathsep.join(str(ROOT/p) for p in ('src', 'scripts', 'tests')),
        PYTHONDONTWRITEBYTECODE='1', PYTEST_ADDOPTS='', TURBO_ACCEPTANCE_PASS=str(number))
    imported = subprocess.run([sys.executable, '-c',
        'import daxlab.research.turbo_contract as c; print(c.__file__)'], cwd=ROOT,
        env=env, capture_output=True, text=True, check=True)
    if not Path(imported.stdout.strip()).resolve().is_relative_to(ROOT/'src'):
        raise ValueError('TURBO_WRONG_IMPORT')
    before, protected = source_snapshot(), protected_snapshot()
    with tempfile.TemporaryDirectory(prefix='turbo-pytest-') as temp:
        junit = Path(temp)/'raw.xml'
        result = subprocess.run([sys.executable, '-m', 'pytest', *TESTS, '-q', f'--junitxml={junit}'],
            cwd=ROOT, env=env, capture_output=True, text=True, timeout=600)
        cases = read_results(junit)
    groups = acceptance_groups(cases)
    dogfood = historical_dogfood(destination/'lessons', pass_number=number, generated_at=started)
    after, protected_after = source_snapshot(), protected_snapshot()
    summary = summarize(cases)
    stable = before == after and protected == protected_after
    passed = result.returncode == 0 and stable and summary['status'] == 'PASS' and all(
        g['status'] == 'PASS' and g['executed_cases'] == 1 for g in groups.values())
    head = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True,
                          text=True, check=True).stdout.strip()
    dirty = subprocess.run(['git', 'diff', '--quiet'], cwd=ROOT).returncode != 0
    report = {'schema': 'DAX_TURBO_ACCEPTANCE_V1_1', 'pass': args.pass_name,
        'status': 'PASS' if passed else 'INCOMPLETE_OR_FAILED', 'source_head': head,
        'worktree_dirty': dirty, 'source_file_sha256': before, 'source_stable': stable,
        'source_fingerprint': digest(before), 'protected_file_sha256': protected,
        'evidence_scope': 'LOCAL_TEST', 'test_data_scope': 'SYNTHETIC',
        'real_host_head': HOST_HEAD, 'continuity_anchor': ANCHOR,
        'started_at': started, 'completed_at': datetime.now(timezone.utc).isoformat(),
        'scenario_namespace': f'turbo-p{number}', 'scenario_date': f'2026-09-{15+number}',
        'scenario_regime': 'TREND' if number == 1 else 'RANGE',
        'fault_order': 'FORWARD' if number == 1 else 'REVERSED',
        'pytest_exit_code': result.returncode, 'summary': summary, 'groups': groups,
        'dogfood': dogfood, 'execution_capability': 'NONE', 'order_execution_enabled': False,
        'runtime_actuation': False, 'broker_evidence': 'NOT_OBTAINED',
        'safety_audit_scope': 'DENIED_TEST_NETWORK_AND_NO_WRITE_API_IMPORTS_PLUS_PROTECTED_SOURCE_HASHES'}
    atomic_write_json(destination/'acceptance.json', report, overwrite=False)
    print(json.dumps({'pass': args.pass_name, 'status': report['status'], 'counts': summary['counts'],
        'groups': {k: v['status'] for k, v in groups.items()}, 'dogfood': dogfood['status']}))
    return 0 if passed else 2


if __name__ == '__main__':
    try:
        code = main()
    except Exception:
        print(json.dumps({'status': 'TURBO_ACCEPTANCE_HARNESS_FAILED', 'execution_capability': 'NONE'}))
        code = 2
    raise SystemExit(code)
