from datetime import datetime, timedelta, timezone
import hashlib
import json

import pytest

from daxlab.runtime.mt5_shadow_integration import mt5_shadow_resume_payload
from daxlab.runtime.mt5_shadow_supervisor import (
    load_mt5_resume_payload,
    process_mt5_shadow_cycle,
    shadow_authorization,
    supervisor_error_heartbeat,
    supervisor_stopped_heartbeat,
    with_history_archive_status,
)
from daxlab.runtime.shadow_soak import MT5_READONLY_EVIDENCE_STATE


def _seal(payload: dict) -> dict:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    sealed = dict(payload)
    sealed["sha256"] = hashlib.sha256(canonical.encode()).hexdigest()
    return sealed


def _bundle() -> dict:
    observed = datetime(2026, 9, 9, 19, 30, tzinfo=timezone.utc)
    latest = observed - timedelta(minutes=5)
    bars = []
    for offset in (10, 5, 0):
        t = latest - timedelta(minutes=offset)
        bars.append(
            {
                "open_time": t.isoformat(),
                "open": 25000.0 + offset,
                "high": 25003.0 + offset,
                "low": 24999.0 + offset,
                "close": 25001.0 + offset,
            }
        )
    return _seal(
        {
            "schema": "DAXLAB_MT5_WINDOWS_BUNDLE_V1",
            "symbol_resolution_state": "CONFIGURED_EXACT_DATA_ONLY",
            "host_probe": {
                "observed_at": observed.isoformat(),
                "terminal_connected": True,
                "account_connected": True,
                "account_trade_allowed": False,
                "order_execution_enabled": False,
                "engine_loop_healthy": True,
                "clock_ok": True,
                "broker_timezone": "Europe/Berlin",
                "symbols": [
                    {
                        "name": "DE40",
                        "digits": 2,
                        "point": 0.01,
                        "trade_mode": "DISABLED",
                        "contract_size": 1.0,
                        "volume_min": 0.1,
                        "volume_step": 0.1,
                    }
                ],
            },
            "closed_m5_feed": {
                "observed_at": observed.isoformat(),
                "requested_start_pos": 1,
                "max_age_seconds": 600.0,
                "broker_timezone": "Europe/Berlin",
                "timestamp_interpretation": "EXPLICIT_BROKER_WALL_CLOCK",
                "bars": bars,
            },
            "notes": ["READ_ONLY", "BAR_0_EXCLUDED", "NO_CREDENTIALS", "NO_ORDER_API"],
        }
    )


def _mutated_bundle() -> dict:
    bundle = _bundle()
    payload = dict(bundle)
    payload.pop("sha256")
    feed = dict(payload["closed_m5_feed"])
    bars = [dict(item) for item in feed["bars"]]
    bars[1]["close"] += 25.0
    bars[1]["high"] += 25.0
    feed["bars"] = bars
    payload["closed_m5_feed"] = feed
    return _seal(payload)


def test_supervisor_green_cycle_is_no_order_and_builds_resume() -> None:
    result = process_mt5_shadow_cycle(
        _bundle(),
        single_instance_lock_held=True,
        observed_at=datetime(2026, 9, 9, 19, 30, 1, tzinfo=timezone.utc),
    )
    assert result.heartbeat["status"] == "GREEN"
    assert result.heartbeat["processed_total"] == 3
    assert result.heartbeat["new_decisions"] == 3
    assert result.heartbeat["evidence_state"] == MT5_READONLY_EVIDENCE_STATE
    assert result.heartbeat["execution_capability"] == "NONE"
    assert result.heartbeat["order_execution_enabled"] is False
    assert result.heartbeat["cross_cycle_status"] == "NOT_AVAILABLE"
    assert result.resume_state is not None


def test_supervisor_resume_suppresses_seen_bars() -> None:
    first = process_mt5_shadow_cycle(_bundle(), single_instance_lock_held=True)
    assert first.resume_state is not None
    second = process_mt5_shadow_cycle(
        _bundle(),
        single_instance_lock_held=True,
        resume_state=first.resume_state,
    )
    assert second.heartbeat["status"] == "GREEN"
    assert second.heartbeat["new_decisions"] == 0
    assert second.heartbeat["duplicates_suppressed"] == 0
    assert second.resume_state is not None
    assert second.resume_state.checkpoint == first.resume_state.checkpoint


def test_cross_cycle_identical_snapshot_stays_green() -> None:
    first = process_mt5_shadow_cycle(_bundle(), single_instance_lock_held=True)
    assert first.resume_state is not None
    second = process_mt5_shadow_cycle(
        _bundle(),
        single_instance_lock_held=True,
        resume_state=first.resume_state,
        previous_bundle_payload=_bundle(),
    )
    assert second.heartbeat["status"] == "GREEN"
    assert second.heartbeat["cross_cycle_status"] == "GREEN"
    assert second.heartbeat["cross_cycle_overlapping_bars"] == 3
    assert second.heartbeat["cross_cycle_identical_overlaps"] == 3
    assert second.heartbeat["cross_cycle_mutated_overlaps"] == 0
    assert second.heartbeat["new_decisions"] == 0
    assert second.resume_state is not None


def test_cross_cycle_mutation_blocks_before_resume_advance() -> None:
    first = process_mt5_shadow_cycle(_bundle(), single_instance_lock_held=True)
    assert first.resume_state is not None
    blocked = process_mt5_shadow_cycle(
        _mutated_bundle(),
        single_instance_lock_held=True,
        resume_state=first.resume_state,
        previous_bundle_payload=_bundle(),
    )
    assert blocked.heartbeat["status"] == "BLOCKED"
    assert blocked.heartbeat["blockers"] == ["HISTORICAL_BAR_MUTATION"]
    assert blocked.heartbeat["cross_cycle_status"] == "BLOCKED"
    assert blocked.heartbeat["cross_cycle_mutated_overlaps"] == 1
    assert blocked.heartbeat["new_decisions"] == 0
    assert blocked.resume_state is None
    assert blocked.heartbeat["execution_capability"] == "NONE"
    assert blocked.heartbeat["order_execution_enabled"] is False


def test_history_archive_status_annotation_preserves_no_order() -> None:
    heartbeat = process_mt5_shadow_cycle(_bundle(), single_instance_lock_held=True).heartbeat
    ok = with_history_archive_status(heartbeat, archived=True)
    failed = with_history_archive_status(heartbeat, archived=False)
    assert ok["history_archive_status"] == "OK"
    assert failed["history_archive_status"] == "FAILED"
    for item in (ok, failed):
        assert item["execution_capability"] == "NONE"
        assert item["order_execution_enabled"] is False
        assert item["status"] == heartbeat["status"]


def test_history_archive_status_rejects_execution_capability() -> None:
    heartbeat = process_mt5_shadow_cycle(_bundle(), single_instance_lock_held=True).heartbeat
    heartbeat["execution_capability"] = "PAPER"
    with pytest.raises(ValueError, match="execution_capability"):
        with_history_archive_status(heartbeat, archived=True)


def test_supervisor_lost_lock_blocks_and_does_not_advance_resume() -> None:
    result = process_mt5_shadow_cycle(_bundle(), single_instance_lock_held=False)
    assert result.heartbeat["status"] == "BLOCKED"
    assert "SINGLE_INSTANCE_LOCK_NOT_HELD" in result.heartbeat["blockers"]
    assert result.resume_state is None
    assert result.heartbeat["order_execution_enabled"] is False


def test_resume_payload_round_trip_through_supervisor_loader() -> None:
    cycle = process_mt5_shadow_cycle(_bundle(), single_instance_lock_held=True)
    assert cycle.resume_state is not None
    payload = mt5_shadow_resume_payload(cycle.resume_state)
    assert load_mt5_resume_payload(payload) == cycle.resume_state


def test_resume_payload_tamper_fails_closed() -> None:
    cycle = process_mt5_shadow_cycle(_bundle(), single_instance_lock_held=True)
    assert cycle.resume_state is not None
    payload = mt5_shadow_resume_payload(cycle.resume_state)
    payload["payload_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="hash mismatch"):
        load_mt5_resume_payload(payload)


def test_shadow_authorization_does_not_authorize_paper_or_live() -> None:
    auth = shadow_authorization()
    assert auth.shadow_authorized is True
    assert auth.paper_authorized is False
    assert auth.live_authorized is False


def test_error_heartbeat_is_bounded_no_order() -> None:
    heartbeat = supervisor_error_heartbeat(
        error_code="MT5_PROBE_FAILED",
        observed_at=datetime(2026, 9, 9, 19, 31, tzinfo=timezone.utc),
    )
    assert heartbeat["status"] == "ERROR"
    assert heartbeat["blockers"] == ["MT5_PROBE_FAILED"]
    assert heartbeat["execution_capability"] == "NONE"
    assert heartbeat["order_execution_enabled"] is False
    serialized = json.dumps(heartbeat).lower()
    for forbidden in ("password", "login", "token", "secret", "account_id"):
        assert forbidden not in serialized


def test_error_heartbeat_rejects_unbounded_text() -> None:
    with pytest.raises(ValueError, match="must be an identifier"):
        supervisor_error_heartbeat(error_code="C:\\Users\\Name\\secret.txt")


def test_stopped_heartbeat_is_no_order_and_lock_released() -> None:
    heartbeat = supervisor_stopped_heartbeat()
    assert heartbeat["status"] == "STOPPED"
    assert heartbeat["single_instance_lock_held"] is False
    assert heartbeat["order_execution_enabled"] is False
