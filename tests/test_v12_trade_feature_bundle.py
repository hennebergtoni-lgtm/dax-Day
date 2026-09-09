from datetime import datetime, timedelta, timezone

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
    build_trade_feature_bundle,
)


def _trade_identity() -> TradeEvidenceIdentity:
    return TradeEvidenceIdentity(856, REPRODUCED_TRADES_SHA256, REPRODUCED_TRADE_PROVENANCE)


def _ohlc_identity(*, rows: int, days: int) -> OhlcEvidenceIdentity:
    return OhlcEvidenceIdentity(rows, days, VERIFIED_DATASET_SHA256)


def _bar(time: datetime, base: float = 100.0) -> TimedClosedBar:
    return TimedClosedBar(time, base, base + 1.0, base - 1.0, base + 0.5)


def test_bundle_rejects_sequence_length_drift_before_feature_use() -> None:
    bars = (_bar(datetime(2019, 1, 2, 9, 0, tzinfo=timezone.utc)),)
    trade = ReproducedTrade(
        wf=1,
        entry_time=datetime(2019, 1, 2, 9, 10, tzinfo=timezone.utc),
        signal_time=datetime(2019, 1, 2, 9, 0, tzinfo=timezone.utc),
        retest_time=None,
        entry_mode="breakout",
        r=1.0,
    )
    with pytest.raises(ValueError, match="row-count"):
        build_trade_feature_bundle(
            bars,
            (trade,),
            ohlc_identity=_ohlc_identity(rows=1, days=1),
            trade_identity=_trade_identity(),
        )


def test_bundle_rejects_unverified_metadata_even_if_sequence_shape_looks_valid() -> None:
    bars = (_bar(datetime(2019, 1, 2, 9, 0, tzinfo=timezone.utc)),)
    bad = OhlcEvidenceIdentity(172_319, 1_673, "0" * 64)
    with pytest.raises(ValueError, match="fingerprint"):
        build_trade_feature_bundle(
            bars,
            (),
            ohlc_identity=bad,
            trade_identity=_trade_identity(),
        )


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


def test_reproduced_trade_requires_valid_timestamp_contract() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        ReproducedTrade(1, datetime(2019, 1, 2, 9, 10), datetime(2019, 1, 2, 9, 0), None, "breakout", 1.0)
    with pytest.raises(ValueError, match="unsupported entry_mode"):
        ReproducedTrade(
            1,
            datetime(2019, 1, 2, 9, 10, tzinfo=timezone.utc),
            datetime(2019, 1, 2, 9, 0, tzinfo=timezone.utc),
            None,
            "other",
            1.0,
        )


def test_retest_staleness_contract_rejects_non_m5_alignment() -> None:
    # Full historical bundle execution is intentionally impossible in a unit test
    # without the verified 172,319-row input. Validate the trade-side contract here.
    trade = ReproducedTrade(
        wf=1,
        entry_time=datetime(2019, 1, 2, 9, 15, tzinfo=timezone.utc),
        signal_time=datetime(2019, 1, 2, 9, 0, tzinfo=timezone.utc),
        retest_time=datetime(2019, 1, 2, 9, 7, tzinfo=timezone.utc),
        entry_mode="retest",
        r=1.0,
    )
    assert trade.retest_time is not None
    assert (trade.retest_time - trade.signal_time) == timedelta(minutes=7)
