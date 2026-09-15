"""Synthetic test fixtures are analytical tests, never venue/research evidence."""
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import importlib.util

import pytest
from daxlab.detail_artifact_loader import DetailArtifactPreflight
from daxlab.detail_import import plan_detail_rows
from daxlab.research.failure_analysis import empirical_distribution, historical_risk_envelope


def evidence(returns=(-1,-1,2), **change):
    rows = []
    for i,r in enumerate(returns):
        hour = 10+i
        rows.append(dict(wf=1,variant_index=1,date='2026-09-11',r=r,side='long',entry=100,exit=99,
                         reason='stop',entry_time=f'2026-09-11T{hour:02}:00:00',
                         exit_time=f'2026-09-11T{hour:02}:30:00',mae_r=-i-1,mfe_r=i,**change))
    planned = plan_detail_rows(experiment_key='SYNTHETIC_TEST_ONLY',detail_kind='TRADES',rows=rows)
    return DetailArtifactPreflight('TRADES',len(rows),hashlib.sha256(json.dumps(rows).encode()).hexdigest(),planned)


def test_quantiles_linear_interpolation_and_adverse_magnitude():
    q = empirical_distribution([0,1,2,3,4])
    assert q['median'] == 2
    assert q['p90'] == pytest.approx(3.6)
    assert q['p95'] == pytest.approx(3.8)
    assert q['p99'] == pytest.approx(3.96)
    v = historical_risk_envelope(evidence())
    assert v['mae_magnitude_r']['worst_observed'] == 3
    assert v['mae_magnitude_r']['median'] == 2
    assert v['max_observed_loss_streak'] == 2
    assert v['duration_seconds']['median'] == 1800
    assert v['drawdown_r']['worst_observed'] == 2
    assert v['cost_stress']['stress_2x'] == 'UNKNOWN_NO_PER_TRADE_COST_EVIDENCE'
    assert v['by_side']['short']['count'] == 0
    assert v['survival_verdict'] == 'UNVERIFIED_THRESHOLD'


@pytest.mark.parametrize('values', [[],[2],[2,2,2]])
def test_sample_edge_cases_are_observations_not_tail_confidence(values):
    v = empirical_distribution(values)
    assert v['count'] == len(values)
    assert v['inference_state'] == ('UNVERIFIED_THRESHOLD' if values else 'INSUFFICIENT_SAMPLE')
    assert v['p99'] == (2 if values else None)


@pytest.mark.parametrize('bad', [float('nan'),float('inf'),True,'1'])
def test_distribution_rejects_malformed_values(bad):
    with pytest.raises(ValueError):
        empirical_distribution([bad])


def test_duplicate_or_mutated_detail_cannot_create_risk_evidence():
    p = evidence()
    with pytest.raises(ValueError,match='duplicate'):
        historical_risk_envelope(replace(p,observed_rows=4,planned_rows=(*p.planned_rows,p.planned_rows[0])))
    bad = replace(p.planned_rows[0],payload=p.planned_rows[0].payload | {'mae_r':-999})
    with pytest.raises(ValueError,match='mutated'):
        historical_risk_envelope(replace(p,planned_rows=(bad,*p.planned_rows[1:])))


def test_reordered_source_rows_have_same_causal_analysis():
    p = evidence()
    assert historical_risk_envelope(p) == historical_risk_envelope(replace(p,planned_rows=tuple(reversed(p.planned_rows))))


def test_unknown_overlapping_sequences_do_not_become_cash_drawdown():
    p = evidence()
    row = p.planned_rows[0]
    payload = row.payload | {'exit_time_utc': p.planned_rows[-1].payload['exit_time_utc']}
    from daxlab.detail_import import _payload_hash
    changed = replace(row,payload=payload,payload_sha256=_payload_hash(payload))
    v = historical_risk_envelope(replace(p,planned_rows=(changed,*p.planned_rows[1:])))
    assert v['max_observed_loss_streak'] is None
    assert v['loss_sequences'][0]['state'] == 'UNKNOWN_OVERLAPPING_TRADES'
    assert v['drawdown_r']['count'] == 0


def test_production_reader_missing_source_and_wrong_hash_fail_closed(tmp_path):
    spec = importlib.util.spec_from_file_location('risk_reader',Path('scripts/analyze_historical_risk_envelope.py'))
    script = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(script)
    assert script.analyze(None)['observed_rows'] == 0
    path = tmp_path/'trades.csv'
    path.write_text('fake')
    with pytest.raises(ValueError,match='HASH_MISMATCH'):
        script.analyze(path)
