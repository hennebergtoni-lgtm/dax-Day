"""Causal ATR / opening-range regime features for ATR001 research."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import numpy as np
import pandas as pd


@dataclass(frozen=True, slots=True)
class AtrObservation:
    atr_points: float
    observation_time: datetime
    period: int


@dataclass(frozen=True, slots=True)
class OrAtrFeature:
    or_points: float
    atr_points: float
    ratio: float
    atr_observation_time: datetime
    or_confirmation_time: datetime
    entry_time: datetime


def true_range(bars: pd.DataFrame) -> pd.Series:
    required = {"high", "low", "close"}
    missing = sorted(required - set(bars.columns))
    if missing:
        raise ValueError(f"ATR bars missing required columns: {missing}")
    high = pd.to_numeric(bars["high"], errors="coerce")
    low = pd.to_numeric(bars["low"], errors="coerce")
    close = pd.to_numeric(bars["close"], errors="coerce")
    prev_close = close.shift(1)
    return pd.concat(
        [(high - low), (high - prev_close).abs(), (low - prev_close).abs()],
        axis=1,
    ).max(axis=1)


def wilder_atr(bars: pd.DataFrame, period: int = 14) -> pd.Series:
    """Return ATR using true range and Wilder alpha=1/period smoothing."""
    if period <= 0:
        raise ValueError("ATR period must be positive")
    tr = true_range(bars)
    return tr.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()


def atr_before_entry(
    bars: pd.DataFrame,
    *,
    entry_time: datetime,
    time_col: str = "datetime",
    period: int = 14,
) -> AtrObservation:
    """Return the latest completed ATR observation strictly before entry."""
    if entry_time.tzinfo is None:
        raise ValueError("entry time must be timezone-aware")
    if time_col not in bars.columns:
        raise ValueError(f"ATR bars missing time column: {time_col}")
    work = bars.copy()
    times = pd.to_datetime(work[time_col], utc=True, errors="coerce")
    if times.isna().any():
        raise ValueError("ATR bars contain invalid timestamps")
    if times.duplicated().any() or not times.is_monotonic_increasing:
        raise ValueError("ATR bars must be unique and ordered")
    work[time_col] = times
    work["_atr"] = wilder_atr(work, period=period)
    entry = pd.Timestamp(entry_time).tz_convert("UTC")
    eligible = work.loc[work[time_col] < entry, [time_col, "_atr"]].dropna()
    if eligible.empty:
        raise ValueError("insufficient completed bars for ATR before entry")
    row = eligible.iloc[-1]
    value = float(row["_atr"])
    if not np.isfinite(value) or value <= 0:
        raise ValueError("ATR before entry must be finite and positive")
    return AtrObservation(
        atr_points=value,
        observation_time=pd.Timestamp(row[time_col]).to_pydatetime(),
        period=period,
    )


def build_or_atr_feature(
    *,
    or_high: float,
    or_low: float,
    or_confirmation_time: datetime,
    atr: AtrObservation,
    entry_time: datetime,
) -> OrAtrFeature:
    """Combine an already-completed OR with a causal pre-entry ATR observation."""
    for value, name in (
        (or_confirmation_time, "OR confirmation time"),
        (entry_time, "entry time"),
        (atr.observation_time, "ATR observation time"),
    ):
        if value.tzinfo is None:
            raise ValueError(f"{name} must be timezone-aware")
    if or_confirmation_time >= entry_time:
        raise ValueError("opening range must be complete before entry")
    if atr.observation_time >= entry_time:
        raise ValueError("ATR observation must be strictly before entry")
    or_points = float(or_high) - float(or_low)
    if not np.isfinite(or_points) or or_points <= 0:
        raise ValueError("opening range must be finite and positive")
    if not np.isfinite(atr.atr_points) or atr.atr_points <= 0:
        raise ValueError("ATR must be finite and positive")
    return OrAtrFeature(
        or_points=or_points,
        atr_points=float(atr.atr_points),
        ratio=float(or_points / atr.atr_points),
        atr_observation_time=atr.observation_time,
        or_confirmation_time=or_confirmation_time,
        entry_time=entry_time,
    )


def causal_hysteresis_regime(
    observations, *, decision_at, enter_threshold, exit_threshold,
    confirmation_observations, source_sha256,
):
    """Research-only hysteresis on explicitly available closed-bar features.

    Supports precomputed causal ADX/relative-volatility observations; does not
    infer provider finality or create another indicator/runtime regime engine.
    Equal-to-decision features are excluded. Parameters must be predeclared in
    the existing immutable trial registry; no candidate promotion occurs here.
    """
    from datetime import timezone
    import hashlib
    import json
    from math import isfinite
    import re

    def finite(value):
        try:
            return type(value) in (int, float) and isfinite(value)
        except OverflowError:
            return False

    if not isinstance(decision_at, datetime) or decision_at.tzinfo is None:
        raise ValueError("timezone-aware decision required")
    if not isinstance(source_sha256, str) or re.fullmatch(r"[0-9a-f]{64}", source_sha256) is None:
        raise ValueError("pinned source SHA256 required")
    if (not finite(enter_threshold) or not finite(exit_threshold)
            or enter_threshold <= exit_threshold or exit_threshold < 0):
        raise ValueError("finite nonnegative exit below enter required")
    if type(confirmation_observations) is not int or confirmation_observations < 1:
        raise ValueError("positive integer confirmation required")
    if not isinstance(observations, list):
        raise ValueError("ordered observation list required")
    previous = None
    eligible = []
    for row in observations:
        if not isinstance(row, dict) or set(row) != {"available_at", "value"}:
            raise ValueError("closed available-at feature schema required")
        time = row["available_at"]
        if not isinstance(time, datetime) or time.tzinfo is None:
            raise ValueError("timezone-aware feature availability required")
        if previous is not None and time <= previous:
            raise ValueError("unique increasing availability required")
        previous = time
        if time >= decision_at:
            continue
        value = row["value"]
        if not finite(value) or value < 0:
            raise ValueError("finite nonnegative available feature required")
        eligible.append({"available_at": time.astimezone(timezone.utc).isoformat(), "value": value})
    active = False
    confirmations = flips = 0
    trace = []
    for row in eligible:
        crossing = row["value"] <= exit_threshold if active else row["value"] >= enter_threshold
        confirmations = confirmations + 1 if crossing else 0
        flipped = confirmations >= confirmation_observations
        if flipped:
            active = not active
            confirmations = 0
            flips += 1
        trace.append(row | {"active": active, "flipped": flipped,
                            "pending_confirmations": confirmations})
    spec = {"source_sha256": source_sha256,
            "decision_at": decision_at.astimezone(timezone.utc).isoformat(),
            "enter_threshold": enter_threshold, "exit_threshold": exit_threshold,
            "confirmation_observations": confirmation_observations, "eligible": eligible}
    digest = hashlib.sha256(json.dumps(spec, sort_keys=True, separators=(",", ":"),
                                      allow_nan=False).encode()).hexdigest()
    return {"schema": "DAX_CAUSAL_HYSTERESIS_RESEARCH_V1", "identity_sha256": digest,
            "status": "AVAILABLE" if eligible else "INSUFFICIENT_SAMPLE",
            "active": active if eligible else None, "flip_count": flips, "trace": trace,
            "source_sha256": source_sha256,
            "availability_contract": "CALLER_PINNED_CLOSED_FEATURE_NOT_PROVIDER_FINALITY_PROOF",
            "hypothesis_validation": "NOT_TESTED_AGAINST_COSTED_OOS_LEDGER",
            "execution_capability": "NONE", "order_execution_enabled": False}
