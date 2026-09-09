from datetime import datetime, timedelta, timezone

from daxlab.runtime.mt5_readonly import Mt5Bar
from daxlab.runtime.shadow_soak import SoakFault, run_shadow_soak


def test_blocked_counter_counts_only_faulted_unique_observations() -> None:
    start = datetime(2026, 9, 9, 8, 0, tzinfo=timezone.utc)
    bars = tuple(
        Mt5Bar(start + timedelta(minutes=5 * i), 100.0, 101.0, 99.0, 100.5)
        for i in range(3)
    )
    result = run_shadow_soak(bars, faults={1: SoakFault(clock_ok=False)})
    assert result.processed == 3
    assert result.blocked == 1
