from datetime import datetime, timezone

import pandas as pd

from daxlab.research.fibonacci_anchor import build_opening_range_anchor


def test_future_price_pollution_cannot_change_confirmed_opening_range_anchor():
    bars = pd.DataFrame(
        {
            "datetime": pd.date_range("2026-01-05 08:00", periods=8, freq="5min", tz="UTC"),
            "open": [100, 101, 102, 103, 104, 105, 106, 107],
            "high": [102, 104, 106, 999, 108, 109, 110, 111],
            "low": [99, 100, 101, -999, 103, 104, 105, 106],
        }
    )
    confirmation = datetime(2026, 1, 5, 8, 15, tzinfo=timezone.utc)

    clean = build_opening_range_anchor(
        bars,
        confirmation_time=confirmation,
        direction="long",
    )

    polluted = bars.copy()
    polluted.loc[polluted["datetime"] >= confirmation, "high"] = 99999
    polluted.loc[polluted["datetime"] >= confirmation, "low"] = -99999
    observed = build_opening_range_anchor(
        polluted,
        confirmation_time=confirmation,
        direction="long",
    )

    assert observed == clean
    assert clean.start_price == 100.0
    assert clean.end_price == 106.0
    assert clean.confirmation_time == confirmation


def test_bar_opening_at_confirmation_is_not_yet_closed_or_eligible():
    bars = pd.DataFrame(
        {
            "datetime": pd.date_range("2026-01-05 08:00", periods=4, freq="5min", tz="UTC"),
            "open": [100, 101, 102, 103],
            "high": [102, 104, 106, 999],
            "low": [99, 100, 101, -999],
        }
    )
    confirmation = datetime(2026, 1, 5, 8, 15, tzinfo=timezone.utc)
    anchor = build_opening_range_anchor(
        bars,
        confirmation_time=confirmation,
        direction="long",
    )

    assert anchor.end_price == 106.0
    assert anchor.end_time < confirmation
