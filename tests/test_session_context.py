from datetime import datetime, timezone

import pytest

from daxlab.research.session_context import session_context


def test_session_context_uses_berlin_dst() -> None:
    # 07:00 UTC in summer is 09:00 Europe/Berlin.
    state = session_context(datetime(2026, 7, 1, 7, 0, tzinfo=timezone.utc))
    assert state is not None
    assert state.minutes_since_open == 0
    assert state.phase == "EARLY"


def test_coarse_boundaries_are_fixed() -> None:
    early = session_context(datetime(2026, 1, 5, 11, 0, tzinfo=timezone.utc))
    middle = session_context(datetime(2026, 1, 5, 11, 1, tzinfo=timezone.utc))
    assert early is not None and middle is not None
    # January Berlin = UTC+1, so these are 12:00 and 12:01 local: 180/181 min since open.
    assert early.phase == "MIDDLE"
    assert middle.phase == "MIDDLE"


def test_outside_session_is_none() -> None:
    assert session_context(datetime(2026, 7, 1, 6, 59, tzinfo=timezone.utc)) is None


def test_naive_datetime_fails_closed() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        session_context(datetime(2026, 7, 1, 9, 0))
