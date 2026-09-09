from datetime import datetime

import pytest

from daxlab.runtime.mt5_readonly import Mt5Bar
from daxlab.runtime.shadow_soak import run_shadow_soak


def test_soak_rejects_timezone_naive_bar() -> None:
    bar = Mt5Bar(
        open_time=datetime(2026, 9, 9, 8, 0),
        open=100.0,
        high=101.0,
        low=99.0,
        close=100.5,
    )
    with pytest.raises(ValueError, match="timezone-aware"):
        run_shadow_soak((bar,))
