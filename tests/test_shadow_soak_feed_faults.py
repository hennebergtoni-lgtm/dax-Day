from datetime import datetime, timedelta, timezone

import pytest

from daxlab.runtime.mt5_feed_payload import parse_closed_m5_feed


def row(at: datetime, price: float = 100.0) -> dict:
    return {
        "open_time": at.isoformat(),
        "open": price,
        "high": price + 1.0,
        "low": price - 1.0,
        "close": price + 0.25,
    }


def payload(times: list[datetime]) -> dict:
    observed = max(times) + timedelta(minutes=10)
    return {
        "observed_at": observed.isoformat(),
        "requested_start_pos": 1,
        "max_age_seconds": 600,
        "bars": [row(value, 100.0 + index) for index, value in enumerate(times)],
    }


def test_missing_bar_is_explicit_discontinuity() -> None:
    start = datetime(2026, 9, 9, 6, 0, tzinfo=timezone.utc)
    feed = parse_closed_m5_feed(payload([start, start + timedelta(minutes=10)]))
    assert feed.discontinuities
    assert "600s" in feed.discontinuities[0]


def test_out_of_order_bars_are_rejected() -> None:
    start = datetime(2026, 9, 9, 6, 0, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="chronological"):
        parse_closed_m5_feed(payload([start + timedelta(minutes=5), start]))


def test_duplicate_bars_are_rejected() -> None:
    start = datetime(2026, 9, 9, 6, 0, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="unique"):
        parse_closed_m5_feed(payload([start, start]))
