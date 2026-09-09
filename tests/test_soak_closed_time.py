from datetime import datetime, timezone

from daxlab.runtime.mt5_readonly import Mt5Bar
from daxlab.runtime.shadow_soak import run_shadow_soak


def test_soak_observation_occurs_after_completed_m5_bar() -> None:
    at = datetime(2026, 9, 9, 8, 0, tzinfo=timezone.utc)
    bar = Mt5Bar(at, 100.0, 101.0, 99.0, 100.5)
    result = run_shadow_soak((bar,))
    assert result.decisions[0].observed_at > at
    assert (result.decisions[0].observed_at - at).total_seconds() == 301
