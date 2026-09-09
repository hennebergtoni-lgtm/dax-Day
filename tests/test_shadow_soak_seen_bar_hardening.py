from dataclasses import replace
from datetime import datetime, timezone

import pytest

from daxlab.runtime.mt5_readonly import Mt5Bar
from daxlab.runtime.shadow_soak import (
    SoakFault,
    bar_fingerprint,
    run_shadow_soak,
    verify_soak_checkpoint,
)


def _bar(minute: int = 0) -> Mt5Bar:
    return Mt5Bar(
        datetime(2026, 9, 9, 8, minute, tzinfo=timezone.utc),
        100.0,
        101.0,
        99.0,
        100.5,
    )


def test_same_closed_bar_is_suppressed_when_fault_state_changes() -> None:
    bar = _bar()
    first = run_shadow_soak((bar,))
    resumed = run_shadow_soak(
        (bar,),
        checkpoint=first.checkpoint,
        faults={0: SoakFault(feed_fresh=False, clock_ok=False)},
    )
    assert resumed.decisions == ()
    assert resumed.processed == 1
    assert resumed.duplicates_suppressed == 1
    assert resumed.checkpoint == first.checkpoint


def test_checkpoint_tracks_accepted_bar_fingerprint() -> None:
    bar = _bar()
    result = run_shadow_soak((bar,))
    assert result.checkpoint.schema_version == "DAXLAB_SHADOW_SOAK_CHECKPOINT_V2"
    assert result.checkpoint.seen_bar_fingerprints == (bar_fingerprint(bar),)
    assert result.checkpoint.processed_count == 1


def test_seen_bar_checkpoint_tamper_is_rejected() -> None:
    result = run_shadow_soak((_bar(),))
    tampered = replace(
        result.checkpoint,
        seen_bar_fingerprints=("0" * 64,),
    )
    with pytest.raises(ValueError, match="hash mismatch"):
        verify_soak_checkpoint(tampered)


def test_split_resume_parity_tracks_same_seen_bars() -> None:
    bars = (_bar(0), _bar(5), _bar(10))
    full = run_shadow_soak(bars)
    first = run_shadow_soak(bars[:2])
    resumed = run_shadow_soak(bars[2:], checkpoint=first.checkpoint)
    assert resumed.processed == full.processed == 3
    assert resumed.checkpoint == full.checkpoint


def test_repeated_resume_after_fault_change_stays_idempotent() -> None:
    bar = _bar()
    first = run_shadow_soak((bar,))
    second = run_shadow_soak(
        (bar,), checkpoint=first.checkpoint, faults={0: SoakFault(host_read_only_healthy=False)}
    )
    third = run_shadow_soak(
        (bar,), checkpoint=second.checkpoint, faults={0: SoakFault(single_instance_lock_held=False)}
    )
    assert second.checkpoint == first.checkpoint
    assert third.checkpoint == first.checkpoint
    assert second.duplicates_suppressed == 1
    assert third.duplicates_suppressed == 1
