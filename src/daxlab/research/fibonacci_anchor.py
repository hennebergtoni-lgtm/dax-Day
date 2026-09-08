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
    bar_minutes: int = 5,
) -> CausalImpulseAnchor:
    """Build an immutable OR impulse from bars closed by confirmation time.

    `time_col` is treated as bar-open/event time. A bar is eligible only when its
    derived close time is less than or equal to `confirmation_time`. Later/open
    bars may be present in `bars` but are ignored by construction.
    """
    if confirmation_time.tzinfo is None:
        raise ValueError("OR confirmation time must be timezone-aware")
    if direction not in {"long", "short"}:
        raise ValueError("direction must be long or short")
    if bar_minutes <= 0:
        raise ValueError("bar_minutes must be positive")

    required = {time_col, "open", "high", "low"}
    missing = sorted(required - set(bars.columns))
    if missing:
        raise ValueError(f"opening-range bars missing required columns: {missing}")

    times = pd.to_datetime(bars[time_col], utc=True)
    closes = times + pd.to_timedelta(bar_minutes, unit="min")
    confirmation_utc = pd.Timestamp(confirmation_time).tz_convert("UTC")
    eligible_mask = closes <= confirmation_utc
    eligible = bars.loc[eligible_mask].copy()
    eligible[time_col] = times.loc[eligible_mask]
    if eligible.empty:
        raise ValueError("no closed bars available by OR confirmation time")

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


def build_confirmed_breakout_anchor(
    bars: pd.DataFrame,
    *,
    boundary_price: float,
    breakout_time: datetime,
    available_until: datetime,
    direction: str,
    time_col: str = "datetime",
) -> CausalImpulseAnchor:
    """Freeze the first causal post-breakout impulse before `available_until`.

    The reference research timestamps are treated as completed-state labels here.
    The breakout row must close beyond the supplied completed-OR boundary. The
    directional extreme advances only while later completed rows extend it. The
    first failure to extend freezes the anchor. Future rows are ignored.
    """
    if breakout_time.tzinfo is None or available_until.tzinfo is None:
        raise ValueError("breakout and availability times must be timezone-aware")
    if breakout_time >= available_until:
        raise ValueError("available_until must follow breakout_time")
    if direction not in {"long", "short"}:
        raise ValueError("direction must be long or short")

    required = {time_col, "high", "low", "close"}
    missing = sorted(required - set(bars.columns))
    if missing:
        raise ValueError(f"breakout bars missing required columns: {missing}")

    times = pd.to_datetime(bars[time_col], utc=True)
    breakout_utc = pd.Timestamp(breakout_time).tz_convert("UTC")
    available_utc = pd.Timestamp(available_until).tz_convert("UTC")
    work = bars.loc[(times >= breakout_utc) & (times < available_utc)].copy()
    work[time_col] = times.loc[(times >= breakout_utc) & (times < available_utc)]
    work = work.sort_values(time_col)
    if work.empty or work.iloc[0][time_col] != breakout_utc:
        raise ValueError("breakout bar is missing")

    first = work.iloc[0]
    boundary = float(boundary_price)
    first_close = float(first["close"])
    if direction == "long" and first_close <= boundary:
        raise ValueError("long breakout bar must close above boundary")
    if direction == "short" and first_close >= boundary:
        raise ValueError("short breakout bar must close below boundary")

    if direction == "long":
        extreme = float(first["high"])
    else:
        extreme = float(first["low"])
    extreme_time = first[time_col].to_pydatetime()

    freeze_time: datetime | None = None
    for _, row in work.iloc[1:].iterrows():
        if direction == "long":
            candidate = float(row["high"])
            if candidate > extreme:
                extreme = candidate
                extreme_time = row[time_col].to_pydatetime()
                continue
        else:
            candidate = float(row["low"])
            if candidate < extreme:
                extreme = candidate
                extreme_time = row[time_col].to_pydatetime()
                continue
        freeze_time = row[time_col].to_pydatetime()
        break

    if freeze_time is None:
        raise ValueError("breakout impulse is not frozen before observation")
    if extreme == boundary:
        raise ValueError("breakout impulse has zero range")

    return CausalImpulseAnchor(
        rule_id="CONFIRMED_BREAKOUT_IMPULSE",
        start_price=boundary,
        start_time=breakout_time,
        end_price=extreme,
        end_time=extreme_time,
        confirmation_time=freeze_time,
    )
