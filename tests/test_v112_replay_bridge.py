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
    v112_results_fingerprint,
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


def make_one(event: datetime) -> Candle:
    return Candle(
        symbol="DAX",
        timeframe="5m",
        event_time=event,
        close_time=event + timedelta(minutes=5),
        open=100.0,
        high=101.0,
        low=99.0,
        close=100.5,
        volume=None,
        source="fixture",
        received_at=event + timedelta(minutes=5, seconds=1),
        is_closed=True,
        quality_state=DataQualityState.OK,
    )


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
    params = next(iter(engine.grid()))
    candles = make_session(2) + make_session(3) + make_session(4)
    historical = run_historical_days(engine, candles, params)
    replay = run_replay_days(engine, candles, params)
    assert len(historical) == 3
    assert_v112_day_parity(historical, replay)


def test_v112_daily_context_does_not_use_current_day_range() -> None:
    engine = load_exact_candidate_engine()
    candles = [candle for day in range(2, 19) for candle in make_session(day)]
    original = candles_to_v112_frame(candles)
    target_day = original.iloc[-1]["date"]
    original_context = engine.daily_context(original)[target_day]

    mutated = original.copy()
    current_mask = mutated["date"] == target_day
    mutated.loc[current_mask, "high"] += 5000.0
    mutated.loc[current_mask, "low"] -= 5000.0
    mutated_context = engine.daily_context(mutated)[target_day]

    assert original_context == mutated_context


def test_bridge_preserves_berlin_winter_and_summer_session_time() -> None:
    winter = make_one(datetime(2026, 1, 5, 9, 0, tzinfo=BERLIN))
    summer = make_one(datetime(2026, 6, 5, 9, 0, tzinfo=BERLIN))
    frame = candles_to_v112_frame([winter, summer])
    assert frame.iloc[0]["time"] == "09:00"
    assert frame.iloc[1]["time"] == "09:00"
    assert frame.iloc[0]["datetime"].utcoffset() == timedelta(hours=1)
    assert frame.iloc[1]["datetime"].utcoffset() == timedelta(hours=2)


def test_replay_rerun_is_deterministic() -> None:
    engine = load_exact_candidate_engine()
    params = next(iter(engine.grid()))
    candles = make_session(2) + make_session(3) + make_session(4)
    first = run_replay_days(engine, candles, params)
    second = run_replay_days(engine, candles, params)
    assert first == second
    assert v112_results_fingerprint(first) == v112_results_fingerprint(second)


def test_bridge_rejects_unsafe_data() -> None:
    with pytest.raises(ValueError, match="safe closed candles"):
        candles_to_v112_frame(make_session(2, quality=DataQualityState.GAP))
