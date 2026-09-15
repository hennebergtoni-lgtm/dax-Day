"""Measure the pure DAX-BOT CAND-001 pipeline without imposing a pass/fail budget."""
from __future__ import annotations

import argparse
import json
import math
import platform
from datetime import date, datetime, time, timedelta
from statistics import median
from time import perf_counter_ns
from zoneinfo import ZoneInfo

from daxlab.runtime.candidate_config import Cand001Config
from daxlab.runtime.candidate_pipeline import Cand001PipelineState, process_cand001_candle
from daxlab.runtime.contracts import Candle


SCHEMA_VERSION = "DAX_BOT_CAND001_BENCHMARK_V1"
BERLIN = ZoneInfo("Europe/Berlin")
BARS_PER_SESSION = 103


def synthetic_session(day: date, *, base_price: float) -> tuple[Candle, ...]:
    """Build one deterministic 103-bar feed surface from 09:00 through 17:30."""
    session_start = datetime.combine(day, time(9, 0), tzinfo=BERLIN)
    bars: list[Candle] = []
    for index in range(BARS_PER_SESSION):
        event = session_start + timedelta(minutes=5 * index)
        if index == 0:
            open_price, high, low, close = base_price, base_price + 5, base_price - 5, base_price + 1
        elif index == 1:
            open_price, high, low, close = base_price + 1, base_price + 8, base_price - 6, base_price + 2
        elif index == 2:
            open_price, high, low, close = base_price + 2, base_price + 7, base_price - 7, base_price + 1
        elif index == 3:
            open_price, high, low, close = base_price + 2, base_price + 12, base_price + 1, base_price + 10
        else:
            open_price, high, low, close = base_price, base_price + 2, base_price - 2, base_price
        bars.append(
            Candle(
                symbol="DE40",
                timeframe="5m",
                event_time=event,
                close_time=event + timedelta(minutes=5),
                open=float(open_price),
                high=float(high),
                low=float(low),
                close=float(close),
                volume=None,
                source="SYNTHETIC_BENCHMARK",
                received_at=event + timedelta(minutes=5, seconds=1),
                is_closed=True,
            )
        )
    return tuple(bars)


def benchmark(*, sessions: int, repeats: int) -> dict[str, object]:
    if sessions < 1:
        raise ValueError("sessions must be >= 1")
    if repeats < 1:
        raise ValueError("repeats must be >= 1")

    cfg = Cand001Config()
    start_day = date(2026, 1, 5)
    feed = tuple(
        candle
        for session_index in range(sessions)
        for candle in synthetic_session(
            start_day + timedelta(days=session_index),
            base_price=25000.0 + session_index,
        )
    )
    event_count = len(feed)
    samples_ns_per_event: list[float] = []
    terminal_fingerprint = ""

    for _ in range(repeats):
        state = Cand001PipelineState()
        started = perf_counter_ns()
        for candle in feed:
            result = process_cand001_candle(
                state,
                candle,
                observed_at=candle.close_time + timedelta(seconds=1),
                config=cfg,
            )
            state = result.state
            terminal_fingerprint = result.operator_snapshot.snapshot_fingerprint
        elapsed_ns = perf_counter_ns() - started
        samples_ns_per_event.append(elapsed_ns / event_count)

    sorted_samples = sorted(samples_ns_per_event)
    p95_index = max(0, math.ceil(0.95 * len(sorted_samples)) - 1)
    median_ns = median(samples_ns_per_event)
    return {
        "schema_version": SCHEMA_VERSION,
        "core_version": cfg.product_identity().core_version,
        "candidate_id": cfg.candidate_id,
        "config_fingerprint": cfg.product_identity().config_fingerprint,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "sessions": sessions,
        "bars_per_session": BARS_PER_SESSION,
        "events_per_repeat": event_count,
        "repeats": repeats,
        "samples_ns_per_event": samples_ns_per_event,
        "median_ns_per_event": median_ns,
        "p95_ns_per_event": sorted_samples[p95_index],
        "median_events_per_second": 1_000_000_000.0 / median_ns,
        "terminal_snapshot_fingerprint": terminal_fingerprint,
        "performance_gate": "OBSERVATION_ONLY",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sessions", type=int, default=20)
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()
    print(json.dumps(benchmark(sessions=args.sessions, repeats=args.repeats), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
