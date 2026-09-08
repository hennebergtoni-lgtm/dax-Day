from datetime import datetime, timedelta, timezone

import pytest

from daxlab.research.entry_diagnostics import describe_entry


def test_entry_diagnostics_are_descriptive_only() -> None:
    entry = datetime(2026, 1, 2, 9, 30, tzinfo=timezone.utc)
    state = describe_entry(
        signal_time=entry - timedelta(minutes=10),
        retest_time=entry - timedelta(minutes=5),
        entry_time=entry,
        risk_points=20,
        target_points=30,
    )
    assert state.signal_to_entry_minutes == 10
    assert state.retest_to_entry_minutes == 5
    assert state.rr_points == 1.5


def test_future_signal_fails_closed() -> None:
    entry = datetime(2026, 1, 2, 9, 30, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="signal_time"):
        describe_entry(
            signal_time=entry + timedelta(minutes=5),
            retest_time=None,
            entry_time=entry,
            risk_points=20,
            target_points=30,
        )
