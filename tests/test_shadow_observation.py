from __future__ import annotations

from datetime import datetime

import pytest

from daxlab.runtime.shadow_observation import (
    ShadowObservationInput,
    advance_checkpoint,
    build_counters,
    build_shadow_decision,
    initial_checkpoint,
    recovery_payload,
    suppress_duplicate,
    verify_recovery_payload,
)


def observation(**overrides):
    base = dict(
        observed_at=datetime.fromisoformat("2026-09-09T06:00:00+02:00"),
        symbol="EURUSD",
        closed_bar_fingerprint="a" * 64,
        host_read_only_healthy=True,
        feed_fresh=True,
        clock_ok=True,
        single_instance_lock_held=True,
    )
    base.update(overrides)
    return ShadowObservationInput(**base)


def test_healthy_shadow_decision_is_always_no_order():
    decision = build_shadow_decision(observation())
    assert decision.action == "NO_ORDER"
    assert decision.reason_codes == ("OBSERVATION_ONLY_NO_ORDER",)


def test_watchdog_blocks_are_explicit_and_still_no_order():
    decision = build_shadow_decision(
        observation(host_read_only_healthy=False, feed_fresh=False, clock_ok=False)
    )
    assert decision.action == "NO_ORDER"
    assert "MT5_HOST_NOT_HEALTHY" in decision.reason_codes
    assert "CLOSED_M5_FEED_NOT_FRESH" in decision.reason_codes
    assert "CLOCK_NOT_SAFE" in decision.reason_codes


def test_v112_reference_binding_is_fail_closed():
    with pytest.raises(ValueError, match="reference experiment mismatch"):
        observation(reference_experiment_id="V12")
    with pytest.raises(ValueError, match="engine fingerprint mismatch"):
        observation(reference_engine_sha256="0" * 64)


def test_decision_id_is_deterministic_and_duplicates_suppress():
    first = build_shadow_decision(observation())
    second = build_shadow_decision(observation())
    assert first.decision_id == second.decision_id
    seen: set[str] = set()
    assert suppress_duplicate(first, seen) is False
    assert suppress_duplicate(second, seen) is True


def test_checkpoint_resume_advances_without_order_state():
    checkpoint = initial_checkpoint()
    decision = build_shadow_decision(observation())
    advanced = advance_checkpoint(checkpoint, decision)
    assert advanced.processed_count == 1
    assert advanced.last_decision_id == decision.decision_id


def test_dashboard_counters_are_observation_only():
    healthy = build_shadow_decision(observation())
    blocked = build_shadow_decision(observation(feed_fresh=False))
    counters = build_counters((healthy, blocked), duplicates_suppressed=3)
    assert counters.observations == 2
    assert counters.no_order == 2
    assert counters.blocked == 1
    assert counters.duplicates_suppressed == 3


def test_recovery_roundtrip_contract_and_tamper_detection():
    decision = build_shadow_decision(observation())
    checkpoint = advance_checkpoint(initial_checkpoint(), decision)
    counters = build_counters((decision,))
    payload = recovery_payload(
        checkpoint=checkpoint,
        decisions=(decision,),
        counters=counters,
    )
    verify_recovery_payload(payload)
    tampered = dict(payload)
    tampered["execution_capability"] = "ORDER"
    with pytest.raises(ValueError, match="must not carry execution capability"):
        verify_recovery_payload(tampered)


def test_bad_bar_fingerprint_is_rejected():
    with pytest.raises(ValueError, match="sha256"):
        observation(closed_bar_fingerprint="abc")
