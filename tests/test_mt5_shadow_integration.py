from datetime import datetime, timedelta, timezone
import hashlib
import json

from daxlab.runtime.mt5_shadow_integration import (
    combined_recovery_payload,
    evaluate_shadow_from_bundle,
    host_readiness_summary,
    verify_combined_recovery_payload,
)
from daxlab.runtime.mt5_windows_bundle import parse_windows_mt5_bundle
from daxlab.runtime.prospective_gate import ProspectiveAuthorization
from daxlab.runtime.shadow_observation import advance_checkpoint, initial_checkpoint


def _seal(payload: dict) -> dict:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    value = dict(payload)
    value["sha256"] = hashlib.sha256(canonical.encode()).hexdigest()
    return value


def _bundle_payload(*, terminal_connected: bool = True, state: str = "AUTO_EXACT_ALIAS_DATA_ONLY") -> dict:
    observed = datetime(2026, 9, 9, 6, 30, tzinfo=timezone.utc)
    latest = observed - timedelta(minutes=5)
    bars = []
    for offset in (10, 5, 0):
        t = latest - timedelta(minutes=offset)
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
            "symbol_resolution_state": state,
            "host_probe": {
                "observed_at": observed.isoformat(),
                "terminal_connected": terminal_connected,
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
        paper_authorized=True,
        live_authorized=False,
    )


def test_parse_is_idempotent() -> None:
    payload = _bundle_payload()
    one = parse_windows_mt5_bundle(payload)
    two = parse_windows_mt5_bundle(payload)
    assert one == two
    assert one.fingerprint == two.fingerprint


def test_terminal_disconnected_is_blocked() -> None:
    bundle = parse_windows_mt5_bundle(_bundle_payload(terminal_connected=False))
    assert "TERMINAL_NOT_CONNECTED" in bundle.blockers


def test_missing_bars_is_rejected() -> None:
    payload = _bundle_payload()
    payload.pop("sha256")
    payload["closed_m5_feed"]["bars"] = []
    payload = _seal(payload)
    try:
        parse_windows_mt5_bundle(payload)
    except ValueError as exc:
        assert "non-empty list" in str(exc)
    else:
        raise AssertionError("missing bars must be rejected")


def test_ambiguous_symbol_is_blocked() -> None:
    bundle = parse_windows_mt5_bundle(_bundle_payload(state="AMBIGUOUS_DATA_ONLY"))
    assert "SYMBOL_AMBIGUOUS_DATA_ONLY" in bundle.blockers


def test_host_to_shadow_end_to_end_is_no_order() -> None:
    bundle = parse_windows_mt5_bundle(_bundle_payload())
    gate, decision, status = evaluate_shadow_from_bundle(
        bundle,
        authorization=_auth(),
        single_instance_lock_held=True,
    )
    assert gate.allowed
    assert decision is not None
    assert decision.action == "NO_ORDER"
    assert decision.reason_codes == ("OBSERVATION_ONLY_NO_ORDER",)
    assert status.status == "GREEN"
    assert status.order_execution_enabled is False


def test_single_instance_lock_is_bound_to_status_and_gate() -> None:
    bundle = parse_windows_mt5_bundle(_bundle_payload())
    gate, decision, status = evaluate_shadow_from_bundle(
        bundle,
        authorization=_auth(),
        single_instance_lock_held=False,
    )
    assert not gate.allowed
    assert decision is None
    assert "SINGLE_INSTANCE_LOCK_NOT_HELD" in status.blockers
    assert status.status == "BLOCKED"


def test_combined_recovery_round_trip_and_tamper_detection() -> None:
    bundle = parse_windows_mt5_bundle(_bundle_payload())
    _, decision, _ = evaluate_shadow_from_bundle(
        bundle,
        authorization=_auth(),
        single_instance_lock_held=True,
    )
    assert decision is not None
    checkpoint = advance_checkpoint(initial_checkpoint(), decision)
    payload = combined_recovery_payload(
        bundle=bundle,
        checkpoint=checkpoint,
        decision=decision,
    )
    verify_combined_recovery_payload(payload)
    payload["host_evidence_sha256"] = "0" * 64
    try:
        verify_combined_recovery_payload(payload)
    except ValueError as exc:
        assert "hash mismatch" in str(exc)
    else:
        raise AssertionError("tampered recovery payload must fail")


def test_readiness_summary_is_credential_free() -> None:
    bundle = parse_windows_mt5_bundle(_bundle_payload())
    _, _, status = evaluate_shadow_from_bundle(
        bundle,
        authorization=_auth(),
        single_instance_lock_held=True,
    )
    summary = host_readiness_summary(status)
    serialized = json.dumps(summary).lower()
    for forbidden in ("password", "login", "token", "secret", "account_id"):
        assert forbidden not in serialized
    assert summary["order_execution_enabled"] is False
