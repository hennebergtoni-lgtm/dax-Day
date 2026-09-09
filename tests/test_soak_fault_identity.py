from datetime import datetime, timezone

from daxlab.runtime.mt5_readonly import Mt5Bar
from daxlab.runtime.shadow_soak import SoakFault, run_shadow_soak


def test_shadow_decision_identity_changes_when_safety_state_changes() -> None:
    bar = Mt5Bar(
        open_time=datetime(2026, 9, 9, 8, 0, tzinfo=timezone.utc),
        open=100.0,
        high=101.0,
        low=99.0,
        close=100.5,
    )
    healthy = run_shadow_soak((bar,))
    stale = run_shadow_soak((bar,), faults={0: SoakFault(feed_fresh=False)})
    assert healthy.decisions[0].decision_id != stale.decisions[0].decision_id
    assert healthy.decisions[0].action == stale.decisions[0].action == "NO_ORDER"
