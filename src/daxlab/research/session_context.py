"""Causal coarse session context for SESSION001 research only."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
from zoneinfo import ZoneInfo

BERLIN = ZoneInfo("Europe/Berlin")
SESSION_OPEN = time(9, 0)
SESSION_CLOSE = time(17, 30)


@dataclass(frozen=True, slots=True)
class SessionContext:
    local_time: datetime
    minutes_since_open: int
    minutes_to_close: int
    phase: str
    weekday: int


def _minutes(t: time) -> int:
    return t.hour * 60 + t.minute


def session_context(decision_time: datetime) -> SessionContext | None:
    """Return predeclared coarse Berlin-session context known at decision time."""
    if decision_time.tzinfo is None:
        raise ValueError("decision_time must be timezone-aware")
    local = decision_time.astimezone(BERLIN)
    now = _minutes(local.timetz().replace(tzinfo=None))
    open_m = _minutes(SESSION_OPEN)
    close_m = _minutes(SESSION_CLOSE)
    if now < open_m or now > close_m:
        return None
    since = now - open_m
    to_close = close_m - now
    # Fixed coarse buckets: early 0-120m, middle 121-300m, late >300m.
    if since <= 120:
        phase = "EARLY"
    elif since <= 300:
        phase = "MIDDLE"
    else:
        phase = "LATE"
    return SessionContext(
        local_time=local,
        minutes_since_open=since,
        minutes_to_close=to_close,
        phase=phase,
        weekday=local.weekday(),
    )
