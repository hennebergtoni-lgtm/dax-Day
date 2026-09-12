from __future__ import annotations

import ast
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from daxlab.adapters.mt5_market_data import Mt5ClosedM5CandleSource
from daxlab.domain.market import DataQualityState, InstrumentId
from daxlab.domain.ports import CandleSourcePort
from daxlab.runtime.candidate_mt5_feed import validated_mt5_feed_to_candidate_candles
from daxlab.runtime.mt5_feed_payload import ClosedM5Feed
from daxlab.runtime.mt5_readonly import Mt5Bar


UTC = timezone.utc
EET = timezone(timedelta(hours=2))
INSTRUMENT = InstrumentId("DAX.CFD")


def bar(minute: int, close: float, *, tz=UTC) -> Mt5Bar:
    open_time = datetime(2026, 9, 10, 8, minute, tzinfo=UTC).astimezone(tz)
    return Mt5Bar(
        open_time=open_time,
        open=close - 0.5,
        high=close + 1.0,
        low=close - 1.0,
        close=close,
    )


def feed(
    *,
    bars: tuple[Mt5Bar, ...] | None = None,
    observed_at: datetime | None = None,
    fresh: bool = True,
    discontinuities: tuple[str, ...] = (),
) -> ClosedM5Feed:
    values = bars or (bar(0, 100.0), bar(5, 101.0), bar(10, 102.0))
    observed = observed_at or datetime(2026, 9, 10, 8, 16, tzinfo=UTC)
    return ClosedM5Feed(
        observed_at=observed,
        requested_start_pos=1,
        bars=values,
        latest_closed_fingerprint="f" * 64,
        age_seconds=60.0,
        fresh=fresh,
        discontinuities=discontinuities,
        broker_timezone=None,
        timestamp_interpretation="RAW_UTC_ASSUMPTION",
    )


def test_adapter_satisfies_candle_source_port_and_emits_each_bar_once() -> None:
    snapshot = feed()
    source = Mt5ClosedM5CandleSource(
        feed_provider=lambda: snapshot,
        broker_symbol="DE40",
        instrument_id=INSTRUMENT,
    )

    assert isinstance(source, CandleSourcePort)
    first = source.next_candle()
    second = source.next_candle()
    third = source.next_candle()
    exhausted = source.next_candle()

    assert first is not None and second is not None and third is not None
    assert exhausted is None
    assert tuple(item.close for item in (first, second, third)) == (100.0, 101.0, 102.0)
    assert tuple(item.close_time for item in (first, second, third)) == (
        datetime(2026, 9, 10, 8, 5, tzinfo=UTC),
        datetime(2026, 9, 10, 8, 10, tzinfo=UTC),
        datetime(2026, 9, 10, 8, 15, tzinfo=UTC),
    )
    assert all(item.instrument_id == INSTRUMENT for item in (first, second, third))
    assert all(item.timeframe == "M5" for item in (first, second, third))
    assert all(item.source == "MT5_READ_ONLY:DE40" for item in (first, second, third))
    assert all(item.quality_state is DataQualityState.OK for item in (first, second, third))
    assert all(item.safe_for_decision for item in (first, second, third))
    assert source.last_close_time == third.close_time


def test_adapter_normalizes_offset_aware_mt5_timestamps_to_canonical_utc() -> None:
    offset_bars = (bar(0, 100.0, tz=EET), bar(5, 101.0, tz=EET))
    observed = datetime(2026, 9, 10, 10, 11, tzinfo=EET)
    snapshot = feed(bars=offset_bars, observed_at=observed)
    source = Mt5ClosedM5CandleSource(
        feed_provider=lambda: snapshot,
        broker_symbol="DE40",
        instrument_id=INSTRUMENT,
    )

    candle = source.next_candle()

    assert candle is not None
    assert candle.event_time == datetime(2026, 9, 10, 8, 0, tzinfo=UTC)
    assert candle.close_time == datetime(2026, 9, 10, 8, 5, tzinfo=UTC)
    assert candle.received_at == datetime(2026, 9, 10, 8, 11, tzinfo=UTC)
    assert candle.event_time.utcoffset() == timedelta(0)
    assert candle.received_at.utcoffset() == timedelta(0)


def test_new_adapter_preserves_legacy_candidate_mt5_ohlc_and_time_semantics() -> None:
    snapshot = feed()
    legacy = validated_mt5_feed_to_candidate_candles(
        snapshot,
        broker_symbol="DE40",
        runtime_symbol="DE40",
    )
    source = Mt5ClosedM5CandleSource(
        feed_provider=lambda: snapshot,
        broker_symbol="DE40",
        instrument_id=INSTRUMENT,
    )
    modern = tuple(source.next_candle() for _ in range(len(snapshot.bars)))

    assert all(item is not None for item in modern)
    for old, new in zip(legacy, modern):
        assert new is not None
        assert new.event_time == old.event_time
        assert new.close_time == old.close_time
        assert new.open == old.open
        assert new.high == old.high
        assert new.low == old.low
        assert new.close == old.close
        assert new.volume == old.volume
        assert new.received_at == old.received_at
        assert new.is_closed == old.is_closed


def test_adapter_fails_closed_on_stale_discontinuous_or_unclosed_feed() -> None:
    stale = feed(fresh=False)
    source = Mt5ClosedM5CandleSource(
        feed_provider=lambda: stale,
        broker_symbol="DE40",
        instrument_id=INSTRUMENT,
    )
    with pytest.raises(ValueError, match="fresh market data"):
        source.next_candle()

    discontinuous = feed(discontinuities=("gap",))
    source = Mt5ClosedM5CandleSource(
        feed_provider=lambda: discontinuous,
        broker_symbol="DE40",
        instrument_id=INSTRUMENT,
    )
    with pytest.raises(ValueError, match="continuous"):
        source.next_candle()

    unclosed_bar = bar(15, 103.0)
    unclosed = feed(
        bars=(bar(10, 102.0), unclosed_bar),
        observed_at=datetime(2026, 9, 10, 8, 19, tzinfo=UTC),
    )
    source = Mt5ClosedM5CandleSource(
        feed_provider=lambda: unclosed,
        broker_symbol="DE40",
        instrument_id=INSTRUMENT,
    )
    with pytest.raises(ValueError, match="closed bars only"):
        source.next_candle()


def test_adapter_rejects_invalid_feed_shape_and_ohlc() -> None:
    snapshot = feed()
    bad_start = replace(snapshot, requested_start_pos=0)
    source = Mt5ClosedM5CandleSource(
        feed_provider=lambda: bad_start,
        broker_symbol="DE40",
        instrument_id=INSTRUMENT,
    )
    with pytest.raises(ValueError, match="position >= 1"):
        source.next_candle()

    duplicate = replace(snapshot, bars=(snapshot.bars[0], snapshot.bars[0]))
    source = Mt5ClosedM5CandleSource(
        feed_provider=lambda: duplicate,
        broker_symbol="DE40",
        instrument_id=INSTRUMENT,
    )
    with pytest.raises(ValueError, match="unique"):
        source.next_candle()

    bad_ohlc_bar = replace(snapshot.bars[0], high=99.0)
    bad_ohlc = replace(snapshot, bars=(bad_ohlc_bar,))
    source = Mt5ClosedM5CandleSource(
        feed_provider=lambda: bad_ohlc,
        broker_symbol="DE40",
        instrument_id=INSTRUMENT,
    )
    with pytest.raises(ValueError, match="high violates OHLC"):
        source.next_candle()


def test_none_snapshot_is_non_error_no_data_state() -> None:
    source = Mt5ClosedM5CandleSource(
        feed_provider=lambda: None,
        broker_symbol="DE40",
        instrument_id=INSTRUMENT,
    )
    assert source.next_candle() is None
    assert source.last_close_time is None


def test_adapter_boundary_has_no_sdk_candidate_or_execution_dependency() -> None:
    repo = Path(__file__).resolve().parents[1]
    module = repo / "src/daxlab/adapters/mt5_market_data.py"
    tree = ast.parse(module.read_text(encoding="utf-8"))
    imported: set[str] = set()
    attribute_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
        elif isinstance(node, ast.Attribute):
            attribute_names.add(node.attr)

    forbidden_imports = (
        "MetaTrader5",
        "daxlab.runtime.candidate",
        "daxlab.domain.execution",
    )
    assert not any(
        name == prefix or name.startswith(prefix + ".")
        for name in imported
        for prefix in forbidden_imports
    )
    assert "order_send" not in attribute_names
    assert "accept_intent" not in attribute_names

    source = Mt5ClosedM5CandleSource(
        feed_provider=lambda: None,
        broker_symbol="DE40",
        instrument_id=INSTRUMENT,
    )
    assert not hasattr(source, "order_send")
    assert not hasattr(source, "accept_intent")
