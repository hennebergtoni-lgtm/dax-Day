"""Immutable metadata for the audited V11.2 reference baseline.

This module contains the frozen research contracts and cryptographic references. The
recovered executable engine is loaded separately through a strict SHA-256 gate.
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
    positive_wfs: int = 36
    negative_wfs: int = 45
    flat_wfs: int = 0
    oos_trades: int = 1384
    oos_return_r: float = -68.1095
    exact_engine_sha256: str = (
        "9561b9089c57c543798dc587ce240a729b7995230dd5d665a1bdd029f3990887"
    )


V11_2 = V112Reference()


def assert_reference_invariants() -> None:
    assert V11_2.positive_wfs + V11_2.negative_wfs + V11_2.flat_wfs == V11_2.walk_forwards
    assert V11_2.train_days == 45 and V11_2.oos_days == 20 and V11_2.step_days == 20
    assert V11_2.variants == 144
    assert V11_2.valid_session_days == 1673
    assert V11_2.raw_m5_rows == 1673 * 288
    assert V11_2.m5_session_bars == 1673 * 103
