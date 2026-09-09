from datetime import datetime, timezone

from daxlab.runtime.mt5_readonly import Mt5Bar
from daxlab.runtime.shadow_soak import bar_fingerprint


def test_bar_fingerprint_is_deterministic_and_price_sensitive() -> None:
    first = Mt5Bar(
        open_time=datetime(2026, 9, 9, 8, 0, tzinfo=timezone.utc),
        open=100.0,
        high=101.0,
        low=99.0,
        close=100.5,
    )
    same = Mt5Bar(**{
        "open_time": first.open_time,
        "open": first.open,
        "high": first.high,
        "low": first.low,
        "close": first.close,
    })
    changed = Mt5Bar(
        open_time=first.open_time,
        open=100.0,
        high=101.0,
        low=99.0,
        close=100.6,
    )
    assert bar_fingerprint(first) == bar_fingerprint(same)
    assert bar_fingerprint(first) != bar_fingerprint(changed)
