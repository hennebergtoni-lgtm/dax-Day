from dataclasses import replace
from datetime import datetime, timedelta, timezone
import hashlib
import json

import pytest

from daxlab.runtime.mt5_shadow_integration import (
    build_mt5_shadow_resume_state,
    combined_recovery_payload,
    evaluate_shadow_from_bundle,
    evaluate_shadow_soak_from_bundle,
    host_readiness_summary,
    mt5_shadow_resume_payload,
    parse_mt5_shadow_resume_payload,
    verify_combined_recovery_payload,
    verify_mt5_shadow_resume_state,
)
from daxlab.runtime.mt5_windows_bundle import parse_windows_mt5_bundle
from daxlab.runtime.prospective_gate import ProspectiveAuthorization
from daxlab.runtime.shadow_observation import advance_checkpoint, initial_checkpoint
from daxlab.runtime.shadow_soak import MT5_READONLY_EVIDENCE_STATE


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
    with pytest.raises(ValueError, match="non-empty list"):
        parse_windows_mt5_bundle(payload)


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


def test_multi_bar_shadow_soak_is_no_order_only() -> None:
    bundle = parse_windows_mt5_bundle(_bundle_payload())
    gate, result, status = evaluate_shadow_soak_from_bundle(
        bundle,
        authorization=_auth(),
        single_instance_lock_held=True,
    )
    assert gate.allowed
    assert result is not None
    assert status.status == "GREEN"
    assert result.processed == 3
    assert result.evidence_state == MT5_READONLY_EVIDENCE_STATE
    assert result.execution_capability == "NONE"
    assert result.order_execution_enabled is False
    assert all(item.action == "NO_ORDER" for item in result.decisions)


def test_multi_bar_shadow_resume_is_provenance_bound_and_idempotent() -> None:
    bundle = parse_windows_mt5_bundle(_bundle_payload())
    _, first, status = evaluate_shadow_soak_from_bundle(
        bundle,
        authorization=_auth(),
        single_instance_lock_held=True,
    )
    assert first is not None
    assert status.symbol == "DE40"
    resume_state = build_mt5_shadow_resume_state(
        symbol=status.symbol,
        checkpoint=first.checkpoint,
    )
    verify_mt5_shadow_resume_state(resume_state, expected_symbol="DE40")
    _, resumed, _ = evaluate_shadow_soak_from_bundle(
        bundle,
        authorization=_auth(),
        single_instance_lock_held=True,
        resume_state=resume_state,
    )
    assert resumed is not None
    assert resumed.processed == first.processed
    assert resumed.evidence_state == MT5_READONLY_EVIDENCE_STATE
    assert resumed.duplicates_suppressed == 0
    assert resumed.decisions == ()


def test_mt5_resume_processes_only_bars_after_anchor() -> None:
    first_payload = _bundle_payload()
    first_payload.pop("sha256")
    first_payload["closed_m5_feed"]["bars"] = first_payload["closed_m5_feed"]["bars"][:2]
    first_bundle = parse_windows_mt5_bundle(_seal(first_payload))
    _, first, status = evaluate_shadow_soak_from_bundle(
        first_bundle,
        authorization=_auth(),
        single_instance_lock_held=True,
    )
    assert first is not None and status.symbol is not None
    assert first.processed == 2
    resume_state = build_mt5_shadow_resume_state(
        symbol=status.symbol,
        checkpoint=first.checkpoint,
    )

    full_bundle = parse_windows_mt5_bundle(_bundle_payload())
    _, resumed, _ = evaluate_shadow_soak_from_bundle(
        full_bundle,
        authorization=_auth(),
        single_instance_lock_held=True,
        resume_state=resume_state,
    )
    assert resumed is not None
    assert resumed.processed == 3
    assert len(resumed.decisions) == 1
    assert resumed.duplicates_suppressed == 0
    assert resumed.execution_capability == "NONE"
    assert resumed.order_execution_enabled is False


def test_mt5_resume_missing_anchor_fails_closed() -> None:
    changed_payload = _bundle_payload()
    changed_payload.pop("sha256")
    changed_payload["closed_m5_feed"]["bars"][-1]["close"] = 25000.5
    changed_bundle = parse_windows_mt5_bundle(_seal(changed_payload))
    _, first, status = evaluate_shadow_soak_from_bundle(
        changed_bundle,
        authorization=_auth(),
        single_instance_lock_held=True,
    )
    assert first is not None and status.symbol is not None
    resume_state = build_mt5_shadow_resume_state(
        symbol=status.symbol,
        checkpoint=first.checkpoint,
    )

    original_bundle = parse_windows_mt5_bundle(_bundle_payload())
    with pytest.raises(RuntimeError, match="anchor not found"):
        evaluate_shadow_soak_from_bundle(
            original_bundle,
            authorization=_auth(),
            single_instance_lock_held=True,
            resume_state=resume_state,
        )


def test_mt5_resume_payload_round_trip_is_credential_free() -> None:
    bundle = parse_windows_mt5_bundle(_bundle_payload())
    _, result, status = evaluate_shadow_soak_from_bundle(
        bundle,
        authorization=_auth(),
        single_instance_lock_held=True,
    )
    assert result is not None and status.symbol is not None
    state = build_mt5_shadow_resume_state(
        symbol=status.symbol,
        checkpoint=result.checkpoint,
    )
    payload = mt5_shadow_resume_payload(state)
    parsed = parse_mt5_shadow_resume_payload(payload)
    assert parsed == state
    serialized = json.dumps(payload).lower()
    for forbidden in ("password", "login", "token", "secret", "account_id"):
        assert forbidden not in serialized
    assert payload["execution_capability"] == "NONE"
    assert payload["order_execution_enabled"] is False


def test_mt5_resume_rejects_evidence_state_tamper() -> None:
    bundle = parse_windows_mt5_bundle(_bundle_payload())
    _, result, status = evaluate_shadow_soak_from_bundle(
        bundle,
        authorization=_auth(),
        single_instance_lock_held=True,
    )
    assert result is not None and status.symbol is not None
    state = build_mt5_shadow_resume_state(
        symbol=status.symbol,
        checkpoint=result.checkpoint,
    )
    bad = replace(state, evidence_state="SYNTHETIC_ONLY_NOT_BROKER_EVIDENCE")
    with pytest.raises(ValueError, match="evidence state mismatch"):
        verify_mt5_shadow_resume_state(bad, expected_symbol="DE40")


def test_mt5_resume_rejects_symbol_tamper() -> None:
    bundle = parse_windows_mt5_bundle(_bundle_payload())
    _, result, status = evaluate_shadow_soak_from_bundle(
        bundle,
        authorization=_auth(),
        single_instance_lock_held=True,
    )
    assert result is not None and status.symbol is not None
    state = build_mt5_shadow_resume_state(
        symbol=status.symbol,
        checkpoint=result.checkpoint,
    )
    bad = replace(state, symbol="GER40")
    with pytest.raises(ValueError, match="symbol mismatch"):
        verify_mt5_shadow_resume_state(bad, expected_symbol="DE40")


def test_mt5_resume_rejects_hash_tamper() -> None:
    bundle = parse_windows_mt5_bundle(_bundle_payload())
    _, result, status = evaluate_shadow_soak_from_bundle(
        bundle,
        authorization=_auth(),
        single_instance_lock_held=True,
    )
    assert result is not None and status.symbol is not None
    state = build_mt5_shadow_resume_state(
        symbol=status.symbol,
        checkpoint=result.checkpoint,
    )
    bad = replace(state, payload_sha256="0" * 64)
    with pytest.raises(ValueError, match="hash mismatch"):
        verify_mt5_shadow_resume_state(bad, expected_symbol="DE40")


def test_mt5_resume_payload_rejects_execution_capability() -> None:
    bundle = parse_windows_mt5_bundle(_bundle_payload())
    _, result, status = evaluate_shadow_soak_from_bundle(
        bundle,
        authorization=_auth(),
        single_instance_lock_held=True,
    )
    assert result is not None and status.symbol is not None
    state = build_mt5_shadow_resume_state(
        symbol=status.symbol,
        checkpoint=result.checkpoint,
    )
    payload = mt5_shadow_resume_payload(state)
    payload["order_execution_enabled"] = True
    with pytest.raises(ValueError, match="keep order execution disabled"):
        parse_mt5_shadow_resume_payload(payload)


def test_bare_generic_checkpoint_is_not_public_mt5_resume_api() -> None:
    bundle = parse_windows_mt5_bundle(_bundle_payload())
    _, result, _ = evaluate_shadow_soak_from_bundle(
        bundle,
        authorization=_auth(),
        single_instance_lock_held=True,
    )
    assert result is not None
    with pytest.raises(TypeError, match="unexpected keyword argument 'checkpoint'"):
        evaluate_shadow_soak_from_bundle(
            bundle,
            authorization=_auth(),
            single_instance_lock_held=True,
            checkpoint=result.checkpoint,  # type: ignore[call-arg]
        )


def test_multi_bar_shadow_blocked_gate_produces_no_result() -> None:
    bundle = parse_windows_mt5_bundle(_bundle_payload())
    gate, result, status = evaluate_shadow_soak_from_bundle(
        bundle,
        authorization=_auth(),
        single_instance_lock_held=False,
    )
    assert not gate.allowed
    assert result is None
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
    with pytest.raises(ValueError, match="hash mismatch"):
        verify_combined_recovery_payload(payload)


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
