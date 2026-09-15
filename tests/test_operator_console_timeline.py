from datetime import timedelta
import pytest
from daxlab.runtime.candidate_operator_query import build_operator_console_projection
from test_operator_console_projection import console_sources


def timeline(history=()):
    raw, snap, hb, now, _ = console_sources()
    return build_operator_console_projection(snapshot_payload=snap, bundle_payload=raw, heartbeat_payload=hb,
                                             queried_at=now, heartbeat_history=history)


def test_current_timeline_preserves_snapshot_time_not_bar_or_fetch_time():
    v = timeline()
    events = v['incident_timeline']['events']
    assert {e['stage'] for e in events} == {'MARKET_OBSERVATION','SIGNAL','ADMISSION','DECISION'}
    for e in events:
        if e['stage'] != 'MARKET_OBSERVATION':
            assert e['observed_at'] == v['candidate']['generated_at']
        assert e['independent_transition_time'] == 'UNKNOWN'
    assert v['incident_timeline']['history_completeness'] == 'UNKNOWN'


def test_duplicate_and_out_of_order_heartbeat_display_is_deterministic():
    _, _, hb, now, _ = console_sources()
    older = hb | {'observed_at_utc': (now-timedelta(seconds=1)).isoformat()}
    a = timeline((hb,older,hb))['incident_timeline']
    b = timeline((older,hb))['incident_timeline']
    assert a == b
    assert sum(e['stage']=='SUPERVISOR_OBSERVATION' for e in a['events']) == 2


@pytest.mark.parametrize('mutation', [{'execution_capability':'DEMO'}, {'order_execution_enabled':True}, {'nested':[{'Api_Token':'sentinel'}]}, {'observed_at_utc':'2099-01-01T00:00:00+00:00'}])
def test_malformed_or_secret_history_cannot_renew_or_leak(mutation):
    _, _, hb, _, _ = console_sources()
    with pytest.raises(ValueError):
        timeline((hb | mutation,))
