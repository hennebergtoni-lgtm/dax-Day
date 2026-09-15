"""Independent V1 contract oracles; real owners, synthetic external I/O only.

The JSON scenarios are fixed before implementation. Registry existence is never
counted as scenario success. No real host or broker claim follows from this suite.
"""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from daxlab.domain.market import InstrumentId
from daxlab.runtime.bot_helper import coordinate, run_helper_shadow_candle
from daxlab.runtime.bot_helper_contract import HelperSubject, digest, observation
from daxlab.runtime.candidate_config import Cand001Config
from daxlab.runtime.candidate_shadow_orchestrator import Cand001ShadowState
from daxlab.runtime.candidate_sizing import Cand001SimulationSizingPolicy
from daxlab.runtime.contracts import Candle, RuntimeMode
from daxlab.runtime.manifests import RunManifest

from test_independent_pretrade_controls import observation as ptc_observation
from test_independent_pretrade_controls import policy as ptc_policy
from test_independent_pretrade_controls import protection
from test_run_ig_predemo_readiness_2238 import MatrixClient, runner

ROOT = Path(__file__).resolve().parents[1]
SPEC = json.loads((ROOT / "tests/fixtures/bot_helper_acceptance_v1.json").read_text())
HEAD = "aa11dc32fbd91c84edea19816e13fb6dc613a964"
UTC = timezone.utc
PASS_NUMBER = int(os.environ.get("BOT_HELPER_PASS", "1"))
SESSION_DAY = 15 if PASS_NUMBER == 1 else 17
PRICE_OFFSET = 0.0 if PASS_NUMBER == 1 else 1000.0


def manifest():
    return RunManifest.build(dataset_fingerprint="d" * 64, engine_fingerprint="e" * 64,
                             config={"candidate": Cand001Config(),
                                     "sizing": Cand001SimulationSizingPolicy()},
                             mode=RuntimeMode.SHADOW)


def subject():
    return HelperSubject(run_id=manifest().manifest_fingerprint, provider="SYNTHETIC",
                         environment="SHADOW", account_fingerprint="a" * 64,
                         instrument_id=InstrumentId("DE40"),
                         market_contract_fingerprint="c" * 64, session_id=f"2026-09-{SESSION_DAY:02d}",
                         code_head=HEAD, config_fingerprint=manifest().config_fingerprint,
                         instrument_identity_fingerprint="b" * 64,
                         risk_policy_fingerprint=digest(ptc_policy()))


def bar(index=0, *, close=101.0, **changes):
    event = datetime(2026, 9, SESSION_DAY, 7, 0, tzinfo=UTC) + timedelta(minutes=5 * index)
    args = dict(symbol="DE40", timeframe="5m", event_time=event,
                close_time=event + timedelta(minutes=5), open=100.0,
                high=max(103.0, close), low=98.0, close=close, volume=None,
                source="TEST", received_at=event + timedelta(minutes=5, seconds=1),
                is_closed=True)
    values = {**args, **changes}
    for field in ("open", "high", "low", "close"):
        values[field] += PRICE_OFFSET
    return Candle(**values)


def events(now, *, subject_value=None, overrides=None):
    bound = subject_value or subject()
    return tuple(observation(subject=bound, role=role,
                             status=(overrides or {}).get(role, "PASS"),
                             source_time=now - timedelta(seconds=1), observed_at=now,
                             valid_until=now + timedelta(seconds=120),
                             evidence_scope="SYNTHETIC", producer_epoch="e" * 64)
                 for role in ("H", "D", "B", "S", "O"))


def run(candle, *, state=None, now=None, event_values=None, **kwargs):
    stamp = now or candle.received_at
    return run_helper_shadow_candle(
        state or Cand001ShadowState(), candle, observed_at=stamp, run_manifest=manifest(),
        subject=subject(), events=event_values or events(stamp), **kwargs,
    )


def assert_blocked(result, original):
    """Fixed oracle deliberately independent of the coordinator implementation."""
    assert result.cycle.shadow_allowed is False
    assert result.shadow_result is None
    assert result.state == original
    assert result.cycle.shadow_blockers


def test_T01_actual_candidate_session_keeps_one_intent_and_one_outcome():
    state = Cand001ShadowState()
    bars = [bar(0), bar(1, close=102.0), bar(2),
            bar(3, close=104.0, high=105.0),
            bar(4, open=104.0, high=108.0, low=101.0, close=106.0),
            bar(5, open=106.0, high=116.0, low=103.0, close=115.0)]
    intents, outcomes = [], []
    previous = None
    for candle in bars:
        result = run(candle, state=state, previous_candle=previous)
        assert result.cycle.shadow_allowed is True
        assert result.shadow_result is not None
        state = result.state
        previous = candle
        if result.shadow_result.intent_to_publish is not None:
            intents.append(result.shadow_result.intent_to_publish)
        if result.shadow_result.outcome_to_publish is not None:
            outcomes.append(result.shadow_result.outcome_to_publish)
        payload = result.cycle.as_dict()
        assert payload["execution_capability"] == "NONE"
        assert payload["order_execution_enabled"] is False
    assert len(intents) == 1
    assert len(outcomes) == 1
    assert state.active_trade is None


def test_T01_isolated_shadow_not_blocked_by_missing_broker_truth():
    candle = bar()
    result = run(candle, event_values=events(candle.received_at, overrides={"B": "UNKNOWN"}))
    assert result.cycle.shadow_allowed is True
    assert result.shadow_result is not None
    assert result.shadow_result.intent_to_publish is None


@pytest.mark.parametrize("kind", ["stale_source_new_receive", "open", "gap", "duplicate", "out_of_order", "provider_revision"])
def test_T02_data_gate_precedes_real_admission_and_preserves_state(kind):
    previous = bar()
    original = run(previous).state
    now = None
    if kind == "stale_source_new_receive":
        candle = bar(1)
        now = candle.received_at + timedelta(minutes=10)
    elif kind == "open":
        candle = bar(1, is_closed=False)
    elif kind == "gap":
        candle = bar(3)
    elif kind == "duplicate":
        candle = previous
    elif kind == "provider_revision":
        candle = replace(previous, close=102.0 + PRICE_OFFSET)
    else:
        candle = bar(-1)
    result = run(candle, state=original, now=now, previous_candle=previous)
    assert_blocked(result, original)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
@pytest.mark.parametrize("field", ["open", "high", "low", "close"])
def test_T02_nonfinite_rejected_by_actual_candle_owner(field, value):
    with pytest.raises(ValueError):
        bar(**{field: value})


def test_T02_invalid_ohlc_rejected_by_actual_candle_owner():
    with pytest.raises(ValueError):
        bar(high=97.0)


@pytest.mark.parametrize("case", SPEC["ptc_variants"], ids=lambda case: case["id"])
def test_T06_every_independent_ptc_veto_reaches_real_admission_and_operator(case):
    candle = bar(3, close=104.0, high=105.0)
    original = Cand001ShadowState()
    ptc = dict(policy=ptc_policy(), observation={**ptc_observation(), **case["observation_change"]},
               protection=protection())
    assert ptc["protection"].allow_evidence is True
    result = run(candle, state=original, ptc_inputs=ptc)
    assert_blocked(result, original)
    assert case["expected_blocker"] in json.dumps(result.cycle.as_dict())


def test_T06_oracle_negative_control_detects_disabled_guard(monkeypatch):
    import daxlab.runtime.bot_helper as helper
    original = Cand001ShadowState()
    bad = bar(1)
    real_gate = helper.run_helper_shadow_candle
    result = real_gate(original, bad, observed_at=bad.received_at + timedelta(minutes=10),
                      run_manifest=manifest(), subject=subject(),
                      events=events(bad.received_at + timedelta(minutes=10)))
    assert_blocked(result, original)
    # Bypass the actual runtime eligibility reducer, leaving real Candidate owner
    # intact. The same independent oracle must now fail: this proves sensitivity
    # to a disabled guard, not just a hand-crafted red/green dictionary.
    original_coordinate = helper.coordinate
    def disabled_guard(*args, **kwargs):
        actual = original_coordinate(*args, **kwargs)
        return replace(actual, shadow_blockers=())
    monkeypatch.setattr(helper, "coordinate", disabled_guard)
    # The canonical owner independently recomputes stale data: bypassing only
    # the reducer cannot defeat that second admission boundary.
    with pytest.raises(ValueError, match="HELPER_ADMISSION_BLOCKED"):
        real_gate(original, bad, observed_at=bad.received_at + timedelta(minutes=10),
                  run_manifest=manifest(), subject=subject(),
                  events=events(bad.received_at + timedelta(minutes=10)))
    monkeypatch.setattr(helper, "runtime_data_reasons", lambda *args, **kwargs: ())
    corrupted = real_gate(original, bad,
                          observed_at=bad.received_at + timedelta(minutes=10),
                          run_manifest=manifest(), subject=subject(),
                          events=events(bad.received_at + timedelta(minutes=10)))
    assert corrupted.shadow_result is not None
    assert corrupted.state != original
    with pytest.raises(AssertionError):
        assert_blocked(corrupted, original)


def test_T10_stale_without_any_new_delivery_blocks_current_gate():
    now = bar().received_at
    fixed = events(now)
    assert coordinate(fixed, subject=subject(), now=now).shadow_allowed is True
    expired = coordinate(fixed, subject=subject(), now=now + timedelta(minutes=10))
    assert expired.shadow_allowed is False
    assert expired.shadow_blockers


def test_T10_identical_delivery_is_idempotent():
    now = bar().received_at
    fixed = events(now)
    first = coordinate(fixed, subject=subject(), now=now)
    repeated = coordinate(fixed + fixed, subject=subject(), now=now)
    assert first.as_dict() == repeated.as_dict()


@pytest.mark.parametrize("kind", ["raw_commit", "receipt_commit"])
def test_T09_real_process_crash_recovers_only_confirmed_records(tmp_path, kind):
    namespace = tmp_path / kind
    child = r'''
import os, sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / "scripts"))
import run_ig_predemo_readiness_2238 as r
p = Path(sys.argv[1]); kind = sys.argv[2]
w = r.ReadinessObservationWriter(p, head="aa11dc32fbd91c84edea19816e13fb6dc613a964", evidence_scope="SYNTHETIC")
w.start()
if kind == "raw_commit":
    real = r.atomic_write_json
    def write(path, payload, **kwargs):
        if path.name == "00.receipt.json": os._exit(73)
        return real(path, payload, **kwargs)
    r.atomic_write_json = write
row = r._initial_readiness_rows()[0]
row.update(status="PASS", reason_code="NONE", response_shape_status="VALID")
w.record(0, row)
os._exit(73)
'''
    result = subprocess.run([sys.executable, "-c", child, str(namespace), kind], cwd=ROOT,
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 73, result.stderr
    before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in namespace.iterdir()}
    recovered = runner.recover_readiness_observations(namespace, expected_head=HEAD)
    assert recovered["confirmed_slots"] == ([] if kind == "raw_commit" else [0])
    assert recovered["authenticated_read_matrix"]["row_count"] == 8
    assert len(recovered["authenticated_read_matrix"]["resources"]) == 8
    assert recovered["evidence_scope"] == "SYNTHETIC"
    assert recovered["order_execution_enabled"] is False
    assert {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in namespace.iterdir()} == before


@pytest.mark.parametrize("failure", ["exception", "missing_file", "wrong_bytes"])
def test_T13_transfer_failure_keeps_original_local_evidence(tmp_path, failure):
    evidence, components = runner.collect(MatrixClient(), epic="IX.D.DAX.IFM.IP", instrument_id="DAX", bars=12)
    evidence, components = runner._finalize_evidence(evidence, cleanup_status="PASS", cleanup_error_code="NONE")
    namespace = tmp_path / failure
    def sink(files):
        if failure == "exception":
            raise OSError("synthetic sink unavailable")
        if failure == "missing_file":
            return {}
        return {name: b"wrong" for name in files}
    with pytest.raises(OSError):
        runner._publish(namespace, evidence, components, head=HEAD, synthetic_sink=sink)
    disk_manifest = json.loads((namespace / "MANIFEST.json").read_text())
    for name, expected in disk_manifest["files"].items():
        assert hashlib.sha256((namespace / name).read_bytes()).hexdigest() == expected
    assert json.loads((namespace / "READINESS.json").read_text()) == evidence


def test_T15_exact_registry_semantics_and_scope_are_not_promoted():
    registry = json.loads((ROOT / "research/acceleration_program_v1.json").read_text())
    current = registry["failures"]
    assert [f["id"] for f in current] == [f"F{i:03d}" for i in range(1, 101)]
    assert [{key: f[key] for key in baseline} for f, baseline in
            zip(current, SPEC["registry_baseline"], strict=True)] == SPEC["registry_baseline"]
    assert registry["real_broker_evidence_refs"] == []
    assert [g["id"] for g in SPEC["groups"]] == [f"T{i:02d}" for i in range(1, 16)]
    for group in SPEC["groups"]:
        assert group["variants"]
        for path in group["owner_paths"]:
            assert (ROOT / path).is_file()


@pytest.mark.parametrize("field,value", [
    ("run_id", "1" * 64), ("provider", "IG"), ("environment", "DEMO"),
    ("account_fingerprint", "2" * 64), ("instrument_id", InstrumentId("GOLD")),
    ("market_contract_fingerprint", "3" * 64), ("session_id", "2099-09-16"),
    ("code_head", "4" * 40), ("config_fingerprint", "5" * 64),
])
def test_T05_cross_wired_subjects_cannot_open_current_gate(field, value):
    now = bar().received_at
    wrong = replace(subject(), **{field: value})
    mixed = events(now, subject_value=wrong)
    result = coordinate(mixed, subject=subject(), now=now)
    assert result.shadow_allowed is False
    assert result.shadow_blockers


def test_T10_same_identity_different_payload_is_preserved_contradiction():
    now = bar().received_at
    fixed = events(now)
    conflict = replace(fixed[1], status="BLOCKED", reason_codes=("DATA_INVALID",))
    assert conflict.event_id == fixed[1].event_id
    assert conflict.payload_hash != fixed[1].payload_hash
    result = coordinate(fixed + (conflict,), subject=subject(), now=now)
    assert result.shadow_allowed is False
    assert "CONTRADICTION" in json.dumps(result.as_dict())


def test_T10_missing_dependency_is_explicit_and_blocks_dependent_gate():
    now = bar().received_at
    fixed = list(events(now))
    fixed[1] = replace(fixed[1], dependency_event_ids=("f" * 64,))
    result = coordinate(tuple(fixed), subject=subject(), now=now)
    assert result.shadow_allowed is False
    assert "DEPENDENCY" in json.dumps(result.as_dict())


def test_T10_self_dependency_cycle_is_bounded_and_visible():
    now = bar().received_at
    fixed = list(events(now))
    fixed[1] = replace(fixed[1], dependency_event_ids=(fixed[1].event_id,))
    result = coordinate(tuple(fixed), subject=subject(), now=now)
    assert result.shadow_allowed is False
    assert "CYCLE" in json.dumps(result.as_dict())


def test_T10_257_unique_events_overflow_instead_of_losing_safety():
    now = bar().received_at
    fixed = events(now)
    storm = tuple(replace(fixed[0], source_sequence=i) for i in range(257))
    result = coordinate(storm, subject=subject(), now=now)
    assert result.shadow_allowed is False
    assert "OVERFLOW" in json.dumps(result.as_dict())


def test_T11_scope_cannot_be_promoted_by_untrusted_payload():
    from daxlab.runtime.bot_helper_contract import parse_event
    event = events(bar().received_at)[0]
    raw = json.dumps(event.as_dict())
    assert parse_event(raw, evidence_scope="SYNTHETIC") == event
    with pytest.raises(ValueError):
        parse_event(raw, evidence_scope="REAL_BROKER_READ")


@pytest.mark.parametrize("mutation", [
    {"source_time": "2026-09-15T07:04:00"},
    {"source_time": "2026-09-15T07:09:00+00:00"},
    {"observed_at": "2026-09-15T07:03:00+00:00"},
    {"source_sequence": True}, {"source_sequence": float("nan")},
    {"order_execution_enabled": 0}, {"order_execution_enabled": "false"},
    {"execution_capability": True}, {"schema_version": "UNRECOGNIZED"},
    {"password": "NEVER_PUBLISH_SECRET"},
    {"evidence_refs": ["https://example.invalid/?Bearer=NEVER_PUBLISH_SECRET"]},
    {"reason_codes": ["<script>NEVER_PUBLISH_SECRET</script>"]},
])
def test_T11_invalid_envelope_has_fixed_secret_free_rejection(mutation):
    from daxlab.runtime.bot_helper_contract import parse_event
    raw = {**events(bar().received_at)[0].as_dict(), **mutation}
    with pytest.raises(ValueError) as error:
        parse_event(json.dumps(raw), evidence_scope="SYNTHETIC")
    assert str(error.value) == "HELPER_EVENT_REJECTED"


@pytest.mark.parametrize("value", [None, 1, [], {}, {"password": "NEVER_PUBLISH_SECRET"}])
def test_T11_malformed_nested_subject_cannot_escape_parser_guard(value):
    from daxlab.runtime.bot_helper_contract import parse_event
    raw = events(bar().received_at)[0].as_dict()
    raw["subject"]["instrument_id"] = value
    with pytest.raises(ValueError) as error:
        parse_event(json.dumps(raw), evidence_scope="SYNTHETIC")
    assert str(error.value) == "HELPER_EVENT_REJECTED"


def test_T11_duplicate_json_keys_are_rejected_even_when_values_match():
    from daxlab.runtime.bot_helper_contract import parse_event
    event = events(bar().received_at)[0]
    raw = json.dumps(event.as_dict())
    raw = '{"execution_capability":"NONE",' + raw[1:]
    with pytest.raises(ValueError, match="HELPER_EVENT_REJECTED"):
        parse_event(raw, evidence_scope="SYNTHETIC")


@pytest.mark.parametrize("crash_boundary", ["before_state_commit", "after_state_commit"])
def test_T09_real_candidate_checkpoint_restart_no_double_intent(tmp_path, crash_boundary):
    """Kill an actual helper→Candidate cycle; restart through canonical parser.

    A precommit in-memory result is not a published durable effect. A committed
    publication identity survives and the duplicated bar is blocked on restart.
    """
    state_file = tmp_path / "candidate.json"
    child = r'''
import json, os, sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / "tests"))
from test_bot_helper_acceptance import run, bar, manifest, Cand001Config, Cand001ShadowState
from daxlab.runtime.atomic_json import atomic_write_json, read_json_object
from daxlab.runtime.candidate_shadow_checkpoint import candidate_shadow_checkpoint_payload, parse_candidate_shadow_checkpoint_payload
p = Path(sys.argv[1]); phase = sys.argv[2]
breakout = bar(3, close=104.0, high=105.0)
def payload(state):
    return candidate_shadow_checkpoint_payload(state, run_manifest=manifest(), config=Cand001Config())
if phase in {"before_state_commit", "after_state_commit"}:
    state = Cand001ShadowState()
    previous = None
    for candle in (bar(0), bar(1, close=102.0), bar(2)):
        result = run(candle, state=state, previous_candle=previous)
        assert result.cycle.shadow_allowed
        state = result.state; previous = candle
    atomic_write_json(p, payload(state))
    pending = run(breakout, state=state, previous_candle=bar(2))
    assert pending.shadow_result.intent_to_publish is not None
    if phase == "after_state_commit": atomic_write_json(p, payload(pending.state))
    os._exit(74)
state = parse_candidate_shadow_checkpoint_payload(read_json_object(p), run_manifest=manifest(), config=Cand001Config())
result = run(breakout, state=state, previous_candle=bar(2))
if phase == "resume_after":
    assert result.shadow_result is None
    assert result.state == state
else:
    assert result.shadow_result.intent_to_publish is not None
    atomic_write_json(p, payload(result.state))
assert len(result.state.publication.published_intent_ids) == 1
assert len(result.state.publication.published_outcome_ids) == 0
assert result.state.order_execution_enabled is False
print(json.dumps({"intents":1,"outcomes":0,"execution":"DISABLED"}))
'''
    crash = subprocess.run([sys.executable, "-c", child, str(state_file), crash_boundary],
                           cwd=ROOT, capture_output=True, text=True, timeout=30)
    assert crash.returncode == 74, crash.stderr
    mode = "resume_after" if crash_boundary == "after_state_commit" else "resume_before"
    resumed = subprocess.run([sys.executable, "-c", child, str(state_file), mode], cwd=ROOT,
                             capture_output=True, text=True, timeout=30)
    assert resumed.returncode == 0, resumed.stderr
    assert json.loads(resumed.stdout) == {"intents": 1, "outcomes": 0, "execution": "DISABLED"}
    digest_before = hashlib.sha256(state_file.read_bytes()).hexdigest()
    # Third process is an independent repeat after the successful resume. It must
    # retain byte-identical durable state and cannot consume another session slot.
    repeat = subprocess.run([sys.executable, "-c", child, str(state_file), "resume_after"],
                            cwd=ROOT, capture_output=True, text=True, timeout=30)
    assert repeat.returncode == 0, repeat.stderr
    assert hashlib.sha256(state_file.read_bytes()).hexdigest() == digest_before



def test_T06_explicitly_bound_healthy_ptc_reuses_owner_and_allows_shadow():
    candle = bar()
    result = run(candle, ptc_inputs={"policy": ptc_policy(), "observation": ptc_observation(),
                                    "protection": protection()})
    assert result.cycle.shadow_allowed is True
    assert result.shadow_result is not None
    assert result.shadow_result.intent_to_publish is None


@pytest.mark.parametrize("field,value", [
    ("account_fingerprint", "f" * 64),
    ("instrument_identity_fingerprint", "f" * 64),
    ("risk_policy_fingerprint", "f" * 64),
    ("instrument_identity_fingerprint", None),
    ("risk_policy_fingerprint", None),
])
def test_T06_ptc_policy_must_bind_current_subject_before_admission(field, value):
    candle = bar()
    original = Cand001ShadowState()
    wrong = replace(subject(), **{field: value})
    result = run_helper_shadow_candle(
        original, candle, observed_at=candle.received_at, run_manifest=manifest(),
        subject=wrong, events=events(candle.received_at, subject_value=wrong),
        ptc_inputs={"policy": ptc_policy(), "observation": ptc_observation(),
                    "protection": protection()},
    )
    assert_blocked(result, original)


def test_T15_harness_never_labels_missing_or_skipped_assertions_pass(tmp_path):
    from run_bot_helper_acceptance import read_results, summarize
    assert summarize([])["status"] == "NOT_EXECUTED"
    report = tmp_path / "raw.xml"
    report.write_text('<testsuite><testcase classname="test_example" '
                      'name="test_case[Bearer NEVER_PUBLISH_SECRET]"><skipped '
                      'message="NEVER_PUBLISH_SECRET"/></testcase></testsuite>')
    cases = read_results(report)
    assert summarize(cases)["status"] == "INCOMPLETE"
    assert cases[0]["status"] == "SKIPPED"
    assert "NEVER_PUBLISH_SECRET" not in json.dumps(cases)
    assert "Bearer" not in json.dumps(cases)


def test_T15_harness_failed_assertion_has_safe_fixed_metadata(tmp_path):
    from run_bot_helper_acceptance import read_results, summarize
    report = tmp_path / "raw.xml"
    report.write_text('<testsuite><testcase classname="test_example" '
                      'name="test_case[password=NEVER_PUBLISH_SECRET]">'
                      '<failure message="NEVER_PUBLISH_SECRET">Bearer SECRET</failure>'
                      '</testcase></testsuite>')
    cases = read_results(report)
    assert summarize(cases)["status"] == "FAIL"
    assert "SECRET" not in json.dumps(cases)
