from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OpeningGap:
    previous_close: float
    session_open: float
    points: float
    direction: str
    abs_points: float
    atr_fraction: float | None
    prior_range_fraction: float | None


def opening_gap(
    previous_close: float,
    session_open: float,
    *,
    atr: float | None = None,
    prior_range: float | None = None,
) -> OpeningGap:
    previous_close = float(previous_close)
    session_open = float(session_open)
    gap = session_open - previous_close
    direction = "up" if gap > 0 else "down" if gap < 0 else "flat"

    atr_fraction = None
    if atr is not None:
        atr = float(atr)
        if atr <= 0:
            raise ValueError("atr must be positive")
        atr_fraction = abs(gap) / atr

    prior_range_fraction = None
    if prior_range is not None:
        prior_range = float(prior_range)
        if prior_range <= 0:
            raise ValueError("prior_range must be positive")
        prior_range_fraction = abs(gap) / prior_range

    return OpeningGap(
        previous_close=previous_close,
        session_open=session_open,
        points=gap,
        direction=direction,
        abs_points=abs(gap),
        atr_fraction=atr_fraction,
        prior_range_fraction=prior_range_fraction,
    )


def gap_closed(gap: OpeningGap, session_low: float, session_high: float) -> bool:
    """Whether price traded back to the previous close after the session opened."""
    low = float(session_low)
    high = float(session_high)
    if low > high:
        raise ValueError("session_low must be <= session_high")
    if gap.direction == "up":
        return low <= gap.previous_close
    if gap.direction == "down":
        return high >= gap.previous_close
    return True
