"""Guarded fixture-only smoke run through the SHA-verified V11.2 engine."""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from daxlab.reference.recovered_engine import load_exact_candidate_engine
from daxlab.runtime.contracts import Candle, DataQualityState
from daxlab.runtime.v112_bridge import (
    assert_v112_day_parity,
    run_historical_days,
    run_replay_days,
    v112_results_fingerprint,
)

BERLIN = ZoneInfo("Europe/Berlin")
FIXTURE_DAYS = 17
BARS_PER_DAY = 103


def build_fixture() -> list[Candle]:
    candles: list[Candle] = []
    for day_index in range(FIXTURE_DAYS):
        start = datetime(2026, 1, 5, 9, 0, tzinfo=BERLIN) + timedelta(days=day_index)
        base = 16500.0 + day_index * 8.0
        for bar_index in range(BARS_PER_DAY):
            event = start + timedelta(minutes=5 * bar_index)
            wave = ((bar_index % 18) - 9) * 0.35
            drift = bar_index * 0.06
            close = base + drift + wave
            candles.append(
                Candle(
                    symbol="DAX",
                    timeframe="5m",
                    event_time=event,
                    close_time=event + timedelta(minutes=5),
                    open=close - 0.15,
                    high=close + 1.2,
                    low=close - 1.0,
                    close=close,
                    volume=None,
                    source="fixture-only",
                    received_at=event + timedelta(minutes=5, seconds=1),
                    is_closed=True,
                    quality_state=DataQualityState.OK,
                )
            )
    return candles


def main() -> None:
    engine = load_exact_candidate_engine()
    params = next(iter(engine.grid()))
    candles = build_fixture()

    historical = run_historical_days(engine, candles, params)
    replay_first = run_replay_days(engine, candles, params)
    replay_second = run_replay_days(engine, candles, params)

    assert_v112_day_parity(historical, replay_first)
    if replay_first != replay_second:
        raise SystemExit("V11.2 replay smoke failed: rerun result drift")

    first_hash = v112_results_fingerprint(replay_first)
    second_hash = v112_results_fingerprint(replay_second)
    if first_hash != second_hash:
        raise SystemExit("V11.2 replay smoke failed: fingerprint drift")

    print(
        "V11.2 replay smoke OK | "
        f"surface=FIXTURE_ONLY | days={len(replay_first)} | bars={len(candles)} | "
        f"fingerprint={first_hash}"
    )
    print("Clean 2014-2019 reference parity status: UNVERIFIED_PENDING_AUDITED_BUNDLE")


if __name__ == "__main__":
    main()
