from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

from daxlab.research.cand001_historical_replay import (
    CAND001_HISTORICAL_REPLAY_SCHEMA,
    ECONOMIC_CLAIM,
    EVIDENCE_CLASS,
    candles_from_legacy_session,
    run_cand001_historical_descriptive_replay,
)
from daxlab.runtime.contracts import Candle, DataQualityState


BERLIN = ZoneInfo("Europe/Berlin")
DATASET_SHA = "d" * 64


def _candle(hour: int, minute: int, *, open_: float, high: float, low: float, close: float) -> Candle:
    event = datetime(2026, 9, 11, hour, minute, tzinfo=BERLIN)
    return Candle(
        symbol="DE40",
        timeframe="5m",
        event_time=event,
        close_time=event + timedelta(minutes=5),
        open=open_,
        high=high,
        low=low,
        close=close,
        volume=None,
        source="AUDITED_RECOVERED_M5",
        received_at=event + timedelta(minutes=5),
        is_closed=True,
        quality_state=DataQualityState.OK,
    )


def _trade_path() -> tuple[Candle, ...]:
    return (
        _candle(9, 0, open_=100.0, high=102.0, low=99.0, close=101.0),
        _candle(9, 5, open_=101.0, high=103.0, low=100.0, close=102.0),
        _candle(9, 10, open_=102.0, high=103.0, low=98.0, close=101.0),
        _candle(9, 15, open_=101.0, high=105.0, low=100.0, close=104.0),
        _candle(9, 20, open_=104.0, high=108.0, low=101.0, close=106.0),
        _candle(9, 25, open_=106.0, high=114.0, low=103.0, close=113.0),
    )


def test_historical_replay_is_deterministic_descriptive_and_order_disabled() -> None:
    first = run_cand001_historical_descriptive_replay(
        _trade_path(), dataset_fingerprint=DATASET_SHA
    )
    second = run_cand001_historical_descriptive_replay(
        _trade_path(), dataset_fingerprint=DATASET_SHA
    )

    assert first.to_payload() == second.to_payload()
    report = first.report
    assert report.schema_version == CAND001_HISTORICAL_REPLAY_SCHEMA
    assert report.evidence_class == EVIDENCE_CLASS == "HISTORICAL_DESCRIPTIVE"
    assert report.economic_claim == ECONOMIC_CLAIM
    assert report.runtime_semantics_mode == "SHADOW"
    assert report.execution_capability == "NONE"
    assert report.order_execution_enabled is False
    assert report.processed_bars == 6
    assert report.processed_sessions == 1
    assert report.directional_signals >= 1
    assert report.admitted_trades == 1
    assert report.completed_trades == 1
    assert report.open_trade_at_end is False
    assert report.long_trades == 1
    assert report.short_trades == 0
    assert len(first.trades) == 1
    trade = first.trades[0]
    assert trade.trade_fingerprint
    assert trade.outcome_id
    assert trade.net_r < trade.gross_r
    assert report.trade_records_fingerprint
    assert report.report_fingerprint


def test_historical_session_adapter_emits_canonical_closed_m5_candles() -> None:
    index = pd.DatetimeIndex(
        [
            datetime(2019, 6, 3, 9, 0, tzinfo=BERLIN),
            datetime(2019, 6, 3, 9, 5, tzinfo=BERLIN),
        ]
    )
    frame = pd.DataFrame(
        {
            "open": [100.0, 101.0],
            "high": [102.0, 103.0],
            "low": [99.0, 100.0],
            "close": [101.0, 102.0],
        },
        index=index,
    )

    candles = candles_from_legacy_session(frame)

    assert len(candles) == 2
    assert all(candle.symbol == "DE40" for candle in candles)
    assert all(candle.timeframe == "5m" for candle in candles)
    assert all(candle.is_closed for candle in candles)
    assert all(candle.quality_state is DataQualityState.OK for candle in candles)
    assert candles[0].event_time == index[0].to_pydatetime()
    assert candles[0].close_time == candles[0].event_time + timedelta(minutes=5)
    assert candles[0].received_at == candles[0].close_time


def test_historical_replay_rejects_non_causal_or_unbound_inputs() -> None:
    with pytest.raises(ValueError, match="dataset_fingerprint"):
        run_cand001_historical_descriptive_replay(_trade_path(), dataset_fingerprint="short")

    bars = list(_trade_path())
    bars[1], bars[2] = bars[2], bars[1]
    with pytest.raises(ValueError, match="strictly chronological"):
        run_cand001_historical_descriptive_replay(tuple(bars), dataset_fingerprint=DATASET_SHA)


def test_historical_session_adapter_rejects_non_auditable_index() -> None:
    frame = pd.DataFrame(
        {"open": [100.0], "high": [101.0], "low": [99.0], "close": [100.5]},
        index=["2019-06-03 09:00"],
    )
    with pytest.raises(ValueError, match="DatetimeIndex"):
        candles_from_legacy_session(frame)
