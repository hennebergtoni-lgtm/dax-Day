from datetime import datetime, timedelta, timezone
import hashlib
import json

from daxlab.runtime.mt5_shadow_integration import evaluate_shadow_from_bundle
from daxlab.runtime.mt5_windows_bundle import parse_windows_mt5_bundle
from daxlab.runtime.prospective_gate import ProspectiveAuthorization
from daxlab.runtime.shadow_soak import SoakFault, run_shadow_soak
from daxlab.runtime.mt5_readonly import Mt5Bar


def _seal(payload: dict) -> dict:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    value = dict(payload)
    value["sha256"] = hashlib.sha256(canonical.encode()).hexdigest()
    return value


def _bundle(*, account=True, engine=True, execution=False) -> dict:
    observed = datetime(2026, 9, 9, 8, 0, tzinfo=timezone.utc)
    bars = []
    for offset in (15, 10, 5):
        t = observed - timedelta(minutes=offset)
        bars.append(
            {
                "open_time": t.isoformat(),
                "open": 25000.0,
                "high": 25002.0,
                "low": 24999.0,
                "close": 25001.0,
            }
        )
    return _seal(
        {
            "schema": "DAXLAB_MT5_WINDOWS_BUNDLE_V1",
            "symbol_resolution_state": "AUTO_EXACT_ALIAS_DATA_ONLY",
            "host_probe": {
                "observed_at": observed.isoformat(),
                "terminal_connected": True,
                "account_connected": account,
                "account_trade_allowed": False,
                "order_execution_enabled": execution,
                "engine_loop_healthy": engine,
                "clock_ok": True,
                "symbols": [
                    {
                        "name": "DE40",
                        "digits": 2,
                        "point": 0.01,
                        "trade_mode": "DISABLED",
                    }
                ],
            },
            "closed_m5_feed": {
                "observed_at": observed.isoformat(),
                "requested_start_pos": 1,
                "max_age_seconds": 600,
                "bars": bars,
            },
            "notes": ["READ_ONLY", "BAR_0_EXCLUDED", "NO_CREDENTIALS", "NO_ORDER_API"],
        }
    )


def _auth() -> ProspectiveAuthorization:
    return ProspectiveAuthorization("STEP_91_USER_AUTHORIZATION", True, True, False)


def test_account_disconnect_blocks_shadow() -> None:
    bundle = parse_windows_mt5_bundle(_bundle(account=False))
    gate, decision, status = evaluate_shadow_from_bundle(
        bundle, authorization=_auth(), single_instance_lock_held=True
    )
    assert not gate.allowed
    assert decision is None
    assert status.status == "BLOCKED"
    assert "ACCOUNT_NOT_CONNECTED" in status.blockers


def test_engine_unhealthy_blocks_shadow() -> None:
    bundle = parse_windows_mt5_bundle(_bundle(engine=False))
    gate, decision, status = evaluate_shadow_from_bundle(
        bundle, authorization=_auth(), single_instance_lock_held=True
    )
    assert not gate.allowed
    assert decision is None
    assert "ENGINE_LOOP_UNHEALTHY" in status.blockers


def test_execution_flag_blocks_shadow() -> None:
    bundle = parse_windows_mt5_bundle(_bundle(execution=True))
    gate, decision, status = evaluate_shadow_from_bundle(
        bundle, authorization=_auth(), single_instance_lock_held=True
    )
    assert not gate.allowed
    assert decision is None
    assert "ORDER_EXECUTION_ENABLED" in status.blockers
    assert "EXECUTION_MUST_REMAIN_DISABLED" in status.blockers


def _bars(count: int = 20) -> tuple[Mt5Bar, ...]:
    start = datetime(2026, 9, 9, 6, 0, tzinfo=timezone.utc)
    return tuple(
        Mt5Bar(
            open_time=start + timedelta(minutes=5 * index),
            open=100.0 + index,
            high=102.0 + index,
            low=99.0 + index,
            close=101.0 + index,
        )
        for index in range(count)
    )


def test_full_run_and_split_resume_have_same_final_checkpoint() -> None:
    source = _bars()
    full = run_shadow_soak(source)
    first = run_shadow_soak(source[:10])
    resumed = run_shadow_soak(source[10:], checkpoint=first.checkpoint)
    assert resumed.processed == full.processed
    assert resumed.checkpoint == full.checkpoint


def test_faulted_bar_then_healthy_bars_continue_no_order_only() -> None:
    source = _bars(8)
    first = run_shadow_soak(source[:4], faults={2: SoakFault(feed_fresh=False)})
    resumed = run_shadow_soak(source[4:], checkpoint=first.checkpoint)
    assert first.blocked == 1
    assert resumed.processed == 8
    assert all(item.action == "NO_ORDER" for item in first.decisions + resumed.decisions)
