from datetime import datetime, timedelta, timezone

from daxlab.runtime.mt5_readonly import Mt5Bar
from daxlab.runtime.shadow_soak import run_shadow_soak


def test_processed_count_tracks_unique_observations_across_resume() -> None:
    start = datetime(2026, 9, 9, 8, 0, tzinfo=timezone.utc)
    bars = tuple(
        Mt5Bar(start + timedelta(minutes=5 * i), 100.0, 101.0, 99.0, 100.5)
        for i in range(4)
    )
    first = run_shadow_soak(bars[:2])
    second = run_shadow_soak(bars, checkpoint=first.checkpoint)
    assert first.processed == 2
    assert second.processed == 4
    assert second.duplicates_suppressed == 2
