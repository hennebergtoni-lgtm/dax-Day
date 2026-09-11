"""Deterministic forward-session structure derived from closed M5 bars.

The analyzer is read-only. It derives session and opening-range structure from
canonical closed bars and never submits orders or reads broker balances.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
import math
from zoneinfo import ZoneInfo

import pandas as pd


BERLIN = ZoneInfo("Europe/Berlin")
SESSION_START = time(9, 0)
SESSION_END = time(17, 30)
OR_MINUTES = (5, 15)
_REQUIRED_COLUMNS = ("open_time", "open", "high", "low", "close")


@dataclass(frozen=True)
class OpeningRangeStructure:
    minutes: int
    required_bars: int
    observed_bars: int
    complete: bool
    high: float | None
    low: float | None
    first_high_break_time: str | None
    first_low_break_time: str | None
    latest_close_inside: bool | None

    def to_payload(self) -> dict[str, object]:
        return {
            "minutes": self.minutes,
            "required_bars": self.required_bars,
            "observed_bars": self.observed_bars,
            "complete": self.complete,
            "high": self.high,
            "low": self.low,
            "first_high_break_time": self.first_high_break_time,
            "first_low_break_time": self.first_low_break_time,
            "latest_close_inside": self.latest_close_inside,
        }


@dataclass(frozen=True)
class ForwardSessionStructure:
    session_date: str
    timezone: str
    session_bars: int
    session_high: float
    session_low: float
    latest_bar_time: str
    latest_close: float
    or5: OpeningRangeStructure
    or15: OpeningRangeStructure
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def to_payload(self) -> dict[str, object]:
        return {
            "schema_version": "DAXLAB_FORWARD_SESSION_STRUCTURE_V1",
            "session_date": self.session_date,
            "timezone": self.timezone,
            "session_bars": self.session_bars,
            "session_high": self.session_high,
            "session_low": self.session_low,
            "latest_bar_time": self.latest_bar_time,
            "latest_close": self.latest_close,
            "or5": self.or5.to_payload(),
            "or15": self.or15.to_payload(),
            "execution_capability": self.execution_capability,
            "order_execution_enabled": self.order_execution_enabled,
        }


def _iso_local(value: pd.Timestamp) -> str:
    return value.isoformat()


def _validated_bars(bars: pd.DataFrame) -> pd.DataFrame:
    missing = [column for column in _REQUIRED_COLUMNS if column not in bars.columns]
    if missing:
        raise ValueError(f"missing required columns: {missing}")
    if bars.empty:
        raise ValueError("at least one closed M5 bar is required")

    frame = bars.loc[:, _REQUIRED_COLUMNS].copy()
    frame["open_time"] = pd.to_datetime(frame["open_time"], utc=True, errors="raise")
    if frame["open_time"].isna().any():
        raise ValueError("open_time cannot contain NaT")
    if frame["open_time"].duplicated().any():
        raise ValueError("open_time values must be unique")

    for column in ("open", "high", "low", "close"):
        frame[column] = pd.to_numeric(frame[column], errors="raise")
        if not frame[column].map(lambda value: math.isfinite(float(value))).all():
            raise ValueError(f"{column} values must be finite")

    invalid_ohlc = (
        (frame["high"] < frame[["open", "close"]].max(axis=1))
        | (frame["low"] > frame[["open", "close"]].min(axis=1))
        | (frame["high"] < frame["low"])
    )
    if invalid_ohlc.any():
        raise ValueError("invalid OHLC relationship")

    local = frame["open_time"].dt.tz_convert(BERLIN)
    if ((local.dt.minute % 5) != 0).any() or (local.dt.second != 0).any():
        raise ValueError("open_time values must align to M5 boundaries")
    frame["local_time"] = local
    return frame.sort_values("open_time", kind="stable").reset_index(drop=True)


def _resolve_session_date(frame: pd.DataFrame, session_date: str | date | None) -> date:
    if session_date is not None:
        return date.fromisoformat(session_date) if isinstance(session_date, str) else session_date
    dates = tuple(sorted({stamp.date() for stamp in frame["local_time"]}))
    if len(dates) != 1:
        raise ValueError("session_date is required when bars span multiple Berlin dates")
    return dates[0]


def _opening_range(session: pd.DataFrame, session_day: date, minutes: int) -> OpeningRangeStructure:
    start = pd.Timestamp(datetime.combine(session_day, SESSION_START), tz=BERLIN)
    end = start + timedelta(minutes=minutes)
    required_bars = max(1, minutes // 5)
    expected_times = tuple(start + timedelta(minutes=5 * index) for index in range(required_bars))
    opening = session[session["local_time"].isin(expected_times)]
    observed_bars = len(opening)
    complete = observed_bars == required_bars

    if not complete:
        return OpeningRangeStructure(
            minutes=minutes,
            required_bars=required_bars,
            observed_bars=observed_bars,
            complete=False,
            high=None,
            low=None,
            first_high_break_time=None,
            first_low_break_time=None,
            latest_close_inside=None,
        )

    high = float(opening["high"].max())
    low = float(opening["low"].min())
    after = session[session["local_time"] >= end]
    high_breaks = after[after["high"] > high]
    low_breaks = after[after["low"] < low]
    latest_close = float(session.iloc[-1]["close"])

    return OpeningRangeStructure(
        minutes=minutes,
        required_bars=required_bars,
        observed_bars=observed_bars,
        complete=True,
        high=high,
        low=low,
        first_high_break_time=(
            None if high_breaks.empty else _iso_local(high_breaks.iloc[0]["local_time"])
        ),
        first_low_break_time=(
            None if low_breaks.empty else _iso_local(low_breaks.iloc[0]["local_time"])
        ),
        latest_close_inside=low <= latest_close <= high,
    )


def analyze_forward_session_structure(
    bars: pd.DataFrame,
    *,
    session_date: str | date | None = None,
) -> ForwardSessionStructure:
    """Derive V11.2-compatible OR5/OR15 structure from canonical closed M5 bars."""
    frame = _validated_bars(bars)
    session_day = _resolve_session_date(frame, session_date)
    start = pd.Timestamp(datetime.combine(session_day, SESSION_START), tz=BERLIN)
    end = pd.Timestamp(datetime.combine(session_day, SESSION_END), tz=BERLIN)
    session = frame[(frame["local_time"] >= start) & (frame["local_time"] <= end)]
    if session.empty:
        raise ValueError("no Berlin-session bars available for session_date")

    latest = session.iloc[-1]
    or5 = _opening_range(session, session_day, OR_MINUTES[0])
    or15 = _opening_range(session, session_day, OR_MINUTES[1])
    return ForwardSessionStructure(
        session_date=session_day.isoformat(),
        timezone=str(BERLIN),
        session_bars=len(session),
        session_high=float(session["high"].max()),
        session_low=float(session["low"].min()),
        latest_bar_time=_iso_local(latest["local_time"]),
        latest_close=float(latest["close"]),
        or5=or5,
        or15=or15,
    )
