"""Causal descriptive FIB001 feature bundle for frozen V11.2 trades."""
from __future__ import annotations

from zoneinfo import ZoneInfo

import pandas as pd

from daxlab.research.fibonacci_anchor import build_opening_range_anchor
from daxlab.research.fibonacci_retracement import (
    fixed_zone,
    normalized_retracement,
    validate_retracement_observation,
)

BERLIN = ZoneInfo("Europe/Berlin")


def build_fib001_trade_bundle(
    bars: pd.DataFrame,
    trades: pd.DataFrame,
    *,
    time_col: str = "datetime",
) -> pd.DataFrame:
    """Attach causal OR-anchor retracement diagnostics without filtering trades.

    The observation is the completed V11.2 confirmation bar: `retest_time` for
    retests, otherwise `signal_time`. The bundle is descriptive only and does not
    alter entry, exit, stop, target or trade eligibility.
    """
    bar_required = {time_col, "open", "high", "low", "close"}
    trade_required = {"entry_time", "signal_time", "retest_time", "entry_mode", "side", "orb_min"}
    missing_bars = sorted(bar_required - set(bars.columns))
    missing_trades = sorted(trade_required - set(trades.columns))
    if missing_bars:
        raise ValueError(f"FIB001 bars missing required columns: {missing_bars}")
    if missing_trades:
        raise ValueError(f"FIB001 trades missing required columns: {missing_trades}")

    bars_work = bars.copy()
    bars_work[time_col] = pd.to_datetime(bars_work[time_col], utc=True)
    bars_work["_berlin_date"] = bars_work[time_col].dt.tz_convert(BERLIN).dt.date
    close_lookup = bars_work.set_index(time_col)["close"]

    out = trades.copy()
    feature_rows: list[dict[str, object]] = []
    for trade in out.to_dict("records"):
        entry_time = pd.Timestamp(trade["entry_time"])
        entry_time = entry_time.tz_localize("UTC") if entry_time.tzinfo is None else entry_time.tz_convert("UTC")
        entry_mode = str(trade["entry_mode"])
        raw_observation = trade["retest_time"] if entry_mode == "retest" else trade["signal_time"]
        if pd.isna(raw_observation):
            raise ValueError("FIB001 confirmation observation time is missing")
        observation_time = pd.Timestamp(raw_observation)
        observation_time = (
            observation_time.tz_localize("UTC")
            if observation_time.tzinfo is None
            else observation_time.tz_convert("UTC")
        )
        if observation_time not in close_lookup.index:
            raise ValueError("FIB001 observation bar is missing from bars")

        entry_local = entry_time.tz_convert(BERLIN)
        orb_min = int(trade["orb_min"])
        if orb_min <= 0:
            raise ValueError("FIB001 orb_min must be positive")
        session_open = pd.Timestamp(
            year=entry_local.year,
            month=entry_local.month,
            day=entry_local.day,
            hour=9,
            minute=0,
            tz=BERLIN,
        )
        confirmation_time = session_open + pd.Timedelta(minutes=orb_min)
        day_bars = bars_work.loc[bars_work["_berlin_date"] == entry_local.date()]
        anchor = build_opening_range_anchor(
            day_bars,
            confirmation_time=confirmation_time.to_pydatetime(),
            direction=str(trade["side"]),
            time_col=time_col,
            bar_minutes=5,
        )
        validate_retracement_observation(
            anchor,
            observation_time=observation_time.to_pydatetime(),
            entry_time=entry_time.to_pydatetime(),
        )
        observation_price = float(close_lookup.loc[observation_time])
        depth = normalized_retracement(anchor.start_price, anchor.end_price, observation_price)
        feature_rows.append(
            {
                "fib_anchor_rule": anchor.rule_id,
                "fib_anchor_start_price": anchor.start_price,
                "fib_anchor_end_price": anchor.end_price,
                "fib_anchor_start_time": anchor.start_time,
                "fib_anchor_end_time": anchor.end_time,
                "fib_anchor_confirmation_time": anchor.confirmation_time,
                "fib_observation_time": observation_time,
                "fib_observation_price": observation_price,
                "fib_retracement_depth": depth,
                "fib_fixed_zone": fixed_zone(depth),
            }
        )

    features = pd.DataFrame(feature_rows, index=out.index)
    return pd.concat([out, features], axis=1)
