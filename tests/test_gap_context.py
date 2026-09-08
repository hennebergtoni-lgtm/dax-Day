from datetime import datetime, timedelta, timezone

import pytest

from daxlab.research.gap_context import build_opening_gap


def test_opening_gap_is_known_after_session_open() -> None:
    close_t = datetime(2026, 1, 2, 16, 30, tzinfo=timezone.utc)
    open_t = datetime(2026, 1, 5, 8, 0, tzinfo=timezone.utc)
    state = build_opening_gap(
        prior_session_close_time=close_t,
        prior_session_close=20000,
        session_open_time=open_t,
        session_open=20025,
        decision_time=open_t + timedelta(minutes=5),
    )
    assert state.gap_points == 25
    assert state.direction == "UP"


def test_future_session_open_fails_closed() -> None:
    close_t = datetime(2026, 1, 2, 16, 30, tzinfo=timezone.utc)
    open_t = datetime(2026, 1, 5, 8, 0, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="not yet known"):
        build_opening_gap(
            prior_session_close_time=close_t,
            prior_session_close=20000,
            session_open_time=open_t,
            session_open=20025,
            decision_time=open_t - timedelta(minutes=1),
        )


def test_invalid_time_order_fails_closed() -> None:
    t = datetime(2026, 1, 5, 8, 0, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="must precede"):
        build_opening_gap(
            prior_session_close_time=t,
            prior_session_close=20000,
            session_open_time=t,
            session_open=20025,
            decision_time=t,
        )
