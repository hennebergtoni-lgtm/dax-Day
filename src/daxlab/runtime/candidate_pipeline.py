"""Pure closed-bar vertical slice for DAX-BOT CAND-001.

The pipeline owns no persistence, broker, database, paper or web side effects.
Callers provide one canonical Candle and an explicit observation timestamp.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from daxlab.runtime.bar_identity import closed_bar_identity
from daxlab.runtime.candidate_admission import (
    Cand001AdmissionResult,
    Cand001AdmissionState,
    admit_cand001_trade,
)
from daxlab.runtime.candidate_config import Cand001Config
from daxlab.runtime.candidate_decision import build_cand001_decision
from daxlab.runtime.candidate_signal import (
    Cand001Signal,
    Cand001SignalState,
    SignalReason,
    transition_cand001,
)
from daxlab.runtime.candidate_trade_plan import Cand001TradePlan, build_cand001_trade_plan
from daxlab.runtime.contracts import Candle
from daxlab.runtime.decision import DecisionRecord
from daxlab.runtime.health import HealthState
from daxlab.runtime.operator_snapshot import OperatorSnapshot, build_operator_snapshot


@dataclass(frozen=True, slots=True)
class Cand001PipelineState:
    signal: Cand001SignalState = Cand001SignalState()
    admission: Cand001AdmissionState = Cand001AdmissionState()


@dataclass(frozen=True, slots=True)
class Cand001PipelineResult:
    state: Cand001PipelineState
    signal: Cand001Signal
    proposed_trade_plan: Cand001TradePlan | None
    admission: Cand001AdmissionResult
    decision: DecisionRecord
    operator_snapshot: OperatorSnapshot


def process_cand001_candle(
    state: Cand001PipelineState,
    candle: Candle,
    *,
    observed_at: datetime,
    config: Cand001Config | None = None,
) -> Cand001PipelineResult:
    """Process exactly one canonical closed candle through the pure CAND-001 stack."""
    if observed_at.tzinfo is None:
        raise ValueError("observed_at must be timezone-aware")
    if observed_at < candle.close_time:
        raise ValueError("observed_at cannot precede candle close_time")

    cfg = config or Cand001Config()
    transition = transition_cand001(state.signal, candle, config=cfg)
    proposed_plan = build_cand001_trade_plan(transition.signal, config=cfg)
    admission = admit_cand001_trade(
        state.admission,
        transition.signal,
        proposed_plan,
        config=cfg,
    )
    decision = build_cand001_decision(transition.signal, admission, config=cfg)
    last_bar_id = closed_bar_identity(
        canonical_symbol=candle.symbol,
        timeframe=candle.timeframe,
        close_time=candle.close_time,
    )
    health_state, runtime_events = _candidate_runtime_health(transition.signal.reason)
    snapshot = build_operator_snapshot(
        generated_at=observed_at,
        config=cfg,
        signal=transition.signal,
        proposed_trade_plan=proposed_plan,
        admission=admission,
        decision=decision,
        last_bar_id=last_bar_id,
        last_bar_close_time=candle.close_time,
        freshness_seconds=(observed_at - candle.close_time).total_seconds(),
        health_state=health_state.value,
        health_source="CANDIDATE_INPUT",
        runtime_events=runtime_events,
    )
    return Cand001PipelineResult(
        state=Cand001PipelineState(
            signal=transition.state,
            admission=admission.state,
        ),
        signal=transition.signal,
        proposed_trade_plan=proposed_plan,
        admission=admission,
        decision=decision,
        operator_snapshot=snapshot,
    )


def _candidate_runtime_health(reason: SignalReason) -> tuple[HealthState, tuple[str, ...]]:
    if reason is SignalReason.DATA_UNSAFE:
        return HealthState.RED, (SignalReason.DATA_UNSAFE.value,)
    if reason is SignalReason.OUT_OF_ORDER_BAR:
        return HealthState.RED, (SignalReason.OUT_OF_ORDER_BAR.value,)
    if reason is SignalReason.DUPLICATE_BAR:
        return HealthState.YELLOW, (SignalReason.DUPLICATE_BAR.value,)
    return HealthState.GREEN, ()
