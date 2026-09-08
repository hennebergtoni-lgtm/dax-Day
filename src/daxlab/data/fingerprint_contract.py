"""Versioned contracts for dataset fingerprint provenance."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FingerprintMethod:
    method_id: str
    columns: tuple[str, ...]
    index_encoding: str
    serialization: str
    float_format: str
    text_encoding: str
    digest: str


V1_OHLC_CSV_SHA256 = FingerprintMethod(
    method_id="DAXLAB_OHLC_CSV_SHA256_V1",
    columns=("open", "high", "low", "close"),
    index_encoding="pandas_datetime_index_int64_nanoseconds",
    serialization="pandas.to_csv(index=True,header=True)",
    float_format="%.10f",
    text_encoding="utf-8",
    digest="sha256",
)


def assert_known_fingerprint_method(method_id: str) -> FingerprintMethod:
    """Return the immutable method contract or reject an unknown method."""
    if method_id != V1_OHLC_CSV_SHA256.method_id:
        raise ValueError(f"unknown fingerprint method: {method_id}")
    return V1_OHLC_CSV_SHA256
