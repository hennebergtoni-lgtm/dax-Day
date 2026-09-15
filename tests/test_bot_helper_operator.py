"""V3 producer through existing HTTP/DOM; external provider I/O is injected."""
from datetime import datetime, timedelta, timezone
import importlib.util
import json
from pathlib import Path
import threading

import pytest

from daxlab.runtime.atomic_json import atomic_write_json
from test_operator_console_http import request
from test_run_ig_predemo_readiness_2238 import MatrixClient, runner


SPEC = importlib.util.spec_from_file_location("helper_operator_test", Path("scripts/serve_operator_console.py"))
console = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(console)


def producer(failed=None):
    evidence, _ = runner.collect(MatrixClient(raise_resource=failed), epic="IX.D.DAX.IFMM.IP", instrument_id="DAX", bars=40)
    return runner._finalize_evidence(evidence, cleanup_status="PASS", cleanup_error_code="NONE")[0]


@pytest.fixture
def ig_server(tmp_path):
    evidence = producer()
    path = tmp_path / "READINESS.json"
    atomic_write_json(path, evidence)
    server = console.OperatorReadServer(state_dir=tmp_path, port=0, ig_evidence_path=path,
        ig_evidence_fingerprint=evidence["fingerprint"], ig_instrument_id="DAX")
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
    thread.start()
    yield server, path, evidence
    server.shutdown()
    server.server_close()
    thread.join(timeout=2)


def test_v3_existing_get_route_preserves_source_unknown_and_safety(ig_server):
    server, path, evidence = ig_server
    status, _, body = request(server)
    assert status == 200
    view = json.loads(body)
    assert view["system"]["EXECUTION"]["state"] == "DISABLED"
    assert view["execution_capability"] == "NONE" and view["order_execution_enabled"] is False
    assert view["system"]["MT5"]["state"] == "UNKNOWN"
    assert view["timestamps"]["heartbeat_observed_at"] is None
    assert view["provenance"]["snapshot_fingerprint"] == evidence["fingerprint"]
    assert "BROKER_ECONOMICS_UNVERIFIED" in view["blockers"]
    assert view["helper_diagnostics"]["last_transition"] is None
    later = json.loads(request(server)[2])
    assert later["timestamps"]["snapshot_generated_at"] == view["timestamps"]["snapshot_generated_at"]
    assert later["timestamps"]["snapshot_age_seconds"] >= view["timestamps"]["snapshot_age_seconds"]
    assert request(server, method="POST")[0] == 405
    assert request(server, headers={"Origin": "https://other.invalid"})[0] == 403
    assert not (path.parent / "heartbeat.json").exists()


@pytest.mark.parametrize("failed", ["ACCOUNTS", "MARKET_V4", "M5_PRICES", "POSITIONS_B"])
def test_partial_producer_preserves_blockers_without_mt5(failed):
    evidence = producer(failed)
    view = console.build_ig_operator_projection(evidence, queried_at=datetime.now(timezone.utc), instrument_id="DAX")
    assert view["state"] == "BLOCKED"
    assert view["system"]["MT5"]["state"] == "UNKNOWN"
    assert view["source_available"] is True
    assert len(view["read_outcomes"]) == 8
    assert next(row for row in view["read_outcomes"] if row["resource"] == failed)["status"] == "UNKNOWN"


def test_v3_source_time_future_unknown_schema_or_instrument_rejected():
    evidence = producer()
    now = datetime.fromisoformat(evidence["collected_at_utc"])
    with pytest.raises(ValueError):
        console.build_ig_operator_projection(evidence, queried_at=now-timedelta(seconds=1), instrument_id="DAX")
    with pytest.raises(ValueError):
        console.build_ig_operator_projection(evidence, queried_at=datetime.now(timezone.utc), instrument_id="GOLD")
    evidence["schema"] = "DAXLAB_IG_PREDEMO_READINESS_V9"
    with pytest.raises(ValueError):
        console.build_ig_operator_projection(evidence, queried_at=datetime.now(timezone.utc), instrument_id="DAX")


@pytest.mark.parametrize("malicious", ["Bearer sensitive-value", "postgres://user:password@host/db", "<img src=x onerror=alert(1)>", "-----BEGIN PRIVATE KEY-----", {"pAsSwOrD": ["sensitive-value"]}])
def test_untrusted_extra_payload_never_reaches_existing_get(ig_server, malicious):
    server, path, evidence = ig_server
    evidence["untrusted"] = {"stdout": malicious, "url": malicious, "pointer": malicious}
    evidence.pop("fingerprint")
    evidence["fingerprint"] = runner._fingerprint(evidence)
    server.ig_evidence_fingerprint = evidence["fingerprint"]
    atomic_write_json(path, evidence)
    status, _, body = request(server)
    assert status in {200, 503}
    assert b"sensitive-value" not in body and b"onerror" not in body and b"PRIVATE KEY" not in body


def test_actual_browser_390px_existing_dom_and_get_route(ig_server):
    """Real Chromium layout/JS, mandatory in browser-equipped acceptance CI."""
    import os
    import shutil
    import subprocess

    node = shutil.which("node")
    env = dict(os.environ)
    env["NODE_PATH"] = env.get("NODE_PATH") or env.get("CODEX_PRIMARY_RUNTIME_NODE_MODULES", "")
    probe = subprocess.run([node, "-e", "const p=require('playwright');process.exit(require('fs').existsSync(p.chromium.executablePath())?0:2)"],
        env=env, capture_output=True) if node else None
    if probe is None or probe.returncode:
        if os.environ.get("BOT_HELPER_REQUIRE_BROWSER") == "1":
            pytest.fail("actual Chromium acceptance dependency unavailable")
        pytest.skip("actual Chromium unavailable; 390px browser acceptance NOT VERIFIED")
    server, _, _ = ig_server
    script = r"""
const {chromium}=require('playwright');
(async()=>{
 const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 try {
  const page=await browser.newPage({viewport:{width:390,height:844}});
  await page.goto(process.argv[1]);
  await page.waitForFunction(()=>document.querySelector('#helpers').textContent.includes('IG_READINESS_V3'));
  const text=await page.locator('#helpers').innerText();
  for(const field of ['Source','Age (s)','Reason','Dependency','Evidence','Last transition','UNKNOWN']) {
   if(!text.includes(field)) throw new Error('missing diagnostic '+field);
  }
  if(!(await page.locator('#system').innerText()).includes('DISABLED')) throw new Error('execution not disabled');
  if(await page.evaluate(()=>document.documentElement.scrollWidth>390)) throw new Error('mobile horizontal overflow');
  const first=await page.evaluate(()=>fetch('/api/operator').then(r=>r.json()));
  await page.locator('#refresh').click();
  const second=await page.evaluate(()=>fetch('/api/operator').then(r=>r.json()));
  if(first.timestamps.snapshot_generated_at!==second.timestamps.snapshot_generated_at) throw new Error('fetch renewed source');
  await page.route('**/api/operator',route=>route.abort());
  await page.locator('#refresh').click();
  await page.waitForFunction(()=>document.querySelector('#blockers').textContent.includes('RUNTIME_SOURCE_UNAVAILABLE_OR_INVALID'));
  if((await page.locator('#helpers').innerText()).includes('IG_READINESS_V3')) throw new Error('cached diagnostic survived failure');
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
"""
    subprocess.run([node, "-e", script, f"http://127.0.0.1:{server.server_address[1]}/"],
        env=env, check=True, capture_output=True, text=True, timeout=60)


def test_malicious_raw_row_status_is_not_an_operator_string(ig_server):
    server, path, evidence = ig_server
    evidence["authenticated_read_matrix"]["resources"][0]["status"] = "<img src=x onerror=alert(1)>"
    evidence.pop("fingerprint")
    evidence["fingerprint"] = runner._fingerprint(evidence)
    server.ig_evidence_fingerprint = evidence["fingerprint"]
    atomic_write_json(path, evidence)
    _, _, body = request(server)
    assert b"onerror" not in body


def test_get_runs_real_coordinator_with_unknown_identity_and_replay_scope(ig_server, monkeypatch):
    from daxlab.runtime import bot_helper

    calls = []
    original = bot_helper.coordinate

    def traced(events, **kwargs):
        result = original(events, **kwargs)
        calls.append((events, result))
        return result

    monkeypatch.setattr(bot_helper, "coordinate", traced)
    server, _, evidence = ig_server
    code, _, body = request(server)
    assert code == 200 and len(calls) == 1
    view = json.loads(body)
    assert [c["role"] for c in view["helper_cycle"]["checks"]] == ["H", "D", "B", "S", "O"]
    assert view["helper_cycle"]["shadow_allowed"] is False
    assert "IDENTITY_MISMATCH" in view["helper_cycle"]["blockers"]
    assert view["helper_cycle"]["subject"]["code_head"] is None
    assert view["helper_cycle"]["subject"]["session_id"] is None
    assert view["helper_cycle"]["evidence_scopes"] == ["REPLAY"]
    assert all(event.observed_at == evidence["collected_at_utc"] for event in calls[0][0])
    assert all(c["last_transition"] is None for c in view["helper_cycle"]["checks"])


@pytest.mark.parametrize("market_data", [None, [], "Bearer hidden-provider-secret", {"status": "PASS", "latest_closed_m5": {"close_time": "<script>hidden-provider-secret</script>"}, "freshness_max_age_seconds": 600}, {"status": "PASS", "latest_closed_m5": {"close_time": "2026-09-15T09:00:00+00:00"}, "freshness_max_age_seconds": 1e200}, {"status": "PASS", "latest_closed_m5": {"close_time": "2026-09-15T09:00:00+00:00"}, "freshness_max_age_seconds": 10**400}])
def test_derived_m5_projection_failure_preserves_eight_read_outcomes(ig_server, market_data):
    server, path, evidence = ig_server
    evidence["market_data"] = market_data
    evidence.pop("fingerprint")
    evidence["fingerprint"] = runner._fingerprint(evidence)
    server.ig_evidence_fingerprint = evidence["fingerprint"]
    atomic_write_json(path, evidence)
    status, _, body = request(server)
    assert status == 200
    view = json.loads(body)
    assert len(view["read_outcomes"]) == 8
    assert view["helper_cycle"]["checks"][1]["status"] != "PASS"
    assert b"hidden-provider-secret" not in body


@pytest.mark.parametrize("secret", ["CST: hidden-provider-secret", "X-SECURITY-TOKEN: hidden-provider-secret", "api_key=hidden-provider-secret", "pAsSwOrD=hidden-provider-secret", "postgresql://user:hidden-provider-secret@db.invalid/x", "https://provider.invalid?token=hidden-provider-secret"])
def test_provider_secret_and_scope_claims_cannot_become_helper_evidence(ig_server, secret):
    server, path, evidence = ig_server
    evidence["evidence_scope"] = "REAL_BROKER_READ"
    evidence["unknown_nested"] = [{"Exception": secret, "stdErr": secret, "pointer": secret}]
    evidence.pop("fingerprint")
    evidence["fingerprint"] = runner._fingerprint(evidence)
    server.ig_evidence_fingerprint = evidence["fingerprint"]
    atomic_write_json(path, evidence)
    status, _, body = request(server)
    assert status == 200
    assert b"hidden-provider-secret" not in body
    assert json.loads(body)["helper_cycle"]["evidence_scopes"] == ["REPLAY"]


@pytest.mark.parametrize("threshold", [601.0, 3600.0, 1e9])
def test_noncanonical_finite_ttl_is_data_invalid_and_preserves_raw_source(ig_server, threshold):
    server, path, evidence = ig_server
    evidence["market_data"]["freshness_max_age_seconds"] = threshold
    evidence.pop("fingerprint")
    evidence["fingerprint"] = runner._fingerprint(evidence)
    server.ig_evidence_fingerprint = evidence["fingerprint"]
    atomic_write_json(path, evidence)
    before = path.read_bytes()
    code, _, body = request(server)
    assert code == 200
    view = json.loads(body)
    data_check = next(check for check in view["helper_cycle"]["checks"] if check["role"] == "D")
    assert data_check["status"] != "PASS"
    assert "DATA_INVALID" in data_check["reason_codes"]
    assert data_check["valid_until"] is None
    assert len(view["read_outcomes"]) == 8
    assert path.read_bytes() == before
