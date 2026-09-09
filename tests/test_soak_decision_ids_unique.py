from datetime import datetime, timedelta, timezone

from daxlab.runtime.mt5_readonly import Mt5Bar
from daxlab.runtime.shadow_soak import run_shadow_soak


def test_unique_bars_create_unique_decision_ids() -> None:
    start = datetime(2026, 9, 9, 8, 0, tzinfo=timezone.utc)
    bars = tuple(
        Mt5Bar(start + timedelta(minutes=5 * i), 100.0 + i, 101.0 + i, 99.0 + i, 100.5 + i)
        for i in range(10)
    )
    result = run_shadow_soak(bars)
    ids = tuple(item.decision_id for item in result.decisions)
    assert len(ids) == len(set(ids)) == 10
