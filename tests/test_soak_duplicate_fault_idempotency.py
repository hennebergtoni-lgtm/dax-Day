from datetime import datetime, timezone

from daxlab.runtime.mt5_readonly import Mt5Bar
from daxlab.runtime.shadow_soak import SoakFault, run_shadow_soak


def test_duplicate_faulted_observation_is_suppressed_on_resume() -> None:
    bar = Mt5Bar(
        open_time=datetime(2026, 9, 9, 8, 0, tzinfo=timezone.utc),
        open=100.0,
        high=101.0,
        low=99.0,
        close=100.5,
    )
    fault = {0: SoakFault(feed_fresh=False)}
    first = run_shadow_soak((bar,), faults=fault)
    second = run_shadow_soak((bar,), checkpoint=first.checkpoint, faults=fault)
    assert first.blocked == 1
    assert second.decisions == ()
    assert second.duplicates_suppressed == 1
    assert second.processed == 1
