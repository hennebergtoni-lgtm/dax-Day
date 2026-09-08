from datetime import datetime, timezone

import pytest

from daxlab.research.twap import TwapBar, session_twap_before_entry


def utc(hour: int, minute: int) -> datetime:
    return datetime(2026, 1, 15, hour, minute, tzinfo=timezone.utc)


def test_twap_uses_only_completed_bars_strictly_before_entry() -> None:
    # January Berlin is UTC+1: 08:00 UTC == 09:00 Berlin.
    bars = [
        TwapBar(utc(8, 0), 100.0),
        TwapBar(utc(8, 5), 102.0),
        TwapBar(utc(8, 10), 1000.0),  # completes exactly at entry -> forbidden
    ]
    state = session_twap_before_entry(bars, entry_time=utc(8, 15))
    assert state is not None
    assert state.completed_bar_count == 2
    assert state.session_twap_close == 101.0
    assert state.state_time == utc(8, 10)
    assert state.state_time < utc(8, 15)


def test_twap_ignores_prior_session_and_future_suffix() -> None:
    bars = [
        TwapBar(datetime(2026, 1, 14, 8, 0, tzinfo=timezone.utc), 1.0),
        TwapBar(utc(8, 0), 100.0),
        TwapBar(utc(8, 5), 102.0),
        TwapBar(utc(10, 0), 9999.0),
    ]
    state = session_twap_before_entry(bars, entry_time=utc(8, 15))
    assert state is not None
    assert state.session_twap_close == 101.0
    assert state.completed_bar_count == 2


def test_twap_returns_none_before_any_session_bar_is_available() -> None:
    state = session_twap_before_entry([TwapBar(utc(8, 0), 100.0)], entry_time=utc(8, 5))
    assert state is None


def test_twap_requires_timezone_aware_times() -> None:
    with pytest.raises(ValueError):
        session_twap_before_entry([], entry_time=datetime(2026, 1, 15, 9, 15))
