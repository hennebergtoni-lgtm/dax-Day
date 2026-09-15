"""Execution display must fail closed on both sides of the HTTP boundary."""
from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess

import pytest

from daxlab.runtime.candidate_operator_query import validate_operator_console_safety
from test_operator_console_projection import console_sources, project
from test_operator_console_http import console_server as console_server, request


@pytest.mark.parametrize('state', ['GREEN', 'WARN', 'UNKNOWN', 'STALE', 'QUERY_REQUIRED'])
def test_backend_rejects_execution_tile_contradiction(state):
    raw, snap, hb, now, _ = console_sources()
    view = project(raw, snap, hb, now)
    view['system']['EXECUTION']['state'] = state
    with pytest.raises(ValueError, match='execution'):
        validate_operator_console_safety(view)


def test_actual_http_response_rejects_contradictory_projection(console_server, monkeypatch):
    module, server, _ = console_server
    raw, snap, hb, now, _ = console_sources()
    view = project(raw, snap, hb, now)
    view['source_available'] = True
    view['system']['EXECUTION']['state'] = 'GREEN'
    monkeypatch.setattr(module, 'read_local_operator_projection', lambda *a, **kw: deepcopy(view))
    code, _, body = request(server)
    assert code == 503
    assert json.loads(body)['system']['EXECUTION']['state'] == 'DISABLED'


def test_javascript_runs_validator_and_rejects_green_execution():
    node = shutil.which('node')
    if node is None:
        pytest.skip('Node unavailable; browser validator execution unverified')
    raw, snap, hb, now, _ = console_sources()
    view = project(raw, snap, hb, now)
    source = Path('web/operator.js').read_text().split("  el('refresh').addEventListener")[0]
    source += '\n globalThis.validateConsole=validate;})();'
    harness = source + '\nconst v=' + json.dumps(view) + ';validateConsole(v);v.system.EXECUTION.state="GREEN";let rejected=false;try{validateConsole(v);}catch{rejected=true;}if(!rejected)process.exit(1);'
    subprocess.run([node, '-e', harness], check=True, capture_output=True, text=True)
