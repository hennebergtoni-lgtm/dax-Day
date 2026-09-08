"""Descriptive ENTRY001 diagnostics over frozen V11.2 trade records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class EntryDiagnostics:
    signal_to_entry_minutes: float | None
    retest_to_entry_minutes: float | None
    risk_points: float
    target_points: float
    rr_points: float | None


def describe_entry(
    *,
    signal_time: datetime | None,
    retest_time: datetime | None,
    entry_time: datetime,
    risk_points: float,
    target_points: float,
) -> EntryDiagnostics:
    """Describe an already-completed frozen-reference entry without altering it."""
    if risk_points < 0 or target_points < 0:
        raise ValueError("entry diagnostic points must be non-negative")
    if signal_time is not None and signal_time > entry_time:
        raise ValueError("signal_time cannot be after entry_time")
    if retest_time is not None and retest_time > entry_time:
        raise ValueError("retest_time cannot be after entry_time")

    def minutes(start: datetime | None) -> float | None:
        if start is None:
            return None
        return (entry_time - start).total_seconds() / 60.0

    rr = None if risk_points == 0 else target_points / risk_points
    return EntryDiagnostics(
        signal_to_entry_minutes=minutes(signal_time),
        retest_to_entry_minutes=minutes(retest_time),
        risk_points=float(risk_points),
        target_points=float(target_points),
        rr_points=rr,
    )
