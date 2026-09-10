from datetime import datetime, timedelta, timezone
import hashlib
import json

from daxlab.runtime.mt5_shadow_integration import (
    build_mt5_shadow_resume_state,
    evaluate_shadow_soak_from_bundle,
    host_readiness_summary,
)
from daxlab.runtime.mt5_windows_bundle import parse_windows_mt5_bundle
from daxlab.runtime.prospective_gate import ProspectiveAuthorization


def _seal(payload: dict) -> dict:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    value = dict(payload)
    value["sha256"] = hashlib.sha256(canonical.encode()).hexdigest()
    return value


def _bundle(bar_count: int):
    first_open = datetime(2026, 9, 10, 7, 30, tzinfo=timezone.utc)
    bars = []
    for index in range(bar_count):
        t = first_open + timedelta(minutes=5 * index)
        base = 25000.0 + index
        bars.append(
            {
                "open_time": t.isoformat(),
                "open": base,
                "high": base + 2.0,
                "low": base - 1.0,
                "close": base + 1.0,
            }
        )
    observed = first_open + timedelta(minutes=5 * bar_count)
    return parse_windows_mt5_bundle(
        _seal(
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
    )


def _auth() -> ProspectiveAuthorization:
    return ProspectiveAuthorization(
        gate_id="STEP_91_USER_AUTHORIZATION",
        shadow_authorized=True,
        paper_authorized=False,
        live_authorized=False,
    )


def test_fresh_start_telemetry_exposes_full_feed_as_catchup() -> None:
    gate, result, status = evaluate_shadow_soak_from_bundle(
        _bundle(3),
        authorization=_auth(),
        single_instance_lock_held=True,
    )
    assert gate.allowed
    assert result is not None
    assert status.resume_telemetry is not None
    telemetry = status.resume_telemetry
    assert telemetry.fresh_start is True
    assert telemetry.anchor_found is False
    assert telemetry.anchor_index is None
    assert telemetry.feed_bar_count == 3
    assert telemetry.catchup_bar_count == 3
    assert telemetry.prior_anchor_filtered_bar_count == 0
    assert result.duplicates_suppressed == 0
    assert result.execution_capability == "NONE"
    assert result.order_execution_enabled is False


def test_resume_telemetry_separates_filtered_history_from_catchup() -> None:
    _, first, first_status = evaluate_shadow_soak_from_bundle(
        _bundle(2),
        authorization=_auth(),
        single_instance_lock_held=True,
    )
    assert first is not None and first_status.symbol == "DE40"
    resume_state = build_mt5_shadow_resume_state(
        symbol="DE40",
        checkpoint=first.checkpoint,
    )

    _, resumed, status = evaluate_shadow_soak_from_bundle(
        _bundle(5),
        authorization=_auth(),
        single_instance_lock_held=True,
        resume_state=resume_state,
    )
    assert resumed is not None
    assert status.resume_telemetry is not None
    telemetry = status.resume_telemetry
    assert telemetry.fresh_start is False
    assert telemetry.anchor_found is True
    assert telemetry.anchor_index == 1
    assert telemetry.feed_bar_count == 5
    assert telemetry.catchup_bar_count == 3
    assert telemetry.prior_anchor_filtered_bar_count == 2
    assert len(resumed.decisions) == 3
    assert resumed.duplicates_suppressed == 0
    assert resumed.execution_capability == "NONE"
    assert resumed.order_execution_enabled is False


def test_readiness_summary_exposes_resume_telemetry_without_execution_capability() -> None:
    _, result, status = evaluate_shadow_soak_from_bundle(
        _bundle(3),
        authorization=_auth(),
        single_instance_lock_held=True,
    )
    assert result is not None
    summary = host_readiness_summary(status)
    assert summary["order_execution_enabled"] is False
    assert summary["resume_telemetry"] == {
        "fresh_start": True,
        "anchor_found": False,
        "anchor_index": None,
        "feed_bar_count": 3,
        "catchup_bar_count": 3,
        "prior_anchor_filtered_bar_count": 0,
    }
