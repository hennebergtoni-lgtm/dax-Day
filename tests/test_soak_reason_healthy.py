from datetime import datetime, timezone

from daxlab.runtime.mt5_readonly import Mt5Bar
from daxlab.runtime.shadow_soak import run_shadow_soak


def test_healthy_synthetic_observation_still_says_observation_only_no_order() -> None:
    bar = Mt5Bar(
        open_time=datetime(2026, 9, 9, 8, 0, tzinfo=timezone.utc),
        open=100.0,
        high=101.0,
        low=99.0,
        close=100.5,
    )
    result = run_shadow_soak((bar,))
    assert result.decisions[0].reason_codes == ("OBSERVATION_ONLY_NO_ORDER",)
