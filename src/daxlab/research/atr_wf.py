"""Train-only ATR001 regime construction for canonical walk-forward windows."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import pandas as pd


@dataclass(frozen=True, slots=True)
class TrainOnlyRegimeBoundaries:
    wf: int
    train_start: object
    train_end: object
    atr_q33: float
    atr_q67: float
    or_atr_q33: float
    or_atr_q67: float
    train_rows: int

    def classify_atr(self, value: float) -> str:
        if value <= self.atr_q33:
            return "LOW"
        if value <= self.atr_q67:
            return "MID"
        return "HIGH"

    def classify_or_atr(self, value: float) -> str:
        if value <= self.or_atr_q33:
            return "LOW"
        if value <= self.or_atr_q67:
            return "MID"
        return "HIGH"


def _dates(values: Iterable[object]) -> set[object]:
    return {pd.Timestamp(value).date() for value in values}


def fit_train_only_regimes(
    features: pd.DataFrame,
    *,
    wf: int,
    train_days: Iterable[object],
) -> TrainOnlyRegimeBoundaries:
    """Fit coarse tertile regimes using training dates only.

    Full-sample thresholds are deliberately impossible here: callers must supply
    the exact training-day collection for one WF window.
    """
    required = {"date", "atr14_points", "or_atr_ratio", "feature_eligible"}
    missing = sorted(required - set(features.columns))
    if missing:
        raise ValueError(f"ATR001 regime features missing columns: {missing}")
    allowed_dates = _dates(train_days)
    if not allowed_dates:
        raise ValueError("ATR001 train_days cannot be empty")
    work = features.copy()
    work["_date"] = pd.to_datetime(work["date"], errors="coerce").dt.date
    train = work.loc[work["_date"].isin(allowed_dates) & work["feature_eligible"].astype(bool)]
    if train.empty:
        raise ValueError("ATR001 has no eligible training observations")
    if not set(train["_date"]).issubset(allowed_dates):
        raise AssertionError("ATR001 train-only boundary violated")
    atr = train["atr14_points"].astype(float)
    ratio = train["or_atr_ratio"].astype(float)
    return TrainOnlyRegimeBoundaries(
        wf=wf,
        train_start=min(allowed_dates),
        train_end=max(allowed_dates),
        atr_q33=float(atr.quantile(1 / 3)),
        atr_q67=float(atr.quantile(2 / 3)),
        or_atr_q33=float(ratio.quantile(1 / 3)),
        or_atr_q67=float(ratio.quantile(2 / 3)),
        train_rows=int(len(train)),
    )


def apply_frozen_regimes(
    features: pd.DataFrame,
    boundaries: TrainOnlyRegimeBoundaries,
    *,
    oos_days: Iterable[object],
) -> pd.DataFrame:
    """Apply already-fitted boundaries to OOS dates without refitting."""
    allowed_dates = _dates(oos_days)
    work = features.copy()
    work["_date"] = pd.to_datetime(work["date"], errors="coerce").dt.date
    oos = work.loc[work["_date"].isin(allowed_dates) & work["feature_eligible"].astype(bool)].copy()
    oos["atr_regime"] = oos["atr14_points"].astype(float).map(boundaries.classify_atr)
    oos["or_atr_regime"] = oos["or_atr_ratio"].astype(float).map(boundaries.classify_or_atr)
    oos["regime_fit_wf"] = boundaries.wf
    oos["regime_train_start"] = boundaries.train_start
    oos["regime_train_end"] = boundaries.train_end
    return oos.drop(columns=["_date"])
