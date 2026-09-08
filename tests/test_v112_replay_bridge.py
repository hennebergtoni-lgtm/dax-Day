from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from daxlab.reference.recovered_engine import load_exact_candidate_engine
from daxlab.runtime.contracts import Candle, DataQualityState
from daxlab.runtime.v112_bridge import (
    assert_v112_day_parity,
    candles_to_v112_frame,
    run_historical_days,
    run_replay_days,
)

BERLIN = ZoneInfo("Europe/Berlin")


def make_session(day: int, *, quality: DataQualityState = DataQualityState.OK) -> list[Candle]:
    start = datetime(2026, 1, day, 9, 0, tzinfo=BERLIN)
    candles: list[Candle] = []
    price = 100.0 + day
    for index in range(103):
        event = start + timedelta(minutes=5 * index)
        close = price + index * 0.02
        candles.append(
            Candle(
                symbol="DAX",
                timeframe="5m",
                event_time=event,
                close_time=event + timedelta(minutes=5),
                open=close - 0.01,
                high=close + 0.05,
                low=close - 0.05,
                close=close,
                volume=None,
                source="fixture",
                received_at=event + timedelta(minutes=5, seconds=1),
                is_closed=True,
                quality_state=quality,
            )
        )
    return candles


def test_bridge_frame_matches_v112_dataframe_contract() -> None:
    frame = candles_to_v112_frame(make_session(2))
    assert list(frame.columns) == [
        "datetime",
        "date",
        "time",
        "open",
        "high",
        "low",
        "close",
    ]
    assert len(frame) == 103
    assert frame.iloc[0]["time"] == "09:00"
    assert frame.iloc[-1]["time"] == "17:30"


def test_real_v112_engine_historical_and_replay_match_on_complete_days() -> None:
    engine = load_exact_candidate_engine()
    params = list(engine.grid())[0]
    candles = make_session(2) + make_session(3) + make_session(4)
    historical = run_historical_days(engine, candles, params)
    replay = run_replay_days(engine, candles, params)
    assert len(historical) == 3
    assert_v112_day_parity(historical, replay)


def test_bridge_rejects_unsafe_data() -> None:
    with pytest.raises(ValueError, match="safe closed candles"):
        candles_to_v112_frame(make_session(2, quality=DataQualityState.GAP))
