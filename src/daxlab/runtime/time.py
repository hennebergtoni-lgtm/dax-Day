"""Deterministic Europe/Berlin time conversion helpers."""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

BERLIN = ZoneInfo("Europe/Berlin")


def to_berlin(timestamp: datetime) -> datetime:
    """Convert an aware timestamp to Europe/Berlin using the IANA DST rules."""
    if timestamp.tzinfo is None:
        raise ValueError("timestamp must be timezone-aware")
    return timestamp.astimezone(BERLIN)


def assert_strict_utc_order(previous: datetime, current: datetime) -> None:
    """Require monotonic absolute time even across DST folds and jumps."""
    if previous.tzinfo is None or current.tzinfo is None:
        raise ValueError("timestamps must be timezone-aware")
    if current.timestamp() <= previous.timestamp():
        raise ValueError("timestamps must be strictly increasing in absolute time")
