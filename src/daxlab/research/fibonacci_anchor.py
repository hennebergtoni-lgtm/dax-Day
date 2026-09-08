"""Causal FIB001 anchor generators kept separate from the pure Fibonacci math core."""
from __future__ import annotations

from datetime import datetime

import pandas as pd

from daxlab.research.fibonacci_retracement import CausalImpulseAnchor


def build_opening_range_anchor(
    bars: pd.DataFrame,
    *,
    confirmation_time: datetime,
    direction: str,
    time_col: str = "datetime",
) -> CausalImpulseAnchor:
    """Build an immutable OR impulse using only bars available by OR confirmation.

    `bars` may contain later observations; they are ignored by construction.
    """
    if confirmation_time.tzinfo is None:
        raise ValueError("OR confirmation time must be timezone-aware")
    if direction not in {"long", "short"}:
        raise ValueError("direction must be long or short")

    required = {time_col, "high", "low"}
    missing = sorted(required - set(bars.columns))
    if missing:
        raise ValueError(f"opening-range bars missing required columns: {missing}")

    times = pd.to_datetime(bars[time_col], utc=True)
    confirmation_utc = pd.Timestamp(confirmation_time).tz_convert("UTC")
    eligible = bars.loc[times <= confirmation_utc].copy()
    eligible[time_col] = times.loc[times <= confirmation_utc]
    if eligible.empty:
        raise ValueError("no bars available by OR confirmation time")

    low_idx = eligible["low"].astype(float).idxmin()
    high_idx = eligible["high"].astype(float).idxmax()
    low_price = float(eligible.loc[low_idx, "low"])
    high_price = float(eligible.loc[high_idx, "high"])
    low_time = eligible.loc[low_idx, time_col].to_pydatetime()
    high_time = eligible.loc[high_idx, time_col].to_pydatetime()

    if direction == "long":
        start_price, start_time = low_price, low_time
        end_price, end_time = high_price, high_time
    else:
        start_price, start_time = high_price, high_time
        end_price, end_time = low_price, low_time

    # The directional extremes can occur in either chronological order inside the OR.
    # The anchor becomes usable only at confirmation, so its recorded start/end event
    # times are normalized chronologically while prices preserve the directional move.
    chronological_start = min(start_time, end_time)
    chronological_end = max(start_time, end_time)
    return CausalImpulseAnchor(
        rule_id="OR_COMPLETED_IMPULSE",
        start_price=start_price,
        start_time=chronological_start,
        end_price=end_price,
        end_time=chronological_end,
        confirmation_time=confirmation_time,
    )
