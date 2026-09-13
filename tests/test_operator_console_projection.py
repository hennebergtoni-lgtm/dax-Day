"""Offline canonical composition tests, never real host/broker evidence."""
from copy import deepcopy
from datetime import timedelta

import pytest

from daxlab.runtime.candidate_shadow_host_cycle import run_cand001_shadow_host_cycle
from daxlab.runtime.mt5_shadow_supervisor import process_mt5_shadow_cycle
from daxlab.runtime.mt5_windows_bundle import parse_windows_mt5_bundle
from daxlab.runtime.operator_snapshot import (
    build_operator_console_projection,
    parse_operator_snapshot_payload,
)
from test_candidate_shadow_host_cycle import _bars
from test_mt5_windows_bundle import _bundle, _seal


def console_sources():
    raw = _bundle(demo_context=True)
    bars = _bars()
    observed = bars[-1].open_time + timedelta(minutes=5, seconds=1)
    raw["host_probe"].update(observed_at=observed.isoformat(), broker_timezone="Europe/Berlin")
    raw["closed_m5_feed"].update(
        observed_at=observed.isoformat(), broker_timezone="Europe/Berlin",
        timestamp_interpretation="EXPLICIT_BROKER_WALL_CLOCK",
        bars=[{
            "open_time": b.open_time.isoformat(), "open": b.open,
            "high": b.high, "low": b.low, "close": b.close,
        } for b in bars],
    )
    raw.pop("sha256")
    raw = _seal(raw)
    cycle = run_cand001_shadow_host_cycle(parse_windows_mt5_bundle(raw), single_instance_lock_held=True)
    snapshot = cycle.latest_operator_snapshot.as_dict()
    hb = process_mt5_shadow_cycle(raw, single_instance_lock_held=True, observed_at=observed).heartbeat
    return raw, snapshot, hb, observed, cycle


def project(raw, snapshot, hb, now):
    return build_operator_console_projection(
        bundle_payload=raw, snapshot_payload=snapshot, heartbeat_payload=hb, queried_at=now,
    )


def test_original_v3_parser_preserves_exact_valid_snapshot_digest_and_bytes():
    _, snapshot, _, _, _ = console_sources()
    restored = parse_operator_snapshot_payload(snapshot)
    assert restored.as_dict() == snapshot
    assert restored.snapshot_fingerprint == snapshot["snapshot_fingerprint"]


def test_console_does_not_equate_strategy_or_local_shadow_green_with_broker_readiness():
    raw, snapshot, hb, now, _ = console_sources()
    view = project(raw, snapshot, hb, now)
    assert view["system"]["FEED"]["state"] == "GREEN"
    assert view["system"]["SNAPSHOT AGE"]["state"] == "UNKNOWN"
    assert view["system"]["HOST"]["state"] == "UNKNOWN"
    assert view["system"]["EXECUTION"] == {"state": "BLOCKED", "value": "NONE / disabled"}
    assert view["account_context"]["account_mode"] == "DEMO"
    assert view["reconciliation"]["account_inventory_complete"] is False
    assert view["recovery"]["candidate_reconciliation_scope"] == "LOCAL_SHADOW_ONLY"
    assert view["execution_capability"] == "NONE"
    assert view["order_execution_enabled"] is False
    assert view["risk_loss_exposure"]["values"] is None
    assert view["build_identity"]["runtime_commit"] is None


def test_fetch_time_cannot_renew_source_age_and_reuses_source_feed_limit():
    raw, snapshot, hb, now, _ = console_sources()
    later = now + timedelta(seconds=raw["closed_m5_feed"]["max_age_seconds"])
    view = project(raw, snapshot, hb, later)
    assert view["system"]["FEED"]["state"] == "STALE"
    assert view["timestamps"]["snapshot_generated_at"] == snapshot["generated_at"]
    assert view["timestamps"]["snapshot_measured_bar_age_seconds"] == snapshot["runtime"]["freshness_seconds"]
    assert view["timestamps"]["current_feed_age_seconds"] > view["timestamps"]["source_max_feed_age_seconds"]
    assert view["timestamps"]["broker_tick_observed_at"] is None
    assert "MARKET_DATA_STALE_AT_QUERY" in view["blockers"]


@pytest.mark.parametrize("section,field", [("host_probe", "terminal_connected"), ("host_probe", "engine_loop_healthy"), ("host_probe", "clock_ok")])
def test_alive_web_or_candidate_cannot_hide_down_host_mt5_or_clock(section, field):
    raw, snapshot, hb, now, _ = console_sources()
    raw[section][field] = False
    raw.pop("sha256")
    raw = _seal(raw)
    hb["bundle_sha256"] = raw["sha256"]
    view = project(raw, snapshot, hb, now)
    assert view["system"]["FEED"]["state"] == "BLOCKED"
    assert view["state"] == "BLOCKED"


def test_failed_supervisor_cycle_overrides_old_candidate_green():
    raw, snapshot, hb, now, _ = console_sources()
    hb.update(status="ERROR", blockers=["PROBE_OR_CYCLE_FAILED"])
    view = project(raw, snapshot, hb, now)
    assert view["system"]["FEED"]["state"] == "BLOCKED"
    assert "PROBE_OR_CYCLE_FAILED" in view["blockers"]


def test_heartbeat_from_other_bundle_fails_closed():
    raw, snapshot, hb, now, _ = console_sources()
    hb["bundle_sha256"] = "f" * 64
    view = project(raw, snapshot, hb, now)
    assert "HEARTBEAT_BUNDLE_CYCLE_MISMATCH" in view["blockers"]
    assert view["system"]["FEED"]["state"] == "BLOCKED"


def test_candidate_behind_feed_is_stale_without_inventing_seconds_threshold():
    raw, _, hb, now, _ = console_sources()
    earlier = deepcopy(raw)
    earlier["closed_m5_feed"]["bars"].pop()
    earlier.pop("sha256")
    earlier = _seal(earlier)
    snapshot = run_cand001_shadow_host_cycle(parse_windows_mt5_bundle(earlier), single_instance_lock_held=True).latest_operator_snapshot.as_dict()
    view = project(raw, snapshot, hb, now)
    assert view["system"]["SNAPSHOT AGE"]["state"] == "STALE"
    assert "CANDIDATE_BEHIND_OR_DIFFERENT_FEED" in view["blockers"]


def test_missing_sources_never_green():
    _, _, _, now, _ = console_sources()
    view = project(None, None, None, now)
    assert all(t["state"] != "GREEN" for t in view["system"].values())
    assert "CANDIDATE_SNAPSHOT_MISSING" in view["blockers"]


@pytest.mark.parametrize("source", ["candidate", "bundle", "heartbeat"])
def test_credential_payload_in_any_source_rejects(source):
    raw, snapshot, hb, now, _ = console_sources()
    {"candidate": snapshot, "bundle": raw, "heartbeat": hb}[source]["dsn"] = "secret"
    with pytest.raises(ValueError):
        project(raw, snapshot, hb, now)


def test_original_digest_tampering_rejects_instead_of_rendering_false_evidence():
    raw, snapshot, hb, now, _ = console_sources()
    snapshot["trade_plan"]["entry"] = 999.0
    with pytest.raises(ValueError, match="fingerprint"):
        project(raw, snapshot, hb, now)


def test_future_observation_is_rejected():
    raw, snapshot, hb, now, _ = console_sources()
    with pytest.raises(ValueError, match="future"):
        project(raw, snapshot, hb, now - timedelta(seconds=1))


def test_source_feed_threshold_equality_is_allowed_then_stale():
    raw, snapshot, hb, now, _ = console_sources()
    boundary = now + timedelta(seconds=raw["closed_m5_feed"]["max_age_seconds"] - 1)
    assert project(raw, snapshot, hb, boundary)["system"]["FEED"]["state"] == "GREEN"
    assert project(raw, snapshot, hb, boundary + timedelta(seconds=1))["system"]["FEED"]["state"] == "STALE"


@pytest.mark.parametrize("mutation", ["timezone", "observation_time", "symbol"])
def test_rehashed_cross_source_mismatches_do_not_produce_green_feed(mutation):
    raw, snapshot, hb, now, _ = console_sources()
    if mutation == "timezone":
        raw["host_probe"]["broker_timezone"] = "UTC"
    elif mutation == "observation_time":
        raw["host_probe"]["observed_at"] = (now - timedelta(seconds=1)).isoformat()
    else:
        hb["symbol"] = "OTHER"
    raw.pop("sha256")
    raw = _seal(raw)
    hb["bundle_sha256"] = raw["sha256"]
    view = project(raw, snapshot, hb, now)
    assert view["system"]["FEED"]["state"] == "BLOCKED"
