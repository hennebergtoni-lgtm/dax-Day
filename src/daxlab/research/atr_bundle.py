"""Descriptive ATR001 feature bundle for reproduced V11.2 trades."""
from __future__ import annotations

from dataclasses import asdict
from datetime import timedelta

import pandas as pd

from daxlab.research.atr_regime import atr_before_entry, build_or_atr_feature


def build_atr001_bundle(
    bars: pd.DataFrame,
    trades: pd.DataFrame,
    *,
    period: int = 14,
) -> pd.DataFrame:
    """Attach causal ATR14 and OR/ATR context to an existing trade ledger.

    The function is descriptive only: it never filters, ranks or mutates trades.
    Input bar timestamps are interpreted as M5 bar-open timestamps, matching the
    audited DAX dataset. ATR observations are therefore shifted to bar-close time
    before the strict pre-entry cutoff is applied.
    """
    required_trade = {
        "wf", "date", "entry_time", "orb_min", "entry_mode", "side", "r",
    }
    missing = sorted(required_trade - set(trades.columns))
    if missing:
        raise ValueError(f"ATR001 trades missing required columns: {missing}")
    required_bar = {"datetime", "open", "high", "low", "close"}
    missing_bars = sorted(required_bar - set(bars.columns))
    if missing_bars:
        raise ValueError(f"ATR001 bars missing required columns: {missing_bars}")

    work = bars.copy()
    work["datetime"] = pd.to_datetime(work["datetime"], utc=True, errors="coerce")
    if work["datetime"].isna().any():
        raise ValueError("ATR001 bars contain invalid timestamps")
    if work["datetime"].duplicated().any() or not work["datetime"].is_monotonic_increasing:
        raise ValueError("ATR001 bars must be unique and ordered")
    # atr_before_entry treats the time column as observation time. For audited
    # M5 data the stored timestamp is bar open, so expose the completed-bar time.
    atr_bars = work.copy()
    atr_bars["datetime"] = atr_bars["datetime"] + timedelta(minutes=5)

    rows: list[dict[str, object]] = []
    for trade in trades.to_dict("records"):
        base = {key: trade[key] for key in required_trade}
        entry = pd.Timestamp(trade["entry_time"])
        if entry.tzinfo is None:
            rows.append({**base, "feature_eligible": False, "rejection_reason": "NAIVE_ENTRY_TIME"})
            continue
        entry = entry.tz_convert("UTC")
        orb_min = int(trade["orb_min"])
        local_date = pd.Timestamp(trade["date"]).date()
        # Berlin session opens at 09:00 local; audited UTC bars encode DST.
        day = work.loc[work["datetime"].dt.tz_convert("Europe/Berlin").dt.date == local_date]
        if day.empty:
            rows.append({**base, "feature_eligible": False, "rejection_reason": "MISSING_SESSION"})
            continue
        session = day.loc[day["datetime"].dt.tz_convert("Europe/Berlin").dt.time >= pd.Timestamp("09:00").time()]
        or_bars = session.iloc[: max(1, orb_min // 5)]
        if len(or_bars) != orb_min // 5:
            rows.append({**base, "feature_eligible": False, "rejection_reason": "INCOMPLETE_OR"})
            continue
        or_confirmation = pd.Timestamp(or_bars.iloc[-1]["datetime"]) + timedelta(minutes=5)
        try:
            atr = atr_before_entry(atr_bars, entry_time=entry.to_pydatetime(), period=period)
            feature = build_or_atr_feature(
                or_high=float(or_bars["high"].max()),
                or_low=float(or_bars["low"].min()),
                or_confirmation_time=or_confirmation.to_pydatetime(),
                atr=atr,
                entry_time=entry.to_pydatetime(),
            )
        except ValueError as exc:
            rows.append({**base, "feature_eligible": False, "rejection_reason": str(exc)})
            continue
        rows.append(
            {
                **base,
                **asdict(feature),
                "atr14_points": feature.atr_points,
                "or_atr_ratio": feature.ratio,
                "feature_eligible": True,
                "rejection_reason": None,
            }
        )
    return pd.DataFrame(rows)
