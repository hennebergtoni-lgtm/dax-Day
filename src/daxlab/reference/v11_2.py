"""Immutable metadata for the audited V11.2 active reference.

Legacy V4.0-FIX1 measurements are deliberately named separately so they cannot
silently become active-reference targets again.
"""
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class V112Reference:
    research_start: str = "2014-01-01"
    research_end: str = "2019-12-31"
    timezone: str = "Europe/Berlin"
    session_start: str = "09:00"
    session_end: str = "17:30"
    valid_session_days: int = 1673
    raw_m5_rows: int = 481824
    m5_session_bars: int = 172319
    m5_bars_per_day: int = 103
    dataset_session_ohlc_sha256: str = (
        "e51bba6cb2befe5e7eb0376318e43b096a3e2ecaae3f556019862975c60286a2"
    )
    dataset_zip_sha256: str = (
        "c46c09a391ee83a19a117fb43628cb75ab0a75703701ed7a84731d2963b24870"
    )
    variants: int = 144
    walk_forwards: int = 81
    train_days: int = 45
    oos_days: int = 20
    step_days: int = 20
    positive_wfs: int = 37
    negative_wfs: int = 44
    flat_wfs: int = 0
    oos_trades: int = 856
    oos_return_r: float = -31.309210619787684
    exact_engine_source_sha256: str = (
        "b3d62e0cad72420d36ade523857d024d4a334298be51a8313069e36614bda888"
    )
    oracle_engine_source_sha256: str = (
        "62adde1ccd630d01e9500b20c0efa88a0a8bd277e74c1a2c932ec6fc6efd3a0f"
    )
    legacy_oos_trades: int = 1384
    legacy_oos_return_r: float = -68.10950257808015
    legacy_positive_wfs: int = 36
    legacy_negative_wfs: int = 45


V11_2 = V112Reference()


def assert_reference_invariants() -> None:
    assert V11_2.positive_wfs + V11_2.negative_wfs + V11_2.flat_wfs == V11_2.walk_forwards
    assert V11_2.train_days == 45 and V11_2.oos_days == 20 and V11_2.step_days == 20
    assert V11_2.variants == 144
    assert V11_2.valid_session_days == 1673
    assert V11_2.raw_m5_rows == 1673 * 288
    assert V11_2.m5_session_bars == 1673 * 103
    assert V11_2.oos_trades == 856
    assert V11_2.legacy_oos_trades == 1384
