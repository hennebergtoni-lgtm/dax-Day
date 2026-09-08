from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class BollingerConfig:
    window: int = 20
    std_mult: float = 2.0
    min_position: float | None = None
    min_bandwidth: float | None = None
    bandwidth_quantile: float | None = None
    prior_range_atr_quantile: float | None = None
    htf_minutes: int | None = None
    htf_require_above_mid: bool = False


def add_bollinger_state(
    bars: pd.DataFrame,
    *,
    time_col: str = "datetime",
    close_col: str = "close",
    window: int = 20,
    std_mult: float = 2.0,
) -> pd.DataFrame:
    """Return chronological bars with causal Bollinger state on each completed bar.

    The returned state belongs to the bar itself. Entry-time alignment must therefore
    use :func:`align_last_completed_state` with ``allow_exact_matches=False`` when
    the entry happens at the next bar open.
    """
    if window < 2:
        raise ValueError("window must be >= 2")
    out = bars.copy().sort_values(time_col).reset_index(drop=True)
    close = pd.to_numeric(out[close_col], errors="raise").astype(float)
    out["bb_mid"] = close.rolling(window, min_periods=window).mean()
    out["bb_std"] = close.rolling(window, min_periods=window).std(ddof=0)
    out["bb_upper"] = out["bb_mid"] + std_mult * out["bb_std"]
    out["bb_lower"] = out["bb_mid"] - std_mult * out["bb_std"]
    width = out["bb_upper"] - out["bb_lower"]
    out["bb_bandwidth"] = width / out["bb_mid"]
    out["bb_position"] = np.where(width > 0, (close - out["bb_lower"]) / width, np.nan)
    return out


def align_last_completed_state(
    entries: pd.DataFrame,
    state: pd.DataFrame,
    *,
    entry_time_col: str = "entry_time",
    state_time_col: str = "datetime",
) -> pd.DataFrame:
    """Attach the last fully completed state strictly before entry time."""
    left = entries.copy()
    right = state.copy()
    left[entry_time_col] = pd.to_datetime(left[entry_time_col])
    right[state_time_col] = pd.to_datetime(right[state_time_col])
    left = left.sort_values(entry_time_col)
    right = right.sort_values(state_time_col)
    joined = pd.merge_asof(
        left,
        right,
        left_on=entry_time_col,
        right_on=state_time_col,
        direction="backward",
        allow_exact_matches=False,
        suffixes=("", "_state"),
    )
    bad = joined[state_time_col].notna() & (
        joined[state_time_col] >= joined[entry_time_col]
    )
    if bool(bad.any()):
        raise AssertionError("non-causal Bollinger alignment detected")
    return joined


def train_quantile(values: pd.Series, q: float) -> float:
    """Compute one threshold from training values only."""
    if not 0.0 <= q <= 1.0:
        raise ValueError("q must be within [0, 1]")
    clean = pd.to_numeric(values, errors="coerce").dropna()
    if clean.empty:
        raise ValueError("training values are empty")
    return float(clean.quantile(q))


def prior_range_atr(
    daily: pd.DataFrame,
    *,
    date_col: str = "date",
    high_col: str = "high",
    low_col: str = "low",
    atr_days: int = 14,
) -> pd.DataFrame:
    """Build prior-day range / prior-only ATR context without future leakage."""
    if atr_days < 2:
        raise ValueError("atr_days must be >= 2")
    d = daily.copy().sort_values(date_col).reset_index(drop=True)
    d["day_range"] = pd.to_numeric(d[high_col], errors="raise") - pd.to_numeric(
        d[low_col], errors="raise"
    )
    d["prev_range"] = d["day_range"].shift(1)
    d["atr"] = d["day_range"].shift(1).rolling(atr_days, min_periods=atr_days).mean()
    d["prev_range_atr"] = d["prev_range"] / d["atr"]
    return d


def resample_completed_htf(
    bars: pd.DataFrame,
    *,
    time_col: str = "datetime",
    close_col: str = "close",
    minutes: int = 15,
    window: int = 20,
    std_mult: float = 2.0,
) -> pd.DataFrame:
    """Build HTF BB state timestamped only when the higher-timeframe bar is known."""
    if minutes <= 0 or minutes % 5:
        raise ValueError("minutes must be a positive multiple of 5")
    d = bars.copy().sort_values(time_col)
    d[time_col] = pd.to_datetime(d[time_col])
    d["_block"] = d[time_col].dt.floor(f"{minutes}min")
    htf = (
        d.groupby("_block", as_index=False)
        .agg(**{close_col: (close_col, "last")})
        .rename(columns={"_block": "block_start"})
    )
    htf["known_time"] = htf["block_start"] + pd.Timedelta(minutes=minutes)
    htf = add_bollinger_state(
        htf.rename(columns={"known_time": time_col}),
        time_col=time_col,
        close_col=close_col,
        window=window,
        std_mult=std_mult,
    )
    return htf


def filter_trades(
    trades: pd.DataFrame,
    *,
    config: BollingerConfig,
    bandwidth_col: str = "bb_bandwidth",
    position_col: str = "bb_position",
    prior_range_atr_col: str = "prev_range_atr",
    bandwidth_threshold: float | None = None,
    prior_range_atr_cap: float | None = None,
) -> pd.Series:
    """Return a boolean eligibility mask for a modular BB/context filter."""
    mask = pd.Series(True, index=trades.index)

    if config.min_position is not None:
        mask &= trades[position_col] >= config.min_position

    threshold = config.min_bandwidth if config.min_bandwidth is not None else bandwidth_threshold
    if threshold is not None:
        mask &= trades[bandwidth_col] > threshold

    if prior_range_atr_cap is not None:
        mask &= trades[prior_range_atr_col] <= prior_range_atr_cap

    return mask.fillna(False)
