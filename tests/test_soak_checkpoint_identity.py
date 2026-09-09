from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from daxlab.runtime.mt5_readonly import Mt5Bar
from daxlab.runtime.shadow_soak import run_shadow_soak, verify_soak_checkpoint


def result():
    start = datetime(2026, 9, 9, 8, 0, tzinfo=timezone.utc)
    bars = tuple(
        Mt5Bar(
            open_time=start + timedelta(minutes=5 * index),
            open=100.0,
            high=101.0,
            low=99.0,
            close=100.5,
        )
        for index in range(2)
    )
    return run_shadow_soak(bars)


def test_checkpoint_rejects_schema_drift() -> None:
    checkpoint = result().checkpoint
    with pytest.raises(ValueError, match="schema mismatch"):
        verify_soak_checkpoint(replace(checkpoint, schema_version="OTHER"))


def test_checkpoint_rejects_duplicate_decision_identity() -> None:
    checkpoint = result().checkpoint
    duplicate = checkpoint.seen_decision_ids[0]
    bad = replace(checkpoint, seen_decision_ids=(duplicate, duplicate))
    with pytest.raises(ValueError, match="duplicate decision IDs"):
        verify_soak_checkpoint(bad)
