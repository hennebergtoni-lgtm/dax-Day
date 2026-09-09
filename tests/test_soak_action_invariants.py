from datetime import datetime, timezone

from daxlab.runtime.mt5_readonly import Mt5Bar
from daxlab.runtime.shadow_soak import SoakFault, run_shadow_soak


def test_even_fully_faulted_observation_remains_no_order_and_no_capability() -> None:
    bar = Mt5Bar(
        open_time=datetime(2026, 9, 9, 8, 0, tzinfo=timezone.utc),
        open=100.0,
        high=101.0,
        low=99.0,
        close=100.5,
    )
    result = run_shadow_soak(
        (bar,),
        faults={0: SoakFault(False, False, False, False)},
    )
    assert result.blocked == 1
    assert result.decisions[0].action == "NO_ORDER"
    assert result.execution_capability == "NONE"
    assert result.order_execution_enabled is False
