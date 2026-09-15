from datetime import timedelta
from test_operator_console_projection import console_sources, project


def test_monday_view_never_authorizes_from_green_feed_or_empty_source():
    raw, snap, hb, now, _ = console_sources()
    v = project(raw, snap, hb, now)
    gates = v['monday_pre_demo']['gates']
    assert gates['feed'] == 'VERIFIED'
    assert gates['execution_disabled'] == 'VERIFIED'
    assert gates['first_demo_authorization'] == 'USER_AUTH'
    assert gates['inventory'] == 'WAITING_EXTERNAL'
    assert gates['telemetry'] == 'UNKNOWN'
    assert v['monday_pre_demo']['state'] == 'BLOCKED'
    assert v['health_matrix']['runtime_backend_alive']['state'] == 'GREEN'
    assert v['health_matrix']['telemetry_fresh']['state'] == 'UNKNOWN'


def test_fetch_never_substitutes_for_evidence_or_invents_threshold():
    raw, snap, hb, now, _ = console_sources()
    v = project(raw, snap, hb, now + timedelta(seconds=601))
    f = v['freshness_matrix']
    assert f['operator_snapshot']['observed_at'] == snap['generated_at']
    assert f['operator_snapshot']['threshold'] == 'UNVERIFIED_THRESHOLD'
    assert f['closed_m5']['threshold_seconds'] == raw['closed_m5_feed']['max_age_seconds']
    assert f['closed_m5']['state'] == 'STALE'
    assert f['broker_clock']['observed_at'] is None
    assert f['inventory']['observed_at'] is None
    assert v['monday_pre_demo']['gates']['feed'] == 'BLOCKED'
    assert v['alerts'] and all(a['action'] == 'OBSERVE_REVIEW_NO_REPAIR' for a in v['alerts'])
