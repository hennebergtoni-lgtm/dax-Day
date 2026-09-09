from dataclasses import replace
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json

import pytest

from daxlab.runtime.mt5_readonly import Mt5Bar
from daxlab.runtime.shadow_soak import (
    MT5_READONLY_EVIDENCE_STATE,
    SYNTHETIC_EVIDENCE_STATE,
    SoakFault,
    run_shadow_soak,
    soak_recovery_payload,
    soak_summary,
    verify_soak_checkpoint,
    verify_soak_recovery_payload,
)


def bars(count: int = 24) -> tuple[Mt5Bar, ...]:
    start = datetime(2026, 9, 9, 6, 0, tzinfo=timezone.utc)
    return tuple(
        Mt5Bar(
            open_time=start + timedelta(minutes=5 * index),
            open=25000.0 + index,
            high=25002.0 + index,
            low=24999.0 + index,
            close=25001.0 + index,
        )
        for index in range(count)
    )


def test_soak_is_deterministic_and_no_order_only() -> None:
    first = run_shadow_soak(bars())
    second = run_shadow_soak(bars())
    assert first == second
    assert first.processed == 24
    assert first.blocked == 0
    assert all(item.action == "NO_ORDER" for item in first.decisions)
    assert len(first.run_fingerprint) == 64
    assert soak_summary(first)["evidence_state"] == SYNTHETIC_EVIDENCE_STATE
    assert soak_summary(first)["order_execution_enabled"] is False


def test_default_synthetic_run_keeps_legacy_fingerprint_contract() -> None:
    result = run_shadow_soak(bars(3))
    legacy_payload = {
        "prior_processed": 0,
        "decision_ids": [item.decision_id for item in result.decisions],
        "checkpoint_sha256": result.checkpoint.payload_sha256,
    }
    canonical = json.dumps(
        legacy_payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    assert result.run_fingerprint == sha256(canonical.encode("utf-8")).hexdigest()
    assert result.evidence_state == SYNTHETIC_EVIDENCE_STATE


def test_mt5_readonly_evidence_has_distinct_provenance_and_recovery() -> None:
    source = bars(3)
    synthetic = run_shadow_soak(source)
    mt5 = run_shadow_soak(source, evidence_state=MT5_READONLY_EVIDENCE_STATE)
    assert mt5.evidence_state == MT5_READONLY_EVIDENCE_STATE
    assert mt5.run_fingerprint != synthetic.run_fingerprint
    assert mt5.execution_capability == "NONE"
    assert mt5.order_execution_enabled is False
    payload = soak_recovery_payload(mt5)
    assert payload["evidence_state"] == MT5_READONLY_EVIDENCE_STATE
    verify_soak_recovery_payload(payload)


def test_unknown_evidence_state_is_rejected() -> None:
    with pytest.raises(ValueError, match="unsupported shadow soak evidence state"):
        run_shadow_soak(bars(1), evidence_state="UNVERIFIED_BROKER")


def test_resume_suppresses_already_seen_bars() -> None:
    all_bars = bars(24)
    first = run_shadow_soak(all_bars[:12])
    resumed = run_shadow_soak(all_bars, checkpoint=first.checkpoint)
    assert resumed.processed == 24
    assert resumed.duplicates_suppressed == 12
    assert len(resumed.decisions) == 12
    assert resumed.checkpoint.processed_count == 24


def test_repeated_resume_is_idempotent() -> None:
    first = run_shadow_soak(bars())
    again = run_shadow_soak(bars(), checkpoint=first.checkpoint)
    assert again.processed == first.processed
    assert again.duplicates_suppressed == 24
    assert again.decisions == ()
    assert again.checkpoint == first.checkpoint


def test_checkpoint_tamper_is_rejected() -> None:
    result = run_shadow_soak(bars(3))
    bad = replace(result.checkpoint, processed_count=999)
    with pytest.raises(ValueError, match="processed_count/bar identity mismatch|hash mismatch"):
        verify_soak_checkpoint(bad)


def test_fault_matrix_blocks_but_never_orders() -> None:
    fault_map = {
        1: SoakFault(host_read_only_healthy=False),
        2: SoakFault(feed_fresh=False),
        3: SoakFault(clock_ok=False),
        4: SoakFault(single_instance_lock_held=False),
        5: SoakFault(False, False, False, False),
    }
    result = run_shadow_soak(bars(8), faults=fault_map)
    assert result.blocked == 5
    assert all(item.action == "NO_ORDER" for item in result.decisions)
    combined = result.decisions[5].reason_codes
    assert combined == (
        "MT5_HOST_NOT_HEALTHY",
        "CLOSED_M5_FEED_NOT_FRESH",
        "CLOCK_NOT_SAFE",
        "SINGLE_INSTANCE_LOCK_NOT_HELD",
    )


def test_fault_recovery_has_no_retroactive_decision_change() -> None:
    source = bars(6)
    faulted = run_shadow_soak(source[:3], faults={1: SoakFault(feed_fresh=False)})
    before = faulted.decisions
    resumed = run_shadow_soak(source[3:], checkpoint=faulted.checkpoint)
    assert faulted.decisions == before
    assert resumed.processed == 6
    assert all(item.action == "NO_ORDER" for item in resumed.decisions)


def test_recovery_payload_round_trip_and_tamper_detection() -> None:
    result = run_shadow_soak(bars(5))
    payload = soak_recovery_payload(result)
    verify_soak_recovery_payload(payload)
    payload["run_fingerprint"] = "0" * 64
    with pytest.raises(ValueError, match="hash mismatch"):
        verify_soak_recovery_payload(payload)
