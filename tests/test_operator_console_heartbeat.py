"""An alive process must not hide blockers or invent broker truth."""
from hashlib import sha256
from test_operator_console_projection import console_sources, project


def test_green_heartbeat_preserves_blocker_and_keeps_independent_liveness():
    raw, snap, hb, now, _ = console_sources()
    hb.update(status='GREEN', blockers=['CLOCK_NOT_SAFE'])
    view = project(raw, snap, hb, now)
    assert 'CLOCK_NOT_SAFE' in view['blockers']
    assert view['system']['FEED']['state'] == 'BLOCKED'
    h = view['health_dimensions']
    assert h['liveness']['state'] == 'GREEN'
    assert h['readiness']['state'] == 'BLOCKED'
    assert h['readiness']['blockers'] == view['blockers']
    assert h['broker_truth']['state'] == 'UNKNOWN'


def test_unknown_heartbeat_blockers_preserve_each_identity_without_free_text():
    raw, snap, hb, now, _ = console_sources()
    hb.update(status='GREEN', blockers=['opaque_A', 'opaque_B'])
    view = project(raw, snap, hb, now)
    for value in hb['blockers']:
        assert 'UNKNOWN_SOURCE_BLOCKER:' + sha256(value.encode()).hexdigest() in view['blockers']
    assert view['health_dimensions']['readiness']['blockers'] == view['blockers']
    assert view['system']['FEED']['state'] == 'BLOCKED'
