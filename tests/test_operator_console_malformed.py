import json
from daxlab.runtime.atomic_json import read_json_object, atomic_write_json
from daxlab.runtime.candidate_operator_telemetry import browser_operator_snapshot
from test_operator_console_projection import console_sources
from test_operator_console_http import console_server as console_server, request


def test_deep_malformed_json_returns_bounded_503_not_process_disconnect(console_server):
    _, server, root = console_server
    (root/'heartbeat.json').write_text('['*1500+'0'+']'*1500)
    code, _, body = request(server)
    assert code == 503
    assert len(body) < 5000
    assert json.loads(body)['source_available'] is False


def test_oversized_heartbeat_is_rejected_before_unbounded_read(console_server):
    _, server, root = console_server
    (root/'heartbeat.json').write_bytes(b'x'*(4*1024*1024+1))
    code, _, body = request(server)
    assert code == 503
    assert len(body) < 5000


def test_credential_filtering_failure_is_explicit_without_exposing_secret(console_server):
    _, server, root = console_server
    hb = read_json_object(root/'heartbeat.json')
    hb['extra'] = {'password':'SYNTHETIC_ONLY_SECRET'}
    atomic_write_json(root/'heartbeat.json',hb)
    code, _, body = request(server)
    assert code == 503
    assert b'SYNTHETIC_ONLY_SECRET' not in body
    assert json.loads(body)['alerts'][0]['code'] == 'CREDENTIAL_FILTERING_FAILURE'


def test_existing_virtual_pending_entry_and_candidate_input_enums_remain_visible():
    _, snap, _, _, _ = console_sources()
    snap['virtual_position']['status'] = 'PENDING_ENTRY'
    snap['runtime']['health_source'] = 'CANDIDATE_INPUT'
    v = browser_operator_snapshot(snap)
    assert v['virtual_position']['status'] == 'PENDING_ENTRY'
    assert v['runtime']['health_source'] == 'CANDIDATE_INPUT'
