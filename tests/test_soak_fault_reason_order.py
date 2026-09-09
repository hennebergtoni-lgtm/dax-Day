from datetime import datetime, timezone

from daxlab.runtime.mt5_readonly import Mt5Bar
from daxlab.runtime.shadow_soak import SoakFault, run_shadow_soak


def test_soak_fault_reason_order_is_deterministic() -> None:
    bar = Mt5Bar(
        open_time=datetime(2026, 9, 9, 8, 0, tzinfo=timezone.utc),
        open=100.0,
        high=101.0,
        low=99.0,
        close=100.5,
    )
    result = run_shadow_soak((bar,), faults={0: SoakFault(False, False, False, False)})
    assert result.decisions[0].reason_codes == (
        "MT5_HOST_NOT_HEALTHY",
        "CLOSED_M5_FEED_NOT_FRESH",
        "CLOCK_NOT_SAFE",
        "SINGLE_INSTANCE_LOCK_NOT_HELD",
    )
