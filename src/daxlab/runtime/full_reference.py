"""Guarded full-reference replay orchestration around the frozen V11.2 engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from daxlab.runtime.contracts import Candle
from daxlab.runtime.readiness import ReadinessSnapshot, RunKind, evaluate_run_readiness
from daxlab.runtime.v112_bridge import (
    assert_v112_day_parity,
    run_historical_days,
    run_replay_days,
    v112_results_fingerprint,
)


@dataclass(frozen=True, slots=True)
class FullReferenceReplayResult:
    days: int
    historical_fingerprint: str
    replay_fingerprint: str


def run_guarded_full_reference_replay(
    engine: Any,
    candles: tuple[Candle, ...],
    params: Any,
    readiness: ReadinessSnapshot,
    cost_name: str = "normal",
) -> FullReferenceReplayResult:
    """Run deterministic historical/replay parity only after readiness passes."""
    gate = evaluate_run_readiness(RunKind.CLEAN_REFERENCE_REPLAY, readiness)
    if not gate.allowed:
        blockers = ",".join(gate.blockers)
        raise RuntimeError(f"clean-reference replay blocked: {blockers}")
    if not candles:
        raise ValueError("clean-reference replay requires candles")

    historical = run_historical_days(engine, candles, params, cost_name)
    replay_first = run_replay_days(engine, candles, params, cost_name)
    replay_second = run_replay_days(engine, candles, params, cost_name)

    assert_v112_day_parity(historical, replay_first)
    if replay_first != replay_second:
        raise AssertionError("V11.2 full-reference replay rerun drift")

    historical_hash = v112_results_fingerprint(historical)
    replay_hash = v112_results_fingerprint(replay_first)
    rerun_hash = v112_results_fingerprint(replay_second)
    if historical_hash != replay_hash or replay_hash != rerun_hash:
        raise AssertionError("V11.2 full-reference replay fingerprint drift")

    return FullReferenceReplayResult(
        days=len(replay_first),
        historical_fingerprint=historical_hash,
        replay_fingerprint=replay_hash,
    )
