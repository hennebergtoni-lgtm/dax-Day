"""Immutable metadata for the audited V11.2 reference baseline.

This module intentionally contains metadata/contracts only. The proven engine source must
be imported/reconstructed and parity-verified before it is exposed as executable V11.2.
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
    m1_candles: int = 172319
    m5_bars_per_day: int = 103
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
