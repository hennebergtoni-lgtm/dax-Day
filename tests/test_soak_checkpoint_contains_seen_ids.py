from datetime import datetime, timedelta, timezone

from daxlab.runtime.mt5_readonly import Mt5Bar
from daxlab.runtime.shadow_soak import run_shadow_soak


def test_checkpoint_contains_all_unique_processed_decision_ids() -> None:
    start = datetime(2026, 9, 9, 8, 0, tzinfo=timezone.utc)
    bars = tuple(
        Mt5Bar(start + timedelta(minutes=5 * i), 100.0, 101.0, 99.0, 100.5)
        for i in range(3)
    )
    result = run_shadow_soak(bars)
    assert set(result.checkpoint.seen_decision_ids) == {
        item.decision_id for item in result.decisions
    }
