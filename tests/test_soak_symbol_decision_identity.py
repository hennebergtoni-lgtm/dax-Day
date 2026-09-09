from datetime import datetime, timezone

from daxlab.runtime.mt5_readonly import Mt5Bar
from daxlab.runtime.shadow_soak import run_shadow_soak


def test_shadow_decision_identity_binds_symbol() -> None:
    bar = Mt5Bar(
        open_time=datetime(2026, 9, 9, 8, 0, tzinfo=timezone.utc),
        open=100.0,
        high=101.0,
        low=99.0,
        close=100.5,
    )
    de40 = run_shadow_soak((bar,), symbol="DE40")
    dax40 = run_shadow_soak((bar,), symbol="DAX40")
    assert de40.decisions[0].decision_id != dax40.decisions[0].decision_id
