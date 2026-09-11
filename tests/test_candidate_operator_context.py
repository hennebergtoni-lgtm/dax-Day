from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from daxlab.runtime.bar_identity import closed_bar_identity
from daxlab.runtime.candidate_pipeline import Cand001PipelineState, process_cand001_candle
from daxlab.runtime.contracts import Candle, DataQualityState


BERLIN = ZoneInfo("Europe/Berlin")


def _bar(
    hour: int,
    minute: int,
    *,
    open_: float,
    high: float,
    low: float,
    close: float,
    quality: DataQualityState = DataQualityState.OK,
) -> Candle:
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
        source="TEST",
        received_at=event + timedelta(minutes=5, seconds=1),
        is_closed=True,
        quality_state=quality,
    )


def _step(state: Cand001PipelineState, candle: Candle, *, delay_seconds: int = 1):
    return process_cand001_candle(
        state,
        candle,
        observed_at=candle.close_time + timedelta(seconds=delay_seconds),
    )


def test_operator_snapshot_exposes_strategy_context_last_bar_and_freshness() -> None:
    state = Cand001PipelineState()
    for candle in (
        _bar(9, 0, open_=100, high=102, low=99, close=101),
        _bar(9, 5, open_=101, high=103, low=98, close=102),
        _bar(9, 10, open_=102, high=102.5, low=98.5, close=101),
    ):
        state = _step(state, candle).state

    breakout = _bar(9, 15, open_=102, high=105, low=101, close=104)
    result = _step(state, breakout, delay_seconds=2)
    payload = result.operator_snapshot.as_dict()

    assert payload["strategy"] == {
        "regime": "OBSERVE_ONLY",
        "structure": "OPENING_RANGE/OR15",
        "setup": "LONG_BREAKOUT",
    }
    assert payload["runtime"]["last_bar_id"] == closed_bar_identity(
        canonical_symbol="DE40",
        timeframe="5m",
        close_time=breakout.close_time,
    )
    assert payload["runtime"]["last_bar_close_time"] == breakout.close_time.isoformat()
    assert payload["runtime"]["freshness_seconds"] == 2.0
    assert payload["runtime"]["health_state"] == "GREEN"
    assert payload["runtime"]["health_source"] == "CANDIDATE_INPUT"
    assert payload["runtime"]["events"] == []


def test_same_closed_bar_and_observation_time_keep_runtime_identity_deterministic() -> None:
    candle = _bar(9, 0, open_=100, high=102, low=99, close=101)
    observed_at = candle.close_time + timedelta(seconds=3)

    left = process_cand001_candle(
        Cand001PipelineState(), candle, observed_at=observed_at
    ).operator_snapshot
    right = process_cand001_candle(
        Cand001PipelineState(), candle, observed_at=observed_at
    ).operator_snapshot

    assert left == right
    assert left.snapshot_fingerprint == right.snapshot_fingerprint
    assert left.freshness_seconds == 3.0


def test_duplicate_bar_is_visible_as_yellow_runtime_event() -> None:
    candle = _bar(9, 0, open_=100, high=102, low=99, close=101)
    first = _step(Cand001PipelineState(), candle)
    duplicate = _step(first.state, candle)
    runtime = duplicate.operator_snapshot.as_dict()["runtime"]

    assert duplicate.signal.reason.value == "DUPLICATE_BAR"
    assert runtime["health_state"] == "YELLOW"
    assert runtime["health_source"] == "CANDIDATE_INPUT"
    assert runtime["events"] == ["DUPLICATE_BAR"]


def test_unsafe_bar_is_visible_as_red_runtime_event() -> None:
    unsafe = _bar(
        9,
        0,
        open_=100,
        high=102,
        low=99,
        close=101,
        quality=DataQualityState.GAP,
    )
    result = _step(Cand001PipelineState(), unsafe)
    runtime = result.operator_snapshot.as_dict()["runtime"]

    assert result.signal.reason.value == "DATA_UNSAFE"
    assert runtime["health_state"] == "RED"
    assert runtime["events"] == ["DATA_UNSAFE"]


def test_out_of_order_bar_is_visible_as_red_runtime_event() -> None:
    later = _bar(9, 5, open_=101, high=103, low=98, close=102)
    first = _step(Cand001PipelineState(), later)
    earlier = _bar(9, 0, open_=100, high=102, low=99, close=101)
    result = _step(first.state, earlier)
    runtime = result.operator_snapshot.as_dict()["runtime"]

    assert result.signal.reason.value == "OUT_OF_ORDER_BAR"
    assert runtime["health_state"] == "RED"
    assert runtime["events"] == ["OUT_OF_ORDER_BAR"]
