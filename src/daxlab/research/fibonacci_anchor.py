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

    The first eligible bar open is the impulse start. The direction-specific OR
    extreme is the impulse end. Later bars may be present in `bars` but are ignored.
    """
    if confirmation_time.tzinfo is None:
        raise ValueError("OR confirmation time must be timezone-aware")
    if direction not in {"long", "short"}:
        raise ValueError("direction must be long or short")

    required = {time_col, "open", "high", "low"}
    missing = sorted(required - set(bars.columns))
    if missing:
        raise ValueError(f"opening-range bars missing required columns: {missing}")

    times = pd.to_datetime(bars[time_col], utc=True)
    confirmation_utc = pd.Timestamp(confirmation_time).tz_convert("UTC")
    eligible_mask = times <= confirmation_utc
    eligible = bars.loc[eligible_mask].copy()
    eligible[time_col] = times.loc[eligible_mask]
    if eligible.empty:
        raise ValueError("no bars available by OR confirmation time")

    eligible = eligible.sort_values(time_col)
    first = eligible.iloc[0]
    start_price = float(first["open"])
    start_time = first[time_col].to_pydatetime()

    if direction == "long":
        end_idx = eligible["high"].astype(float).idxmax()
        end_price = float(eligible.loc[end_idx, "high"])
    else:
        end_idx = eligible["low"].astype(float).idxmin()
        end_price = float(eligible.loc[end_idx, "low"])
    end_time = eligible.loc[end_idx, time_col].to_pydatetime()

    if end_time < start_time:
        raise ValueError("OR impulse end cannot precede start")

    return CausalImpulseAnchor(
        rule_id="OR_COMPLETED_IMPULSE",
        start_price=start_price,
        start_time=start_time,
        end_price=end_price,
        end_time=end_time,
        confirmation_time=confirmation_time,
    )
