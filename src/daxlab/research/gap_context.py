"""Causal opening-gap context for GAP001 research only."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class OpeningGapContext:
    prior_session_close_time: datetime
    prior_session_close: float
    session_open_time: datetime
    session_open: float
    gap_points: float

    @property
    def direction(self) -> str:
        if self.gap_points > 0:
            return "UP"
        if self.gap_points < 0:
            return "DOWN"
        return "FLAT"


def build_opening_gap(
    *,
    prior_session_close_time: datetime,
    prior_session_close: float,
    session_open_time: datetime,
    session_open: float,
    decision_time: datetime,
) -> OpeningGapContext:
    """Build gap context only when both reference prices were already known."""
    times = (prior_session_close_time, session_open_time, decision_time)
    if any(value.tzinfo is None for value in times):
        raise ValueError("gap timestamps must be timezone-aware")
    if prior_session_close_time >= session_open_time:
        raise ValueError("prior session close must precede session open")
    if session_open_time > decision_time:
        raise ValueError("session open is not yet known at decision_time")
    return OpeningGapContext(
        prior_session_close_time=prior_session_close_time,
        prior_session_close=float(prior_session_close),
        session_open_time=session_open_time,
        session_open=float(session_open),
        gap_points=float(session_open - prior_session_close),
    )
