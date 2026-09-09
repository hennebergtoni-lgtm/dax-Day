from datetime import datetime, timezone

import pytest

from daxlab.research.v12_evidence_gate import (
    OhlcEvidenceIdentity,
    REPRODUCED_TRADE_PROVENANCE,
    REPRODUCED_TRADES_SHA256,
    TradeEvidenceIdentity,
    VERIFIED_DATASET_SHA256,
)
from daxlab.research.v12_trade_feature_bundle import (
    ReproducedTrade,
    TimedClosedBar,
    breakout_side_close_location,
    build_trade_feature_bundle,
    last_completed_bar_index,
    signal_bar_index,
)


def _trade_identity() -> TradeEvidenceIdentity:
    return TradeEvidenceIdentity(856, REPRODUCED_TRADES_SHA256, REPRODUCED_TRADE_PROVENANCE)


def _verified_ohlc_identity() -> OhlcEvidenceIdentity:
    return OhlcEvidenceIdentity(172_319, 1_673, VERIFIED_DATASET_SHA256)


def _bar(time: datetime, base: float = 100.0) -> TimedClosedBar:
    return TimedClosedBar(time, base, base + 1.0, base - 1.0, base + 0.5)


def test_bundle_rejects_actual_sequence_length_drift() -> None:
    bars = (_bar(datetime(2019, 1, 2, 9, 0, tzinfo=timezone.utc)),)
    with pytest.raises(ValueError, match="sequence length"):
        build_trade_feature_bundle(
            bars,
            (),
            ohlc_identity=_verified_ohlc_identity(),
            trade_identity=_trade_identity(),
        )


def test_bundle_rejects_unverified_metadata_before_feature_use() -> None:
    bars = (_bar(datetime(2019, 1, 2, 9, 0, tzinfo=timezone.utc)),)
    bad = OhlcEvidenceIdentity(172_319, 1_673, "0" * 64)
    with pytest.raises(ValueError, match="fingerprint"):
        build_trade_feature_bundle(
            bars,
            (),
            ohlc_identity=bad,
            trade_identity=_trade_identity(),
        )


def test_last_completed_bar_index_excludes_in_progress_m5_bar() -> None:
    times = [
        datetime(2019, 1, 2, 9, 0, tzinfo=timezone.utc),
        datetime(2019, 1, 2, 9, 5, tzinfo=timezone.utc),
    ]
    with pytest.raises(ValueError, match="no completed"):
        last_completed_bar_index(
            times,
            entry_time=datetime(2019, 1, 2, 9, 4, 59, tzinfo=timezone.utc),
        )
    assert last_completed_bar_index(
        times,
        entry_time=datetime(2019, 1, 2, 9, 5, 0, tzinfo=timezone.utc),
    ) == 0
    assert last_completed_bar_index(
        times,
        entry_time=datetime(2019, 1, 2, 9, 10, 0, tzinfo=timezone.utc),
    ) == 1


def test_signal_bar_index_requires_exact_completed_signal_bar() -> None:
    t0 = datetime(2019, 1, 2, 9, 0, tzinfo=timezone.utc)
    t1 = datetime(2019, 1, 2, 9, 5, tzinfo=timezone.utc)
    index_by_time = {t0: 0, t1: 1}

    assert signal_bar_index(index_by_time, signal_time=t0, entry_time=t1) == 0
    with pytest.raises(ValueError, match="does not map"):
        signal_bar_index(
            index_by_time,
            signal_time=datetime(2019, 1, 2, 9, 10, tzinfo=timezone.utc),
            entry_time=datetime(2019, 1, 2, 9, 15, tzinfo=timezone.utc),
        )
    with pytest.raises(ValueError, match="not fully closed"):
        signal_bar_index(
            index_by_time,
            signal_time=t0,
            entry_time=datetime(2019, 1, 2, 9, 4, 59, tzinfo=timezone.utc),
        )


def test_breakout_side_close_location_mirrors_short() -> None:
    assert breakout_side_close_location(close_location=0.8, side="long") == pytest.approx(0.8)
    assert breakout_side_close_location(close_location=0.8, side="short") == pytest.approx(0.2)
    with pytest.raises(ValueError, match="unsupported side"):
        breakout_side_close_location(close_location=0.8, side="other")
    with pytest.raises(ValueError, match="outside"):
        breakout_side_close_location(close_location=1.1, side="long")


def test_timed_bar_rejects_naive_timestamp_and_invalid_ohlc() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        _bar(datetime(2019, 1, 2, 9, 0))
    with pytest.raises(ValueError, match="invalid OHLC"):
        TimedClosedBar(
            datetime(2019, 1, 2, 9, 0, tzinfo=timezone.utc),
            100.0,
            99.0,
            98.0,
            100.0,
        )


def test_reproduced_trade_requires_valid_timestamp_mode_and_side_contract() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        ReproducedTrade(
            1,
            datetime(2019, 1, 2, 9, 10),
            datetime(2019, 1, 2, 9, 0),
            None,
            "breakout",
            "long",
            1.0,
        )
    with pytest.raises(ValueError, match="unsupported entry_mode"):
        ReproducedTrade(
            1,
            datetime(2019, 1, 2, 9, 10, tzinfo=timezone.utc),
            datetime(2019, 1, 2, 9, 0, tzinfo=timezone.utc),
            None,
            "other",
            "long",
            1.0,
        )
    with pytest.raises(ValueError, match="unsupported side"):
        ReproducedTrade(
            1,
            datetime(2019, 1, 2, 9, 10, tzinfo=timezone.utc),
            datetime(2019, 1, 2, 9, 0, tzinfo=timezone.utc),
            None,
            "breakout",
            "other",
            1.0,
        )
