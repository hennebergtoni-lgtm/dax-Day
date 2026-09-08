"""Bridge canonical closed candles into the frozen V11.2 engine without strategy duplication."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd

from daxlab.runtime.contracts import Candle

BERLIN = ZoneInfo("Europe/Berlin")


@dataclass(frozen=True, slots=True)
class V112DayResult:
    day: date
    outcome: Any


def candles_to_v112_frame(candles: Iterable[Candle]) -> pd.DataFrame:
    """Convert safe closed candles to the dataframe contract used by V11.2."""
    rows: list[dict[str, object]] = []
    for candle in candles:
        if not candle.safe_for_decision:
            raise ValueError("V11.2 bridge accepts only safe closed candles")
        local_time = candle.event_time.astimezone(BERLIN)
        rows.append(
            {
                "datetime": pd.Timestamp(local_time),
                "date": local_time.date(),
                "time": local_time.strftime("%H:%M"),
                "open": float(candle.open),
                "high": float(candle.high),
                "low": float(candle.low),
                "close": float(candle.close),
            }
        )
    if not rows:
        return pd.DataFrame(
            columns=["datetime", "date", "time", "open", "high", "low", "close"]
        )
    frame = pd.DataFrame(rows).sort_values("datetime").reset_index(drop=True)
    if frame["datetime"].duplicated().any():
        raise ValueError("duplicate candle datetime in V11.2 bridge")
    return frame


def _simulate_complete_day(
    engine: Any,
    history: pd.DataFrame,
    day: date,
    params: Any,
    cost_name: str,
) -> V112DayResult:
    context = engine.daily_context(history)
    day_frame = engine.day_slice(history, day)
    day_context = context.get(day, {})
    outcome = engine.simulate_day(
        day_frame,
        params,
        day_context,
        engine.COST_SCENARIOS[cost_name],
    )
    return V112DayResult(day=day, outcome=outcome)


def run_historical_days(
    engine: Any,
    candles: Iterable[Candle],
    params: Any,
    cost_name: str = "normal",
) -> tuple[V112DayResult, ...]:
    """Run completed session days from a historical candle collection."""
    frame = candles_to_v112_frame(candles)
    return tuple(
        _simulate_complete_day(engine, frame, day, params, cost_name)
        for day in engine.trading_days(frame)
    )


def run_replay_days(
    engine: Any,
    candles: Iterable[Candle],
    params: Any,
    cost_name: str = "normal",
) -> tuple[V112DayResult, ...]:
    """Replay candles chronologically and evaluate a day only after it is complete."""
    ordered = sorted(candles, key=lambda candle: candle.event_time)
    if not ordered:
        return ()

    results: list[V112DayResult] = []
    completed: list[Candle] = []
    current_day = ordered[0].event_time.astimezone(BERLIN).date()
    day_buffer: list[Candle] = []

    for candle in ordered:
        if not candle.safe_for_decision:
            raise ValueError("V11.2 replay rejects unsafe or open candles")
        candle_day = candle.event_time.astimezone(BERLIN).date()
        if candle_day != current_day:
            completed.extend(day_buffer)
            history = candles_to_v112_frame(completed)
            results.append(
                _simulate_complete_day(engine, history, current_day, params, cost_name)
            )
            day_buffer = []
            current_day = candle_day
        day_buffer.append(candle)

    completed.extend(day_buffer)
    history = candles_to_v112_frame(completed)
    results.append(_simulate_complete_day(engine, history, current_day, params, cost_name))
    return tuple(results)


def v112_results_fingerprint(results: Iterable[V112DayResult]) -> str:
    """Create a deterministic hash for repeated replay-result comparison."""
    payload = "\n".join(
        f"{result.day.isoformat()}\x1f{result.outcome!r}" for result in results
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def assert_v112_day_parity(
    historical: tuple[V112DayResult, ...], replay: tuple[V112DayResult, ...]
) -> None:
    """Fail on any historical/replay day-result difference."""
    if historical != replay:
        raise AssertionError(
            f"V11.2 historical/replay mismatch: {historical!r} != {replay!r}"
        )
