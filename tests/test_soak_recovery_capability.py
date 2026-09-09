from datetime import datetime, timezone

import pytest

from daxlab.runtime.mt5_readonly import Mt5Bar
from daxlab.runtime.shadow_soak import (
    run_shadow_soak,
    soak_recovery_payload,
    verify_soak_recovery_payload,
)


def test_soak_recovery_rejects_capability_escalation() -> None:
    bar = Mt5Bar(
        open_time=datetime(2026, 9, 9, 8, 0, tzinfo=timezone.utc),
        open=100.0,
        high=101.0,
        low=99.0,
        close=100.5,
    )
    payload = soak_recovery_payload(run_shadow_soak((bar,)))
    payload["execution_capability"] = "BROKER"
    with pytest.raises(ValueError, match="execution capability"):
        verify_soak_recovery_payload(payload)
