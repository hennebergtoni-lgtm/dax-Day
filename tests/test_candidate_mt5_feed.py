from dataclasses import replace
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from daxlab.runtime.candidate_mt5_feed import (
    mt5_bar_to_candidate_candle,
    validated_mt5_feed_to_candidate_candles,
)
from daxlab.runtime.mt5_feed_payload import ClosedM5Feed
from daxlab.runtime.mt5_readonly import Mt5Bar


HELSINKI = ZoneInfo("Europe/Helsinki")


def _bar(hour: int, minute: int, *, close: float = 100.5) -> Mt5Bar:
    return Mt5Bar(
        open_time=datetime(2026, 9, 11, hour, minute, tzinfo=HELSINKI),
        open=100.0,
        high=101.0,
        low=99.0,
        close=close,
    )


def _feed(*bars: Mt5Bar) -> ClosedM5Feed:
    observed_at = bars[-1].open_time + timedelta(minutes=5, seconds=2)
    return ClosedM5Feed(
        observed_at=observed_at,
        requested_start_pos=1,
        bars=tuple(bars),
        latest_closed_fingerprint="a" * 64,
        age_seconds=2.0,
        fresh=True,
        discontinuities=(),
        broker_timezone="Europe/Helsinki",
        timestamp_interpretation="EXPLICIT_BROKER_WALL_CLOCK",
    )


def test_mt5_bar_preserves_broker_wall_clock_and_closed_bar_causality() -> None:
    bar = _bar(10, 0)
    observed_at = bar.open_time + timedelta(minutes=5, seconds=3)

    candle = mt5_bar_to_candidate_candle(
        bar,
        broker_symbol="DE40",
        observed_at=observed_at,
    )

    assert candle.symbol == "DE40"
    assert candle.timeframe == "5m"
    assert candle.event_time == bar.open_time
    assert candle.close_time == bar.open_time + timedelta(minutes=5)
    assert candle.received_at == observed_at
    assert candle.is_closed is True
    assert candle.source == "MT5_READ_ONLY:DE40"
    assert candle.open == 100.0
    assert candle.high == 101.0
    assert candle.low == 99.0
    assert candle.close == 100.5


def test_validated_feed_converts_chronologically_without_retiming() -> None:
    first = _bar(10, 0)
    second = _bar(10, 5, close=100.75)
    candles = validated_mt5_feed_to_candidate_candles(
        _feed(first, second),
        broker_symbol="DE40",
    )

    assert tuple(candle.event_time for candle in candles) == (
        first.open_time,
        second.open_time,
    )
    assert tuple(candle.close_time for candle in candles) == (
        first.open_time + timedelta(minutes=5),
        second.open_time + timedelta(minutes=5),
    )
    assert all(candle.source == "MT5_READ_ONLY:DE40" for candle in candles)


def test_stale_or_discontinuous_feed_fails_closed() -> None:
    first = _bar(10, 0)
    second = _bar(10, 5)
    feed = _feed(first, second)

    with pytest.raises(ValueError, match="fresh"):
        validated_mt5_feed_to_candidate_candles(
            replace(feed, fresh=False),
            broker_symbol="DE40",
        )
    with pytest.raises(ValueError, match="continuous"):
        validated_mt5_feed_to_candidate_candles(
            replace(feed, discontinuities=("gap",)),
            broker_symbol="DE40",
        )


def test_unclosed_bar_fails_closed_even_when_called_directly() -> None:
    bar = _bar(10, 0)
    with pytest.raises(ValueError, match="closed bars only"):
        mt5_bar_to_candidate_candle(
            bar,
            broker_symbol="DE40",
            observed_at=bar.open_time + timedelta(minutes=4, seconds=59),
        )


def test_broker_symbol_provenance_is_separate_from_candidate_symbol() -> None:
    bar = _bar(10, 0)
    candle = mt5_bar_to_candidate_candle(
        bar,
        broker_symbol="GER40",
        runtime_symbol="DE40",
        observed_at=bar.open_time + timedelta(minutes=5),
    )

    assert candle.symbol == "DE40"
    assert candle.source == "MT5_READ_ONLY:GER40"
