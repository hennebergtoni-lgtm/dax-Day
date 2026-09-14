"""Synthetic offline regressions; these fixtures are never real-host evidence."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from test_ig_demo_readonly_probe import price_row

SPEC = importlib.util.spec_from_file_location(
    "ig_cand001_e2e_test", Path(__file__).resolve().parents[1] / "scripts/ig_cand001_shadow_e2e.py",
)
assert SPEC and SPEC.loader
host = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(host)
HEAD = "a" * 40
END = datetime(2026, 9, 14, 7, 20, tzinfo=timezone.utc)  # Berlin breakout candle


def live_fixture(end=END, *, breakout=True, age_seconds=231, request_age_seconds=None):
    now = end + timedelta(seconds=age_seconds)
    requested = end + timedelta(seconds=age_seconds if request_age_seconds is None else request_age_seconds)
    raw = [price_row(end - timedelta(minutes=5 * (n + 1))) for n in reversed(range(40))]
    if breakout:
        raw[-1] = price_row(end - timedelta(minutes=5), 110)
    from ig_demo_readonly_probe import _closed_candles
    rows = _closed_candles({"prices": raw}, epic=host.DEFAULT_EPIC,
                          instrument_id=host.DEFAULT_INSTRUMENT_ID, observed_at=now, closed_as_of=requested)
    probe = {
        "collection_started_at_utc": requested.isoformat(), "price_request_started_at_utc": requested.isoformat(),
        "observed_at_utc": now.isoformat(), "latest_closed_m5": rows[-1],
        "raw_m5_count": 40, "closed_m5_count": 40, "not_closed_m5_count": 0,
        "market": {"epic": host.DEFAULT_EPIC}, "execution_capability": "NONE",
        "order_execution_enabled": False, "m5_timestamp_contract": host.TIMESTAMP_CONTRACT,
        "m5_market_data_contract": host.canonical_ig_m5_contract(),
        "m5_freshness_basis": "TRUE_CLOSE_TIME",
        "m5_freshness_max_age_seconds": 600.0, "m5_freshness_state": "FRESH",
    }
    probe["fingerprint"] = host._fingerprint(probe)
    return probe, rows, now


def evidence(end=END, *, breakout=True, prior=None, age_seconds=231, request_age_seconds=None):
    probe, rows, now = live_fixture(end, breakout=breakout, age_seconds=age_seconds,
                                    request_age_seconds=request_age_seconds)
    payload = host.process_live_window(probe, rows, head=HEAD, observed_at=now, prior=prior)
    payload["fingerprint"] = host._fingerprint(payload)
    host.validate_evidence(payload, head=HEAD, now=now)
    return payload, now


def rehash(payload):
    payload.pop("fingerprint", None)
    payload["fingerprint"] = host._fingerprint(payload)


def test_real_adapter_shape_reaches_existing_strategy_decision_shadow_and_operator():
    payload, now = evidence()
    state = host.validate_evidence(payload, head=HEAD, now=now)
    view = payload["operator_projection"]
    assert view["candidate_id"] == "CAND-001"
    assert view["signal"]["direction"] == "LONG"
    assert view["admission"]["status"] == "ALLOWED"
    assert view["decision"]["action"] == "TRADE"
    assert state.active_trade is not None  # existing virtual owner, never broker
    assert view["safety"]["execution_capability"] == "NONE"
    assert view["safety"]["order_execution_enabled"] is False
    assert payload["decisions"][-1]["scope"] == "CURRENT"
    assert all(d["scope"] == "HISTORICAL_CATCHUP" for d in payload["decisions"][:-1])
    assert view["runtime"]["freshness_seconds"] == 231
    assert payload["protection_state"] == payload["reconciliation_state"] == "UNKNOWN"


def test_no_signal_without_complete_or_is_observable_not_strategy_override():
    payload, _ = evidence(datetime(2026, 9, 14, 12, tzinfo=timezone.utc), breakout=False)
    assert payload["operator_snapshot"]["signal"]["reason"] == "OR_INCOMPLETE"
    assert payload["operator_snapshot"]["decision"]["action"] == "NO_TRADE"
    assert payload["operator_snapshot"]["runtime"]["health_state"] == "GREEN"
    assert "OPENING_RANGE_NOT_COMPLETE_NO_SIGNAL_IS_VALID" in payload["warnings"]


def test_resume_consumes_one_new_bar_retains_existing_trade_and_publication_state():
    prior, _ = evidence(breakout=False)
    payload, _ = evidence(END + timedelta(minutes=5), prior=prior)
    assert len(payload["decisions"]) == 1
    assert payload["recovery_state"] == "RESUME_ANCHOR_RECONCILED"
    state = host.validate_evidence(payload, head=HEAD, now=utc_export(payload))
    assert state.pipeline.signal.or_slots == ("09:00", "09:05", "09:10")


def utc_export(payload):
    return datetime.fromisoformat(payload["exported_at_utc"])


def test_repeat_same_bar_blocks_and_does_not_mutate_prior():
    prior, now = evidence(breakout=False)
    original = deepcopy(prior)
    probe, rows, _ = live_fixture(breakout=False)
    with pytest.raises(host.HostTestBlocked, match="NO_NEW_FINALIZED_M5"):
        host.process_live_window(probe, rows, head=HEAD, observed_at=now, prior=prior)
    assert prior == original


@pytest.mark.parametrize("change", ["overlap", "missing_anchor", "gap", "future", "source"])
def test_state_and_adapter_conflicts_fail_closed(change):
    prior, _ = evidence(breakout=False)
    probe, rows, now = live_fixture(END + timedelta(minutes=5))
    if change == "overlap":
        rows[-2]["close"] += 0.1
    elif change == "missing_anchor":
        probe, rows, now = live_fixture(END + timedelta(hours=4))
    elif change == "gap":
        rows.pop(-2)
    elif change == "future":
        now -= timedelta(minutes=5)
    else:
        rows[-1]["source"] = "MT5"
    with pytest.raises(host.HostTestBlocked):
        host.process_live_window(probe, rows, head=HEAD, observed_at=now, prior=prior)


@pytest.mark.parametrize("change", ["head", "checkpoint", "execution", "dto", "decision", "unknown", "contract", "clock"])
def test_tamper_or_unproven_projection_rejected_even_with_outer_hash_recomputed(change):
    payload, now = evidence(breakout=False)
    if change == "head":
        payload["exact_code_head"] = "b" * 40
    elif change == "checkpoint":
        payload["checkpoint"]["order_execution_enabled"] = True
    elif change == "execution":
        payload["order_execution_enabled"] = True
    elif change == "dto":
        payload["operator_projection"]["decision"]["action"] = "TRADE"
    elif change == "decision":
        payload["decisions"][-1]["record"]["decision_id"] = "b" * 64
    elif change == "unknown":
        payload["reconciliation_state"] = "IN_SYNC"
    elif change == "contract":
        payload["ig_probe"]["m5_freshness_max_age_seconds"] = 9999
        probe = payload["ig_probe"]
        probe.pop("fingerprint")
        probe["fingerprint"] = host._fingerprint(probe)
    else:
        payload["processed_at_utc"] = (now - timedelta(seconds=1)).isoformat()
    rehash(payload)
    with pytest.raises((host.HostTestBlocked, ValueError)):
        host.validate_evidence(payload, head=HEAD, now=now)


def test_stale_reader_cannot_present_previous_success_as_current():
    payload, _ = evidence(breakout=False)
    with pytest.raises(host.HostTestBlocked, match="TELEMETRY_STALE"):
        host.validate_evidence(payload, head=HEAD, now=END + timedelta(seconds=601))
    host.validate_evidence(payload, head=HEAD, now=END + timedelta(seconds=600))


def test_cli_exception_does_not_print_provider_text_or_write_success(tmp_path, monkeypatch, capsys):
    # Exercise the historical plumbing behind a mocked data-contract gate; no live authorization.
    monkeypatch.setattr(host, "require_verified_live_provider_contract", lambda: None)
    monkeypatch.setattr(host, "check_code", lambda _: HEAD)
    monkeypatch.setattr(host.platform, "system", lambda: "Windows")
    def failure(**kwargs):
        raise RuntimeError("password=SYNTHETIC_SECRET_SENTINEL")
    monkeypatch.setattr(host, "collect_probe_with_candles", failure)
    monkeypatch.setattr(host.sys, "argv", ["test", "--expected-head", HEAD,
                                         "--credentials-file", "external.env", "--state-dir", str(tmp_path)])
    assert host.main() == 2
    output = capsys.readouterr().out
    assert "SYNTHETIC_SECRET_SENTINEL" not in output
    assert json.loads(output)["error_code"] == "DATA_TEST_FAILED"
    assert not (tmp_path / "evidence.json").exists()


def test_existing_writer_lock_blocks_before_any_network_read(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(host, "check_code", lambda _: HEAD)
    monkeypatch.setattr(host.platform, "system", lambda: "Windows")
    monkeypatch.setattr(host.sys, "argv", ["test", "--expected-head", HEAD,
                                         "--credentials-file", "external.env", "--state-dir", str(tmp_path)])
    monkeypatch.setattr(host, "collect_probe_with_candles", lambda **_: pytest.fail("network called"))
    with host.SingleInstanceLock(tmp_path / "writer.lock", "existing"):
        assert host.main() == 2
    assert json.loads(capsys.readouterr().out)["error_code"] == "STATE_TEST_FAILED"


def test_cli_atomic_bundle_can_be_read_but_same_bar_cannot_renew_it(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(host, "require_verified_live_provider_contract", lambda: None)
    probe, rows, now = live_fixture(breakout=False)
    monkeypatch.setattr(host, "check_code", lambda _: HEAD)
    monkeypatch.setattr(host.platform, "system", lambda: "Windows")
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return now
    monkeypatch.setattr(host, "datetime", Clock)
    monkeypatch.setattr(host, "collect_probe_with_candles", lambda **_: (probe, rows))
    args = ["test", "--expected-head", HEAD, "--credentials-file", "external.env",
            "--state-dir", str(tmp_path)]
    monkeypatch.setattr(host.sys, "argv", args)
    assert host.main() == 0
    capsys.readouterr()
    path = tmp_path / "evidence.json"
    original = path.read_bytes()
    assert host.main() == 2
    assert json.loads(capsys.readouterr().out)["error_code"] == "STATE_NO_NEW_FINALIZED_M5"
    assert path.read_bytes() == original
    monkeypatch.setattr(host.sys, "argv", ["test", "--expected-head", HEAD, "--read-evidence", str(path),
                                         "--expected-fingerprint", host.read_json_object(path)["fingerprint"]])
    assert host.main() == 0
    result = json.loads(capsys.readouterr().out)
    assert result["decision"]["action"] == "NO_TRADE"
    assert result["fingerprint"] == host.read_json_object(path)["fingerprint"]


def test_code_gate_rejects_parallel_tracked_edit_before_live_read(monkeypatch):
    monkeypatch.setattr(host.subprocess, "check_output", lambda cmd, **_: (
        HEAD if "rev-parse" in cmd else " M src/daxlab/runtime/candidate_signal.py"
    ))
    with pytest.raises(host.HostTestBlocked, match="TRACKED_DRIFT"):
        host.check_code(HEAD)


def test_import_from_other_worktree_blocks_even_with_clean_exact_head(monkeypatch, tmp_path):
    monkeypatch.setattr(host.subprocess, "check_output", lambda cmd, **_: HEAD if "rev-parse" in cmd else "")
    monkeypatch.setitem(host.sys.modules, "daxlab.foreign_runtime", SimpleNamespace(
        __file__=str(tmp_path / "other-worktree" / "runtime.py"),
    ))
    with pytest.raises(host.HostTestBlocked, match="IMPORT_PARITY"):
        host.check_code(HEAD)


@pytest.mark.parametrize("age", [0, 3.7, 59, 60, 231, 600])
def test_true_close_age_boundaries_preserve_complete_nominal_probe(age):
    payload, now = evidence(breakout=False, age_seconds=age)
    state = host.validate_evidence(payload, head=HEAD, now=now)
    assert state.pipeline.signal.last_close_time == END
    assert payload["operator_snapshot"]["runtime"]["last_bar_close_time"] == END.isoformat()
    assert payload["decisions"][-1]["close_time"] == END.isoformat()
    assert payload["ig_probe"]["latest_closed_m5"]["close_time"] == END.isoformat()
    assert payload["candidate_finalized_m5_count"] == 40
    assert payload["not_finalized_m5_count"] == 0
    assert payload["input_window"][-1]["close_time"] == END.isoformat()
    assert payload["execution_capability"] == "NONE"
    assert payload["order_execution_enabled"] is False


def test_additional_sixty_second_grace_is_retired() -> None:
    payload, _ = evidence(breakout=False, age_seconds=0, request_age_seconds=0)
    assert payload["latest_finalized_m5"]["close_time"] == END.isoformat()
    assert payload["not_finalized_m5_count"] == 0
    contract = payload["provider_finalization_contract"]
    assert contract["additional_grace_seconds"] == 0
    assert contract["grace_status"] == "RETIRED_SUPERSEDED_INTERVAL_END_WORKAROUND"


def test_candidate_finalization_excludes_future_true_close() -> None:
    rows = [{"close_time": END.isoformat()}, {
        "close_time": (END + timedelta(minutes=5)).isoformat(),
    }]
    assert host.finalized_rows(rows, END) == rows[:1]


def test_resume_advances_at_new_true_close_without_extra_grace() -> None:
    prior, _ = evidence(breakout=False, age_seconds=0)
    probe, rows, now = live_fixture(
        END + timedelta(minutes=5),
        breakout=False,
        age_seconds=0,
    )
    payload = host.process_live_window(probe, rows, head=HEAD, observed_at=now, prior=prior)
    assert payload["recovery_state"] == "RESUME_ANCHOR_RECONCILED"
    assert payload["decisions"][-1]["close_time"] == (END + timedelta(minutes=5)).isoformat()


def test_manifest_binds_canonical_contract_and_retired_grace(monkeypatch) -> None:
    base = host.manifest(HEAD)
    dataset = host.stable_fingerprint({
        "stream": "IG_READ_ONLY",
        "epic": host.DEFAULT_EPIC,
        "price": "MID_BID_ASK",
        "timestamp_contract": host.TIMESTAMP_CONTRACT,
        "symbol": "DE40",
        "timeframe": "5m",
        "market_data_contract": host.canonical_ig_m5_contract(),
        "provider_finalization": host.finalization_contract(),
    })
    assert base.dataset_fingerprint == dataset
    assert host.finalization_contract()["additional_grace_seconds"] == 0
    monkeypatch.setattr(host, "TIMESTAMP_CONTRACT", "LEGACY_INTERVAL_END")
    changed = host.manifest(HEAD)
    assert changed.dataset_fingerprint != base.dataset_fingerprint
    assert changed.manifest_fingerprint != base.manifest_fingerprint


def legacy_evidence():
    payload, now = evidence(breakout=False)
    payload["schema"] = "DAX_IG_CAND001_REAL_HOST_SHADOW_E2E_V2"
    payload.pop("state_contract")
    payload["provider_finalization_contract"] = {
        "contract": "IG_M5_CAND001_PROVIDER_FINALIZATION_GRACE_V1",
        "grace_seconds": 60,
        "eligibility_clock": "PRICE_REQUEST_STARTED_AT_UTC",
    }
    payload["ig_probe"]["m5_timestamp_contract"] = (
        "IG_MINUTE_5_SNAPSHOT_UTC_INTERVAL_END_V1"
    )
    rehash(payload)
    return payload, now


def test_old_evidence_without_contract_is_not_resume_compatible_even_with_same_head():
    prior, _ = legacy_evidence()
    probe, rows, now = live_fixture(END + timedelta(minutes=5), breakout=False)
    with pytest.raises(host.HostTestBlocked, match="FINALIZATION_CONTRACT_MIGRATION_REQUIRED"):
        host.process_live_window(probe, rows, head=HEAD, observed_at=now, prior=prior)


def test_old_checkpoint_manifest_in_new_envelope_is_explicit_drift():
    payload, now = evidence(breakout=False)
    payload["checkpoint"]["run_manifest_fingerprint"] = "b" * 64
    rehash(payload)
    with pytest.raises(host.HostTestBlocked, match="STATE_MANIFEST_DRIFT"):
        host.validate_evidence(payload, head=HEAD, now=now)


@pytest.mark.parametrize("field", ["high", "low", "close", "volume"])
def test_each_changed_processed_overlap_field_still_blocks_exactly(field):
    prior, _ = evidence(breakout=False, age_seconds=60)
    probe, rows, now = live_fixture(END + timedelta(minutes=5), breakout=False, age_seconds=60)
    rows[-2][field] = 121.0 if field == "volume" else rows[-2][field] + (-0.1 if field == "low" else 0.1)
    with pytest.raises(host.HostTestBlocked, match="STATE_CHANGED_OVERLAP"):
        host.process_live_window(probe, rows, head=HEAD, observed_at=now, prior=prior)


def test_new_true_close_enters_only_after_strict_overlap_reconciliation() -> None:
    prior, _ = evidence(breakout=False, age_seconds=0)
    probe, rows, now = live_fixture(
        END + timedelta(minutes=5),
        breakout=False,
        age_seconds=0,
    )
    payload = host.process_live_window(probe, rows, head=HEAD, observed_at=now, prior=prior)
    assert payload["recovery_state"] == "RESUME_ANCHOR_RECONCILED"
    assert len(payload["decisions"]) == 1
    assert payload["decisions"][0]["close_time"] == (END + timedelta(minutes=5)).isoformat()
    assert payload["checkpoint"]["order_execution_enabled"] is False


def test_legacy_state_blocks_before_network_and_is_preserved(tmp_path, monkeypatch, capsys):
    prior, _ = legacy_evidence()
    path = tmp_path / "evidence.json"
    host.atomic_write_json(path, prior)
    before = path.read_bytes()
    monkeypatch.setattr(host, "check_code", lambda _: HEAD)
    monkeypatch.setattr(host.platform, "system", lambda: "Windows")
    monkeypatch.setattr(host, "collect_probe_with_candles", lambda **_: pytest.fail("network called"))
    monkeypatch.setattr(host.sys, "argv", ["test", "--expected-head", HEAD, "--credentials-file", "external.env",
                                         "--state-dir", str(tmp_path)])
    assert host.main() == 2
    assert json.loads(capsys.readouterr().out)["error_code"] == "STATE_FINALIZATION_CONTRACT_MIGRATION_REQUIRED"
    assert path.read_bytes() == before


def test_auth_401_is_one_call_without_retry_or_provider_text(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(host, "require_verified_live_provider_contract", lambda: None)
    calls = []
    def failed_login(**kwargs):
        calls.append(kwargs)
        raise host.IgReadOnlyError("IG read-only session login failed: HTTP 401 (SYNTHETIC_SECRET_SENTINEL)")
    monkeypatch.setattr(host, "check_code", lambda _: HEAD)
    monkeypatch.setattr(host.platform, "system", lambda: "Windows")
    monkeypatch.setattr(host, "collect_probe_with_candles", failed_login)
    monkeypatch.setattr(host.sys, "argv", ["test", "--expected-head", HEAD, "--credentials-file", "external.env",
                                         "--state-dir", str(tmp_path)])
    assert host.main() == 2
    output = capsys.readouterr().out
    assert json.loads(output)["error_code"] == "IG_AUTHENTICATION_FAILED_NO_RETRY"
    assert "SYNTHETIC_SECRET_SENTINEL" not in output
    assert len(calls) == 1
    assert not (tmp_path / "evidence.json").exists()


def test_verified_provider_contract_gate_has_success_path() -> None:
    assert host.require_verified_live_provider_contract() is None


def test_provider_truth_gate_blocks_contract_drift(monkeypatch) -> None:
    monkeypatch.setattr(host, "TIMESTAMP_CONTRACT", "LEGACY_INTERVAL_END")
    with pytest.raises(host.HostTestBlocked, match="DATA_IG_M5_PROVIDER_CONTRACT_UNVERIFIED"):
        host.require_verified_live_provider_contract()


def test_future_close_decision_cannot_be_inserted_into_evidence() -> None:
    payload, now = evidence(breakout=False, age_seconds=0)
    injected = deepcopy(payload["decisions"][-1])
    injected["close_time"] = (END + timedelta(minutes=5)).isoformat()
    payload["decisions"].insert(0, injected)
    rehash(payload)
    with pytest.raises(host.HostTestBlocked, match="RUNTIME_UNFINALIZED_DECISION"):
        host.validate_evidence(payload, head=HEAD, now=now)
