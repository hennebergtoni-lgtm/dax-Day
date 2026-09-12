"""Compatibility adapter from canonical NextGen strategy contracts to CAND-001.

The existing runtime CAND-001 pipeline remains the behavior owner. This module only
binds canonical instrument/timeframe identity, translates candle contracts, invokes
that pure pipeline, and maps its final admitted decision back to Strategy Plugin V1.
It adds no broker, sizing or order capability.
"""

from __future__ import annotations

from dataclasses import dataclass

from daxlab.domain.market import Candle as CanonicalCandle
from daxlab.domain.market import InstrumentId
from daxlab.domain.strategy import (
    StrategyDecision,
    TradeDirection,
    TradePlan,
)
from daxlab.runtime.candidate_config import Cand001Config
from daxlab.runtime.candidate_pipeline import (
    Cand001PipelineResult,
    Cand001PipelineState,
    process_cand001_candle,
)
from daxlab.runtime.candidate_signal import SignalDirection
from daxlab.runtime.contracts import Candle as RuntimeCandle
from daxlab.runtime.contracts import DataQualityState as RuntimeDataQualityState
from daxlab.runtime.decision import FinalAction
from daxlab.strategies.contracts import StrategyTransition


@dataclass(frozen=True, slots=True)
class Cand001StrategyBinding:
    """Explicit canonical identity binding for the legacy CAND-001 input contract."""

    instrument_id: InstrumentId
    timeframe: str

    def __post_init__(self) -> None:
        if not self.timeframe or self.timeframe != self.timeframe.strip():
            raise ValueError("canonical timeframe must be a non-empty normalized token")


class Cand001StrategyPlugin:
    """Strategy Plugin V1 wrapper around the unchanged pure CAND-001 pipeline."""

    def __init__(
        self,
        *,
        binding: Cand001StrategyBinding,
        config: Cand001Config | None = None,
    ) -> None:
        self._binding = binding
        self._config = config or Cand001Config()
        self._identity = self._config.product_identity()

    @property
    def strategy_id(self) -> str:
        return self._config.candidate_id

    @property
    def strategy_version(self) -> str:
        return self._config.ruleset_version

    @property
    def strategy_fingerprint(self) -> str:
        return self._identity.fingerprint()

    @property
    def binding(self) -> Cand001StrategyBinding:
        return self._binding

    @property
    def config(self) -> Cand001Config:
        return self._config

    def initial_state(self) -> Cand001PipelineState:
        return Cand001PipelineState()

    def on_candle(
        self,
        state: Cand001PipelineState,
        candle: CanonicalCandle,
    ) -> StrategyTransition[Cand001PipelineState]:
        runtime_candle = adapt_cand001_runtime_candle(
            candle,
            binding=self._binding,
            config=self._config,
        )
        result = process_cand001_candle(
            state,
            runtime_candle,
            observed_at=candle.received_at,
            config=self._config,
        )
        decision = map_cand001_strategy_decision(
            result,
            instrument_id=self._binding.instrument_id,
            strategy_id=self.strategy_id,
            strategy_version=self.strategy_version,
            strategy_fingerprint=self.strategy_fingerprint,
        )
        return StrategyTransition(state=result.state, decision=decision)


def adapt_cand001_runtime_candle(
    candle: CanonicalCandle,
    *,
    binding: Cand001StrategyBinding,
    config: Cand001Config | None = None,
) -> RuntimeCandle:
    """Translate one canonical candle into the exact existing CAND-001 input contract."""
    cfg = config or Cand001Config()
    if candle.instrument_id != binding.instrument_id:
        raise ValueError(
            "canonical candle instrument does not match explicit CAND-001 binding"
        )
    if candle.timeframe != binding.timeframe:
        raise ValueError(
            "canonical candle timeframe does not match explicit CAND-001 binding"
        )

    return RuntimeCandle(
        symbol=cfg.symbol,
        timeframe=cfg.bar_timeframe,
        event_time=candle.event_time,
        close_time=candle.close_time,
        open=candle.open,
        high=candle.high,
        low=candle.low,
        close=candle.close,
        volume=candle.volume,
        source=candle.source,
        received_at=candle.received_at,
        is_closed=candle.is_closed,
        quality_state=RuntimeDataQualityState(candle.quality_state.value),
    )


def map_cand001_strategy_decision(
    result: Cand001PipelineResult,
    *,
    instrument_id: InstrumentId,
    strategy_id: str,
    strategy_version: str,
    strategy_fingerprint: str,
) -> StrategyDecision:
    """Map only the existing final admitted CAND-001 action into Strategy Plugin V1."""
    reason_codes = _reason_codes(result)
    if result.decision.final_action is FinalAction.TRADE:
        admitted = result.admission.admitted_plan
        if admitted is None:
            raise ValueError("legacy TRADE decision requires an admitted CAND-001 plan")
        direction = _trade_direction(admitted.direction)
        return StrategyDecision.trade(
            strategy_id=strategy_id,
            strategy_version=strategy_version,
            strategy_fingerprint=strategy_fingerprint,
            event_time=result.decision.event_time,
            instrument_id=instrument_id,
            reason_codes=reason_codes,
            trade_plan=TradePlan(
                instrument_id=instrument_id,
                direction=direction,
                entry_price=admitted.entry_price,
                stop_price=admitted.stop_price,
                target_price=admitted.target_price,
            ),
        )

    if result.decision.final_action is not FinalAction.NO_TRADE:
        raise ValueError("unsupported legacy CAND-001 final action")
    return StrategyDecision.no_trade(
        strategy_id=strategy_id,
        strategy_version=strategy_version,
        strategy_fingerprint=strategy_fingerprint,
        event_time=result.decision.event_time,
        instrument_id=instrument_id,
        reason_codes=reason_codes,
    )


def _reason_codes(result: Cand001PipelineResult) -> tuple[str, ...]:
    codes = [
        f"SIGNAL:{result.signal.reason.value}",
        f"ADMISSION:{result.admission.status.value}",
    ]
    codes.extend(f"BLOCKER:{blocker}" for blocker in result.decision.blockers)
    return tuple(codes)


def _trade_direction(direction: SignalDirection) -> TradeDirection:
    if direction is SignalDirection.LONG:
        return TradeDirection.LONG
    if direction is SignalDirection.SHORT:
        return TradeDirection.SHORT
    raise ValueError("admitted CAND-001 plan must be LONG or SHORT")
