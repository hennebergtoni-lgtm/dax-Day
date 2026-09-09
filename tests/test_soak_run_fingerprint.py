from datetime import datetime, timedelta, timezone

from daxlab.runtime.mt5_readonly import Mt5Bar
from daxlab.runtime.shadow_soak import run_shadow_soak


def make(close: float) -> tuple[Mt5Bar, ...]:
    start = datetime(2026, 9, 9, 8, 0, tzinfo=timezone.utc)
    return (
        Mt5Bar(start, 100.0, 101.0, 99.0, 100.5),
        Mt5Bar(start + timedelta(minutes=5), 100.5, 101.5, 99.5, close),
    )


def test_soak_run_fingerprint_is_repeatable_and_data_sensitive() -> None:
    first = run_shadow_soak(make(101.0))
    second = run_shadow_soak(make(101.0))
    changed = run_shadow_soak(make(101.1))
    assert first.run_fingerprint == second.run_fingerprint
    assert first.run_fingerprint != changed.run_fingerprint
