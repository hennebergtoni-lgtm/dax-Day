"""Deterministic crash/restart recovery drill for MT5 read-only SHADOW.

The drill compares an uninterrupted run with a persisted checkpoint followed by
restart against an overlapping feed. It never enables order execution.
"""
from datetime import datetime, timedelta, timezone
import hashlib
import json

from daxlab.runtime.mt5_shadow_integration import (
    build_mt5_shadow_resume_state,
    evaluate_shadow_soak_from_bundle,
    mt5_shadow_resume_payload,
    parse_mt5_shadow_resume_payload,
)
from daxlab.runtime.mt5_windows_bundle import parse_windows_mt5_bundle
from daxlab.runtime.prospective_gate import ProspectiveAuthorization


def _seal(payload: dict) -> dict:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    value = dict(payload)
    value["sha256"] = hashlib.sha256(canonical.encode()).hexdigest()
    return value


def _bundle_payload(bar_count: int) -> dict:
    start = datetime(2026, 9, 9, 6, 0, tzinfo=timezone.utc)
    bars = []
    for index in range(bar_count):
        t = start + timedelta(minutes=5 * index)
        bars.append(
            {
                "open_time": t.isoformat(),
                "open": 25000.0 + index,
                "high": 25002.0 + index,
                "low": 24999.0 + index,
                "close": 25001.0 + index,
            }
        )
    observed = start + timedelta(minutes=5 * bar_count + 1)
    return _seal(
        {
            "schema": "DAXLAB_MT5_WINDOWS_BUNDLE_V1",
            "symbol_resolution_state": "AUTO_EXACT_ALIAS_DATA_ONLY",
            "host_probe": {
                "observed_at": observed.isoformat(),
                "terminal_connected": True,
                "account_connected": True,
                "account_trade_allowed": False,
                "order_execution_enabled": False,
                "engine_loop_healthy": True,
                "clock_ok": True,
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
                "bars": bars,
            },
            "notes": ["READ_ONLY", "BAR_0_EXCLUDED", "NO_CREDENTIALS", "NO_ORDER_API"],
        }
    )


def _auth() -> ProspectiveAuthorization:
    return ProspectiveAuthorization(
        gate_id="STEP_91_USER_AUTHORIZATION",
        shadow_authorized=True,
        paper_authorized=False,
        live_authorized=False,
    )


def _run(payload: dict, *, resume_state=None):
    bundle = parse_windows_mt5_bundle(payload)
    gate, result, status = evaluate_shadow_soak_from_bundle(
        bundle,
        authorization=_auth(),
        single_instance_lock_held=True,
        resume_state=resume_state,
    )
    assert gate.allowed is True
    assert result is not None
    assert result.execution_capability == "NONE"
    assert result.order_execution_enabled is False
    assert status.symbol == "DE40"
    return result, status


def test_persisted_restart_with_overlap_matches_uninterrupted_final_checkpoint() -> None:
    full_payload = _bundle_payload(6)
    uninterrupted, _ = _run(full_payload)

    before_crash, status = _run(_bundle_payload(3))
    assert status.symbol is not None
    persisted = mt5_shadow_resume_payload(
        build_mt5_shadow_resume_state(
            symbol=status.symbol,
            checkpoint=before_crash.checkpoint,
        )
    )

    # Simulate process death: only serialized state crosses the restart boundary.
    restored = parse_mt5_shadow_resume_payload(
        json.loads(json.dumps(persisted, sort_keys=True))
    )
    resumed, _ = _run(full_payload, resume_state=restored)

    assert before_crash.processed == 3
    assert resumed.processed == uninterrupted.processed == 6
    assert len(resumed.decisions) == 3
    assert resumed.duplicates_suppressed == 0
    assert resumed.checkpoint == uninterrupted.checkpoint
    assert resumed.checkpoint.payload_sha256 == uninterrupted.checkpoint.payload_sha256
    assert resumed.checkpoint.last_bar_fingerprint == uninterrupted.checkpoint.last_bar_fingerprint
    assert resumed.checkpoint.seen_bar_fingerprints == uninterrupted.checkpoint.seen_bar_fingerprints
    assert resumed.checkpoint.seen_decision_ids == uninterrupted.checkpoint.seen_decision_ids


def test_restart_with_identical_feed_is_idempotent() -> None:
    payload = _bundle_payload(4)
    first, status = _run(payload)
    assert status.symbol is not None
    persisted = mt5_shadow_resume_payload(
        build_mt5_shadow_resume_state(
            symbol=status.symbol,
            checkpoint=first.checkpoint,
        )
    )
    restored = parse_mt5_shadow_resume_payload(persisted)
    resumed, _ = _run(payload, resume_state=restored)

    assert resumed.processed == first.processed == 4
    assert resumed.decisions == ()
    assert resumed.duplicates_suppressed == 0
    assert resumed.checkpoint == first.checkpoint
