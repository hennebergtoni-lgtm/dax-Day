"""Strict market-data contracts for reproducible DAX research."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


REQUIRED_OHLC = ("open", "high", "low", "close")


@dataclass(frozen=True, slots=True)
class DataValidationReport:
    rows: int
    duplicate_timestamps: int
    missing_ohlc: int
    ohlc_errors: int
    monotonic_index: bool

    @property
    def valid(self) -> bool:
        return (
            self.rows > 0
            and self.duplicate_timestamps == 0
            and self.missing_ohlc == 0
            and self.ohlc_errors == 0
            and self.monotonic_index
        )


def validate_ohlc(df: pd.DataFrame) -> DataValidationReport:
    """Validate the minimum candle invariants without mutating input data."""
    missing_columns = [column for column in REQUIRED_OHLC if column not in df.columns]
    if missing_columns:
        raise ValueError(f"missing required OHLC columns: {missing_columns}")
    if not isinstance(df.index, pd.DatetimeIndex):
        raise TypeError("market data index must be a pandas.DatetimeIndex")

    ohlc = df.loc[:, REQUIRED_OHLC]
    missing_ohlc = int(ohlc.isna().sum().sum())
    duplicate_timestamps = int(df.index.duplicated().sum())

    high_invalid = (ohlc["high"] < ohlc[["open", "close", "low"]].max(axis=1)).sum()
    low_invalid = (ohlc["low"] > ohlc[["open", "close", "high"]].min(axis=1)).sum()

    return DataValidationReport(
        rows=len(df),
        duplicate_timestamps=duplicate_timestamps,
        missing_ohlc=missing_ohlc,
        ohlc_errors=int(high_invalid + low_invalid),
        monotonic_index=bool(df.index.is_monotonic_increasing),
    )
