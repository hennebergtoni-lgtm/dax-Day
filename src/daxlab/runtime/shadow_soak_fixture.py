"""Deterministic synthetic closed-M5 fixture for V10 SHADOW soak tests only."""
from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from daxlab.runtime.mt5_readonly import Mt5Bar

BERLIN = ZoneInfo("Europe/Berlin")
SESSIONS = 30
BARS_PER_SESSION = 103


def build_bars() -> tuple[Mt5Bar, ...]:
    values: list[Mt5Bar] = []
    day = datetime(2026, 1, 5, 9, 0, tzinfo=BERLIN)
    built = 0
    while built < SESSIONS:
        if day.weekday() < 5:
            base = 16500.0 + built * 4.0
            for index in range(BARS_PER_SESSION):
                at = day + timedelta(minutes=5 * index)
                close = base + index * 0.05 + ((index % 12) - 6) * 0.2
                values.append(
                    Mt5Bar(
                        open_time=at,
                        open=close - 0.1,
                        high=close + 1.0,
                        low=close - 1.0,
                        close=close,
                    )
                )
            built += 1
        day += timedelta(days=1)
    return tuple(values)
