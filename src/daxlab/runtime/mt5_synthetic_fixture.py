"""Synthetic MT5 feed fixtures for offline contract tests only.

Fixtures never represent broker evidence and can never satisfy external-host gates.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from daxlab.runtime.mt5_feed_payload import ClosedM5Feed, parse_closed_m5_feed


def build_synthetic_closed_m5_feed(
    *,
    observed_at: datetime,
    start_open_time: datetime,
    bars: int = 3,
    start_price: float = 100.0,
) -> ClosedM5Feed:
    if observed_at.tzinfo is None or start_open_time.tzinfo is None:
        raise ValueError("synthetic fixture timestamps must be timezone-aware")
    if bars <= 0:
        raise ValueError("bars must be positive")
    rows = []
    for index in range(bars):
        open_time = start_open_time + timedelta(minutes=5 * index)
        price = start_price + index
        rows.append(
            {
                "open_time": open_time.isoformat(),
                "open": price,
                "high": price + 1.0,
                "low": price - 1.0,
                "close": price + 0.25,
            }
        )
    return parse_closed_m5_feed(
        {
            "observed_at": observed_at.isoformat(),
            "requested_start_pos": 1,
            "max_age_seconds": 360,
            "bars": rows,
        }
    )


def synthetic_fixture_evidence_state() -> str:
    return "SYNTHETIC_ONLY_NOT_BROKER_EVIDENCE"
