from datetime import datetime, timezone

from daxlab.runtime.mt5_readonly import Mt5Bar
from daxlab.runtime.shadow_soak import run_shadow_soak


def test_duplicate_counter_counts_repeated_identical_observation() -> None:
    bar = Mt5Bar(
        open_time=datetime(2026, 9, 9, 8, 0, tzinfo=timezone.utc),
        open=100.0,
        high=101.0,
        low=99.0,
        close=100.5,
    )
    result = run_shadow_soak((bar, bar))
    assert result.processed == 1
    assert result.duplicates_suppressed == 1
    assert len(result.decisions) == 1
