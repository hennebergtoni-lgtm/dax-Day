"""Synthetic diagnostic regressions; never broker evidence."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import importlib.util
import json
from pathlib import Path

import pytest

from test_ig_demo_readonly_probe import price_row

SPEC = importlib.util.spec_from_file_location(
    "ig_raw_diagnostic_test", Path(__file__).resolve().parents[1] / "scripts/ig_raw_m5_timestamp_diagnostic.py",
)
assert SPEC and SPEC.loader
raw = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(raw)
HEAD = "a" * 40
T = datetime(2026, 9, 14, 12, 45, tzinfo=timezone.utc)


def evidence(at=T + timedelta(seconds=47)):
    rows = [price_row(T - timedelta(minutes=5)), price_row(T)]
    for row in rows:
        row["lastTradedVolume"] = 29
    return raw.snapshot(rows, head=HEAD, requested=at, observed=at + timedelta(seconds=1))


def resnapshot(payload):
    return raw.snapshot([row["raw"] for row in payload["rows"]], head=payload["exact_code_head"],
                        requested=raw.utc(payload["request_started_at_utc"]),
                        observed=raw.utc(payload["response_observed_at_utc"]))


def test_raw_numeric_quotes_preserved_extra_secrets_not_projected():
    row = price_row(T)
    row.update({"accountId": "SECRET_ACCOUNT", "CST": "SECRET_TOKEN", "unexpected": "SECRET_TEXT"})
    row["openPrice"]["unexpected"] = "SECRET_QUOTE"
    projected = raw.project_row(row)
    assert "SECRET" not in json.dumps(projected)
    assert projected["raw"]["openPrice"]["bid"] == row["openPrice"]["bid"]
    assert projected["raw"]["snapshotTimeUTC"] == row["snapshotTimeUTC"]
    assert projected["normalized_current_adapter_hypothesis"]["close_time"] == T.isoformat()
    assert projected["interval_start_hypothesis"]["close_time"] == (T + timedelta(minutes=5)).isoformat()
    assert projected["normalized_current_adapter_hypothesis"]["verification_state"] == "UNVERIFIED"


@pytest.mark.parametrize("value", ["CST=SECRET", True, float("nan"), float("inf"), {}])
def test_price_string_and_nonfinite_data_cannot_escape(value):
    row = price_row(T)
    row["closePrice"]["bid"] = value
    with pytest.raises(raw.HostTestBlocked, match="RAW_NON_NUMERIC_FIELD"):
        raw.project_row(row)


@pytest.mark.parametrize("timestamp", ["CST=SECRET", "2026-09-14T12:45:00+01:00", "2026-09-14T12:46:00"])
def test_timestamp_invalid_or_local_is_rejected(timestamp):
    row = price_row(T)
    row["snapshotTimeUTC"] = timestamp
    with pytest.raises((raw.HostTestBlocked, ValueError)):
        raw.project_row(row)


def test_raw_revisions_across_boundary_do_not_prove_semantics():
    a = evidence()
    b = evidence(T + timedelta(minutes=5, seconds=47))
    b["rows"][-1]["raw"]["lastTradedVolume"] += 100
    b["rows"][0]["raw"]["closePrice"]["bid"] += 1
    b = resnapshot(b)
    result = raw.compare(a, b)
    assert result["changed_raw_timestamp_count"] == 2
    assert result["comparisons"][-1]["observed_across_next_m5_boundary"] is True
    assert result["timestamp_semantics"] == result["historical_closed_bar_revision"] == "UNKNOWN"
    raw.validate_snapshot(a)
    raw.validate_snapshot(b)


def test_three_rolling_snapshots_cover_two_successive_timestamps():
    captures = []
    for n in range(3):
        tail = T + timedelta(minutes=5*n)
        captures.append(raw.snapshot(
            [price_row(tail - timedelta(minutes=5*i)) for i in reversed(range(3))],
            head=HEAD, requested=tail + timedelta(seconds=47),
            observed=tail + timedelta(seconds=48),
        ))
    ab, bc = raw.compare(captures[0], captures[1]), raw.compare(captures[1], captures[2])
    covered = [row["snapshotTimeUTC"] for result in (ab, bc) for row in result["comparisons"]
               if row["observed_across_next_m5_boundary"]]
    assert covered == [price_row(T)["snapshotTimeUTC"],
                       price_row(T + timedelta(minutes=5))["snapshotTimeUTC"]]


def test_live_linux_blocks_before_collect_or_file_creation(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(raw, "check_code", lambda _: HEAD)
    monkeypatch.setattr(raw.platform, "system", lambda: "Linux")
    monkeypatch.setattr(raw, "collect", lambda *a, **kw: pytest.fail("No live read on Linux"))
    output = tmp_path / "a.json"
    assert raw.main(["--expected-head", HEAD, "--credentials-file", "not-read.env",
                     "--output", str(output)]) == 2
    assert not output.exists()
    assert "GOVERNANCE_WINDOWS_HOST_REQUIRED" in capsys.readouterr().out


def test_offline_compare_uses_no_credentials_or_provider_calls(tmp_path, monkeypatch):
    monkeypatch.setattr(raw, "check_code", lambda _: HEAD)
    monkeypatch.setattr(raw, "collect", lambda *a, **kw: pytest.fail("Offline mode must not login"))
    a, b, output = (tmp_path / name for name in ("a.json", "b.json", "ab.json"))
    a.write_text(json.dumps(evidence()))
    b.write_text(json.dumps(evidence(T + timedelta(minutes=5, seconds=47))))
    assert raw.main(["--expected-head", HEAD, "--compare", str(a), str(b),
                     "--output", str(output)]) == 0
    result = json.loads(output.read_text())
    assert result["execution_capability"] == "NONE"
    assert result["order_execution_enabled"] is False


def test_unchanged_raw_is_not_finality_evidence():
    result = raw.compare(evidence(), evidence(T + timedelta(minutes=5, seconds=47)))
    assert result["changed_raw_timestamp_count"] == 0
    assert result["unchanged_observation_is_not_finality_proof"] is True


def test_tampered_normalization_rehashed_still_rejected():
    payload = evidence()
    payload["rows"][-1]["normalized_current_adapter_hypothesis"]["close_time"] = T.replace(hour=13).isoformat()
    payload.pop("fingerprint")
    payload["fingerprint"] = raw._fingerprint(payload)
    with pytest.raises(raw.HostTestBlocked, match="RAW_EVIDENCE_CONTRACT_OR_HASH_MISMATCH"):
        raw.validate_snapshot(payload)


def test_unsafe_execution_rehashed_still_rejected():
    payload = evidence()
    payload["order_execution_enabled"] = True
    payload.pop("fingerprint")
    payload["fingerprint"] = raw._fingerprint(payload)
    with pytest.raises(raw.HostTestBlocked, match="RAW_EVIDENCE_CONTRACT_OR_HASH_MISMATCH"):
        raw.validate_snapshot(payload)


def test_reverse_or_replayed_observations_block():
    with pytest.raises(raw.HostTestBlocked, match="RAW_OBSERVATIONS_NOT_SEQUENTIAL"):
        raw.compare(evidence(), evidence())


def test_output_exists_blocks_before_credentials_or_network(tmp_path, monkeypatch, capsys):
    output = tmp_path / "a.json"
    output.write_text("PRESERVE")
    monkeypatch.setattr(raw, "check_code", lambda _: HEAD)
    monkeypatch.setattr(raw.platform, "system", lambda: "Windows")
    def unexpected(*args, **kwargs):
        pytest.fail("Must not read credentials or start another session")
    monkeypatch.setattr(raw, "collect", unexpected)
    assert raw.main(["--expected-head", HEAD, "--credentials-file", "not-read.env",
                     "--output", str(output)]) == 2
    assert output.read_text() == "PRESERVE"
    assert "RAW_OUTPUT_ALREADY_EXISTS" in capsys.readouterr().out


def test_one_login_one_prices_one_cleanup_no_inventory_or_dealing(tmp_path):
    creds = tmp_path / "demo.env"
    creds.write_text("IG_USERNAME=user\nIG_PASSWORD=SECRET_PASSWORD\nIG_API_KEY=SECRET_KEY\n")
    calls = []
    class Client:
        authenticated = True
        execution_capability = "NONE"
        order_execution_enabled = False
        def __init__(self, _): pass
        def login(self): calls.append("login")
        def m5_prices(self, epic, *, max_bars):
            assert epic == raw.DEFAULT_EPIC and max_bars == 40
            calls.append("prices")
            return {"prices": [price_row(T - timedelta(minutes=5)), price_row(T)], "CST": "SECRET"}
        def logout(self): calls.append("logout")
    times = iter([T + timedelta(seconds=47), T + timedelta(seconds=48)])
    payload = raw.collect(creds, head=HEAD, client_factory=Client, clock=lambda: next(times))
    assert calls == ["login", "prices", "logout"]
    assert "SECRET" not in json.dumps(payload)
    assert payload["candidate_processing_performed"] is False
    raw.validate_snapshot(payload)


def test_http401_fixed_code_no_retry_provider_text_or_output(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(raw, "check_code", lambda _: HEAD)
    monkeypatch.setattr(raw.platform, "system", lambda: "Windows")
    calls = []
    def failed(*args, **kwargs):
        calls.append(1)
        raise raw.IgReadOnlyError("HTTP 401 SECRET_PROVIDER_TEXT")
    monkeypatch.setattr(raw, "collect", failed)
    output = tmp_path / "auth.json"
    assert raw.main(["--expected-head", HEAD, "--credentials-file", "not-read.env",
                     "--output", str(output)]) == 2
    assert calls == [1] and not output.exists()
    stdout = capsys.readouterr().out
    assert "IG_AUTHENTICATION_FAILED_NO_RETRY" in stdout and "SECRET" not in stdout


def test_missing_volume_distinct_from_null():
    a = evidence()
    b = evidence(T + timedelta(minutes=5, seconds=47))
    del a["rows"][-1]["raw"]["lastTradedVolume"]
    b["rows"][-1]["raw"]["lastTradedVolume"] = None
    a, b = resnapshot(a), resnapshot(b)
    result = raw.compare(a, b)
    changed = result["comparisons"][-1]["changed_fields"]["lastTradedVolume"]
    assert changed["before_present"] is False and changed["after_present"] is True


def test_unknown_evidence_provider_keys_are_not_accepted_even_after_rehash():
    payload = deepcopy(evidence())
    payload["unexpected"] = "provider narrative"
    payload.pop("fingerprint")
    payload["fingerprint"] = raw._fingerprint(payload)
    with pytest.raises(raw.HostTestBlocked, match="RAW_EVIDENCE_CONTRACT_OR_HASH_MISMATCH"):
        raw.validate_snapshot(payload)


def test_row_index_hash_and_unknown_states_are_explicit_and_deterministic():
    payload = evidence()
    assert payload == evidence()
    assert [row["raw_row_index"] for row in payload["rows"]] == [0, 1]
    assert payload["provider_semantics_classification"] == "OTHER_UNKNOWN"
    for row in payload["rows"]:
        assert row["normalized_event_time"] is row["normalized_close_time"] is None
        assert row["closed_state"] == row["provider_finalization_state"] == "UNKNOWN"
        assert row["is_closed"] is None and row["candidate_finalized"] is False
        assert row["freshness_seconds"] is None
        unsigned = {key: value for key, value in row.items() if key != "fingerprint"}
        assert row["fingerprint"] == raw._fingerprint(unsigned)


@pytest.mark.parametrize("seconds,closed", [(0, False), (47, False), (299.999999, False), (300, True)])
def test_start_hypothesis_running_bar_and_exact_closure_boundary(seconds, closed):
    payload = evidence(T + timedelta(seconds=seconds))
    row = payload["rows"][-1]
    start = row["interval_start_hypothesis"]
    assert start["event_time"] == T.isoformat()
    assert start["close_time"] == (T + timedelta(minutes=5)).isoformat()
    assert start["is_closed"] is closed
    assert start["freshness_seconds"] == pytest.approx(seconds + 1 - 300)
    assert start["candidate_finalized"] is False
    assert row["candidate_finalized"] is False


def test_response_crossing_boundary_cannot_promote_start_hypothesis_closure():
    payload = raw.snapshot([price_row(T - timedelta(minutes=5)), price_row(T)], head=HEAD,
                           requested=T + timedelta(seconds=299.9), observed=T + timedelta(seconds=301))
    row = payload["rows"][-1]
    assert row["interval_start_hypothesis"]["is_closed"] is False
    assert row["interval_start_hypothesis"]["freshness_seconds"] == 1
    assert row["is_closed"] is None and row["candidate_finalized"] is False


@pytest.mark.parametrize("age,state", [(600, "FRESH"), (600.000001, "STALE"), (601, "STALE")])
def test_hypothesis_freshness_uses_own_close_and_unchanged_600s_limit(age, state):
    requested = T + timedelta(minutes=5, seconds=age)
    payload = raw.snapshot([price_row(T - timedelta(minutes=5)), price_row(T)], head=HEAD,
                           requested=requested, observed=requested)
    row = payload["rows"][-1]
    assert payload["freshness_max_age_seconds"] == 600
    assert row["interval_start_hypothesis"]["freshness_seconds"] == pytest.approx(age)
    assert row["interval_start_hypothesis"]["freshness_state"] == state
    assert row["normalized_current_adapter_hypothesis"]["freshness_seconds"] == pytest.approx(age + 300)
    assert row["freshness_state"] == "UNKNOWN" and row["candidate_finalized"] is False


@pytest.mark.parametrize("field,expected", [("highPrice", "OHLC_ONLY"),
                                          ("lastTradedVolume", "VOLUME_ONLY")])
def test_mutation_type_leaf_diff_times_ages_and_history_depth(field, expected):
    a, b = evidence(), evidence(T + timedelta(minutes=5, seconds=47))
    if field == "highPrice":
        b["rows"][0]["raw"][field]["ask"] += 2
    else:
        b["rows"][0]["raw"][field] += 2
    b = resnapshot(b)
    item = raw.compare(a, b)["comparisons"][0]
    assert item["observed_mutation_type"] == expected
    changed = [diff for diff in item["field_diffs"] if diff["changed"]]
    assert [diff["field"] for diff in changed] == ["highPrice.ask" if field == "highPrice" else field]
    assert len(item["field_diffs"]) == 14
    assert item["first_seen_at"] == a["response_observed_at_utc"]
    assert item["later_seen_at"] == b["response_observed_at_utc"]
    assert item["age_at_first_observation_seconds"] == 348
    assert item["age_at_later_observation_seconds"] == 648
    assert item["before_bars_back_from_raw_tail"] == item["after_bars_back_from_raw_tail"] == 1


def test_mixed_mutation_does_not_classify_end_with_historical_revisions():
    a, b = evidence(), evidence(T + timedelta(minutes=5, seconds=47))
    b["rows"][-1]["raw"]["closePrice"]["ask"] += 1
    b["rows"][-1]["raw"]["lastTradedVolume"] += 1
    result = raw.compare(a, resnapshot(b))
    assert result["comparisons"][-1]["observed_mutation_type"] == "MIXED"
    assert result["provider_semantics_classification"] == "OTHER_UNKNOWN"
    assert result["historical_closed_bar_revision"] == "UNKNOWN"


def test_old_raw_schema_blocks_without_migration_or_mutation():
    payload = evidence()
    payload["schema"] = "DAX_IG_RAW_M5_TIMESTAMP_OBSERVATION_V1"
    original = deepcopy(payload)
    with pytest.raises(raw.HostTestBlocked, match="RAW_EVIDENCE_SCHEMA_MISMATCH"):
        raw.validate_snapshot(payload)
    assert payload == original


def test_tampered_row_index_or_finality_with_rehashed_outer_snapshot_blocks():
    for field, value in (("raw_row_index", 99), ("candidate_finalized", True), ("is_closed", True)):
        payload = evidence()
        payload["rows"][-1][field] = value
        row = payload["rows"][-1]
        row.pop("fingerprint")
        row["fingerprint"] = raw._fingerprint(row)
        payload.pop("fingerprint")
        payload["fingerprint"] = raw._fingerprint(payload)
        with pytest.raises(raw.HostTestBlocked, match="RAW_EVIDENCE_CONTRACT_OR_HASH_MISMATCH"):
            raw.validate_snapshot(payload)
