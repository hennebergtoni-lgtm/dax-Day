"""Deterministic fingerprints for audited research datasets."""

from __future__ import annotations

import hashlib

import pandas as pd

from daxlab.data.validation import REQUIRED_OHLC, validate_ohlc


def fingerprint_ohlc(df: pd.DataFrame) -> str:
    """Return a SHA-256 fingerprint over timestamps and OHLC values.

    Invalid candle data cannot receive a research fingerprint.
    """
    report = validate_ohlc(df)
    if not report.valid:
        raise ValueError(f"cannot fingerprint invalid market data: {report}")

    normalized = df.loc[:, REQUIRED_OHLC].copy()
    normalized.index = normalized.index.astype("int64")
    payload = normalized.to_csv(index=True, header=True, float_format="%.10f").encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
