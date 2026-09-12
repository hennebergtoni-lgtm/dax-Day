"""Validated MT5 CLOSED-M5 batch runner for the CAND-001 SHADOW orchestrator.

The existing MT5 feed contract owns freshness, continuity and timestamp meaning.
This module converts that feed to canonical candidate candles, filters already
processed overlap after restart, and delegates each new bar to the deterministic
SHADOW orchestrator. It has no broker order capability.
"""
from __future__ import annotations

from dataclasses import dataclass

from daxlab.runtime.candidate_config import Cand001Config
from daxlab.runtime.candidate_mt5_feed import validated_mt5_feed_to_candidate_candles
from daxlab.runtime.candidate_shadow_orchestrator import (
    Cand001ShadowState,
    Cand001ShadowStepResult,
    process_cand001_shadow_candle,
)
from daxlab.runtime.candidate_sizing import Cand001SimulationSizingPolicy
from daxlab.runtime.manifests import RunManifest
from daxlab.runtime.mt5_feed_payload import ClosedM5Feed
from daxlab.runtime.operator_runtime_bridge import OperatorRuntimeContext
from daxlab.runtime.paper_contracts import PaperFillModelConfig


@dataclass(frozen=True, slots=True)
class Cand001ShadowFeedResult:
    state: Cand001ShadowState
    steps: tuple[Cand001ShadowStepResult, ...]
    feed_bar_count: int
    processed_bar_count: int
    overlap_filtered_bar_count: int
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.feed_bar_count < 1:
            raise ValueError("candidate SHADOW feed result requires source bars")
        if self.processed_bar_count != len(self.steps):
            raise ValueError("candidate SHADOW processed count mismatch")
        if self.processed_bar_count + self.overlap_filtered_bar_count != self.feed_bar_count:
            raise ValueError("candidate SHADOW feed accounting mismatch")
        if self.execution_capability != "NONE" or self.order_execution_enabled:
            raise ValueError("candidate SHADOW feed result cannot authorize execution")

    @property
    def latest_step(self) -> Cand001ShadowStepResult | None:
        return self.steps[-1] if self.steps else None


def run_cand001_shadow_from_mt5_feed(
    state: Cand001ShadowState,
    feed: ClosedM5Feed,
    *,
    broker_symbol: str,
    run_manifest: RunManifest,
    config: Cand001Config | None = None,
    sizing: Cand001SimulationSizingPolicy | None = None,
    fill_model: PaperFillModelConfig | None = None,
    runtime_context: OperatorRuntimeContext | None = None,
) -> Cand001ShadowFeedResult:
    """Process only new bars from one validated, possibly overlapping MT5 feed."""
    cfg = config or Cand001Config()
    candles = validated_mt5_feed_to_candidate_candles(
        feed,
        broker_symbol=broker_symbol,
        runtime_symbol=cfg.symbol,
    )
    last_close = state.pipeline.signal.last_close_time
    if last_close is None:
        new_candles = candles
    else:
        new_candles = tuple(candle for candle in candles if candle.close_time > last_close)
    overlap = len(candles) - len(new_candles)

    current = state
    results: list[Cand001ShadowStepResult] = []
    for candle in new_candles:
        step = process_cand001_shadow_candle(
            current,
            candle,
            observed_at=feed.observed_at,
            run_manifest=run_manifest,
            config=cfg,
            sizing=sizing,
            fill_model=fill_model,
            runtime_context=runtime_context,
        )
        current = step.state
        results.append(step)

    return Cand001ShadowFeedResult(
        state=current,
        steps=tuple(results),
        feed_bar_count=len(candles),
        processed_bar_count=len(results),
        overlap_filtered_bar_count=overlap,
    )
