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


def _bundle(bar_count: int):
    observed = datetime(2026, 9, 9, 8, 0, tzinfo=timezone.utc)
    latest = observed - timedelta(minutes=5)
    first = latest - timedelta(minutes=5 * (bar_count - 1))
    bars = []
    for index in range(bar_count):
        t = first + timedelta(minutes=5 * index)
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
        gate_id="RECOVERY_EQUIVALENCE_DRILL",
        shadow_authorized=True,
        paper_authorized=False,
        live_authorized=False,
    )


def _run(bundle, resume_state=None):
    gate, result, status = evaluate_shadow_soak_from_bundle(
        bundle,
        authorization=_auth(),
        single_instance_lock_held=True,
        resume_state=resume_state,
    )
    assert gate.allowed
    assert result is not None
    assert status.symbol == "DE40"
    assert result.execution_capability == "NONE"
    assert result.order_execution_enabled is False
    assert all(item.action == "NO_ORDER" for item in result.decisions)
    return result


def _persist_round_trip(result):
    state = build_mt5_shadow_resume_state(symbol="DE40", checkpoint=result.checkpoint)
    payload = mt5_shadow_resume_payload(state)
    serialized = json.dumps(payload, sort_keys=True)
    restored = parse_mt5_shadow_resume_payload(json.loads(serialized))
    assert restored.payload_sha256 == state.payload_sha256
    assert restored.checkpoint == result.checkpoint
    return restored


def _assert_equivalent(baseline, segments):
    recovered = segments[-1]
    recovered_decisions = tuple(
        decision for segment in segments for decision in segment.decisions
    )
    assert recovered.processed == baseline.processed
    assert recovered.checkpoint == baseline.checkpoint
    assert recovered.checkpoint.payload_sha256 == baseline.checkpoint.payload_sha256
    assert tuple(item.decision_id for item in recovered_decisions) == tuple(
        item.decision_id for item in baseline.decisions
    )
    assert all(item.action == "NO_ORDER" for item in recovered_decisions)


def test_stop_persist_restart_matches_uninterrupted_run():
    full = _bundle(6)
    baseline = _run(full)

    first = _run(_bundle(3))
    restored = _persist_round_trip(first)
    resumed = _run(full, resume_state=restored)

    assert len(first.decisions) == 3
    assert len(resumed.decisions) == 3
    assert resumed.duplicates_suppressed == 0
    _assert_equivalent(baseline, (first, resumed))


def test_crash_before_latest_persist_replays_uncommitted_bar_and_converges():
    full = _bundle(6)
    baseline = _run(full)

    persisted = _run(_bundle(2))
    restored = _persist_round_trip(persisted)

    # Simulate work on bar 3 followed by a crash before its new checkpoint is persisted.
    in_memory = _run(_bundle(3), resume_state=restored)
    assert len(in_memory.decisions) == 1

    # Restart from the last durable checkpoint. Bar 3 must be replayed exactly once,
    # then processing catches up through bar 6 and converges to the baseline state.
    recovered = _run(full, resume_state=restored)
    assert len(recovered.decisions) == 4
    assert recovered.decisions[0].decision_id == in_memory.decisions[0].decision_id
    _assert_equivalent(baseline, (persisted, recovered))


def test_crash_after_persist_resumes_strictly_after_anchor_and_converges():
    full = _bundle(6)
    baseline = _run(full)

    durable = _run(_bundle(3))
    restored = _persist_round_trip(durable)

    # The checkpoint already includes bar 3. Restarting against overlapping history
    # must process only bars 4-6 and still reach the uninterrupted final state.
    recovered = _run(full, resume_state=restored)
    assert len(recovered.decisions) == 3
    assert recovered.duplicates_suppressed == 0
    assert recovered.decisions[0].decision_id == baseline.decisions[3].decision_id
    _assert_equivalent(baseline, (durable, recovered))
