from datetime import datetime, timezone

import pytest

from daxlab.runtime.mt5_readonly import Mt5Bar
from daxlab.runtime.shadow_soak import SoakFault, run_shadow_soak


@pytest.mark.parametrize(
    "fault",
    [
        SoakFault(host_read_only_healthy=False),
        SoakFault(feed_fresh=False),
        SoakFault(clock_ok=False),
        SoakFault(single_instance_lock_held=False),
    ],
)
def test_each_individual_fault_remains_no_order(fault: SoakFault) -> None:
    bar = Mt5Bar(
        open_time=datetime(2026, 9, 9, 8, 0, tzinfo=timezone.utc),
        open=100.0,
        high=101.0,
        low=99.0,
        close=100.5,
    )
    result = run_shadow_soak((bar,), faults={0: fault})
    assert result.blocked == 1
    assert result.decisions[0].action == "NO_ORDER"
