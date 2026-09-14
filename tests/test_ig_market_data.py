from __future__ import annotations

from datetime import datetime, timezone

import pytest

from daxlab.adapters.ig_market_data import IgClosedM5CandleSource, IgClosedM5Feed
from daxlab.domain.market import InstrumentId


EPIC = "IX.D.DAX.IFMM.IP"
INSTRUMENT = InstrumentId("DAX_CFD_IG_DE40_CASH_1EUR")


def _row(
    snapshot: str,
    *,
    open_bid: float = 25_500.0,
    volume: float | None = 42.0,
) -> dict[str, object]:
    return {
        "snapshotTimeUTC": snapshot,
        "openPrice": {"bid": open_bid, "ask": open_bid + 2.0, "lastTraded": None},
        "highPrice": {"bid": open_bid + 10.0, "ask": open_bid + 12.0, "lastTraded": None},
        "lowPrice": {"bid": open_bid - 5.0, "ask": open_bid - 3.0, "lastTraded": None},
        "closePrice": {"bid": open_bid + 4.0, "ask": open_bid + 6.0, "lastTraded": None},
        "lastTradedVolume": volume,
    }


def _feed(*rows: dict[str, object]) -> IgClosedM5Feed:
    return IgClosedM5Feed(
        epic=EPIC,
        observed_at=datetime(2026, 9, 14, 10, 10, tzinfo=timezone.utc),
        prices=rows,
    )


def test_ig_source_maps_bid_ask_midpoint_without_fabricating_last_traded() -> None:
    source = IgClosedM5CandleSource(
        feed_provider=lambda: _feed(_row("2026-09-14T10:00:00")),
        epic=EPIC,
        instrument_id=INSTRUMENT,
    )

    candle = source.next_candle()

    assert candle is not None
    assert candle.instrument_id == INSTRUMENT
    assert candle.timeframe == "M5"
    assert candle.event_time == datetime(2026, 9, 14, 10, 0, tzinfo=timezone.utc)
    assert candle.close_time == datetime(2026, 9, 14, 10, 5, tzinfo=timezone.utc)
    assert candle.open == 25_501.0
    assert candle.high == 25_511.0
    assert candle.low == 25_496.0
    assert candle.close == 25_505.0
    assert candle.volume == 42.0
    assert candle.source == f"IG_READ_ONLY:{EPIC}:MID_BID_ASK"
    assert candle.is_closed is True
    assert candle.safe_for_decision is True


def test_ig_source_emits_chronological_rows_at_most_once() -> None:
    feed = _feed(
        _row("2026-09-14T10:00:00"),
        _row("2026-09-14T10:05:00", open_bid=25_510.0),
    )
    source = IgClosedM5CandleSource(
        feed_provider=lambda: feed,
        epic=EPIC,
        instrument_id=INSTRUMENT,
    )

    first = source.next_candle()
    second = source.next_candle()
    third = source.next_candle()

    assert first is not None and second is not None
    assert first.event_time < second.event_time
    assert third is None
    assert source.last_close_time == second.close_time


def test_ig_source_preserves_missing_volume_as_none() -> None:
    source = IgClosedM5CandleSource(
        feed_provider=lambda: _feed(_row("2026-09-14T10:00:00", volume=None)),
        epic=EPIC,
        instrument_id=INSTRUMENT,
    )

    candle = source.next_candle()

    assert candle is not None
    assert candle.volume is None


def test_ig_source_rejects_epic_mismatch() -> None:
    source = IgClosedM5CandleSource(
        feed_provider=lambda: IgClosedM5Feed(
            epic="WRONG.EPIC",
            observed_at=datetime(2026, 9, 14, 10, 10, tzinfo=timezone.utc),
            prices=(_row("2026-09-14T10:00:00"),),
        ),
        epic=EPIC,
        instrument_id=INSTRUMENT,
    )

    with pytest.raises(ValueError, match="epic does not match"):
        source.next_candle()


def test_ig_source_rejects_missing_bid_ask_evidence() -> None:
    row = _row("2026-09-14T10:00:00")
    row["closePrice"] = {"bid": 25_504.0, "lastTraded": None}
    source = IgClosedM5CandleSource(
        feed_provider=lambda: _feed(row),
        epic=EPIC,
        instrument_id=INSTRUMENT,
    )

    with pytest.raises(ValueError, match="closePrice.ask must be numeric"):
        source.next_candle()


def test_ig_source_rejects_open_or_future_bar() -> None:
    source = IgClosedM5CandleSource(
        feed_provider=lambda: IgClosedM5Feed(
            epic=EPIC,
            observed_at=datetime(2026, 9, 14, 10, 4, 59, tzinfo=timezone.utc),
            prices=(_row("2026-09-14T10:00:00"),),
        ),
        epic=EPIC,
        instrument_id=INSTRUMENT,
    )

    with pytest.raises(ValueError, match="closed M5 bars only"):
        source.next_candle()


def test_ig_source_rejects_duplicate_or_out_of_order_rows() -> None:
    duplicate = _feed(
        _row("2026-09-14T10:00:00"),
        _row("2026-09-14T10:00:00", open_bid=25_510.0),
    )
    source = IgClosedM5CandleSource(
        feed_provider=lambda: duplicate,
        epic=EPIC,
        instrument_id=INSTRUMENT,
    )

    with pytest.raises(ValueError, match="timestamps must remain unique"):
        source.next_candle()


def test_ig_source_rejects_m5_continuity_gap() -> None:
    gap = _feed(
        _row("2026-09-14T09:55:00"),
        _row("2026-09-14T10:05:00", open_bid=25_510.0),
    )
    source = IgClosedM5CandleSource(
        feed_provider=lambda: gap,
        epic=EPIC,
        instrument_id=INSTRUMENT,
    )

    with pytest.raises(ValueError, match="continuous M5 bars"):
        source.next_candle()


def test_ig_source_rejects_crossed_bid_ask() -> None:
    row = _row("2026-09-14T10:00:00")
    row["openPrice"] = {"bid": 25_502.0, "ask": 25_501.0, "lastTraded": None}
    source = IgClosedM5CandleSource(
        feed_provider=lambda: _feed(row),
        epic=EPIC,
        instrument_id=INSTRUMENT,
    )

    with pytest.raises(ValueError, match="ask must not be below bid"):
        source.next_candle()
