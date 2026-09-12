"""Deterministic broker-neutral replay engine for DAX-BOT NextGen.

This engine owns only causal event sequencing and Strategy Plugin orchestration.
It has no broker, risk sizing, persistence backend or order-submission capability.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
import json
from typing import Generic, Sequence, TypeVar

from daxlab.domain.market import Candle, InstrumentId
from daxlab.domain.strategy import StrategyDecision
from daxlab.strategies.contracts import StrategyPlugin


ENGINE_VERSION = "DAXLAB_PRODUCT_REPLAY_V1"
StateT = TypeVar("StateT")


class ReplayInputError(ValueError):
    """Raised when a canonical replay stream violates causal input invariants."""


class StrategyContractError(RuntimeError):
    """Raised when a Strategy Plugin returns output inconsistent with the input event."""


@dataclass(frozen=True, slots=True)
class ReplayRunManifest:
    engine_version: str
    strategy_id: str
    strategy_version: str
    strategy_fingerprint: str
    instrument_id: InstrumentId
    timeframe: str
    candle_count: int
    input_fingerprint: str
    run_fingerprint: str


@dataclass(frozen=True, slots=True)
class ReplayResult(Generic[StateT]):
    manifest: ReplayRunManifest
    decisions: tuple[StrategyDecision, ...]
    final_state: StateT
    first_event_time: datetime
    last_close_time: datetime
    decision_ids_fingerprint: str
    result_fingerprint: str
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.execution_capability != "NONE":
            raise ValueError("deterministic replay has no execution capability")
        if self.order_execution_enabled:
            raise ValueError("deterministic replay cannot enable order execution")
        if len(self.decisions) != self.manifest.candle_count:
            raise ValueError("replay result must contain exactly one decision per candle")


def replay_candles(
    strategy: StrategyPlugin[StateT],
    candles: Sequence[Candle],
) -> ReplayResult[StateT]:
    """Replay an explicit canonical candle sequence through one Strategy Plugin."""
    stream = tuple(candles)
    instrument_id, timeframe = _validate_stream(stream)
    input_fingerprint = _fingerprint(tuple(_candle_identity(candle) for candle in stream))
    manifest = _build_manifest(
        strategy=strategy,
        instrument_id=instrument_id,
        timeframe=timeframe,
        candle_count=len(stream),
        input_fingerprint=input_fingerprint,
    )

    state = strategy.initial_state()
    decisions: list[StrategyDecision] = []
    for candle in stream:
        transition = strategy.on_candle(state, candle)
        _validate_decision(strategy, candle, transition.decision)
        state = transition.state
        decisions.append(transition.decision)

    frozen_decisions = tuple(decisions)
    decision_ids_fingerprint = _fingerprint(
        tuple(decision.decision_id for decision in frozen_decisions)
    )
    result_fingerprint = _fingerprint(
        {
            "run_fingerprint": manifest.run_fingerprint,
            "decision_ids_fingerprint": decision_ids_fingerprint,
        }
    )
    return ReplayResult(
        manifest=manifest,
        decisions=frozen_decisions,
        final_state=state,
        first_event_time=stream[0].event_time,
        last_close_time=stream[-1].close_time,
        decision_ids_fingerprint=decision_ids_fingerprint,
        result_fingerprint=result_fingerprint,
    )


def _validate_stream(candles: tuple[Candle, ...]) -> tuple[InstrumentId, str]:
    if not candles:
        raise ReplayInputError("replay requires at least one canonical candle")

    instrument_id = candles[0].instrument_id
    timeframe = candles[0].timeframe
    previous: Candle | None = None
    for index, candle in enumerate(candles):
        if candle.instrument_id != instrument_id:
            raise ReplayInputError("replay cannot mix instrument identities")
        if candle.timeframe != timeframe:
            raise ReplayInputError("replay cannot mix timeframes")
        if not candle.safe_for_decision:
            raise ReplayInputError(f"candle {index} is not safe for decision")
        if candle.received_at < candle.close_time:
            raise ReplayInputError(f"candle {index} was observed before it closed")
        if previous is not None:
            if candle.event_time < previous.close_time:
                raise ReplayInputError("replay candles must be ordered and non-overlapping")
            if candle.close_time <= previous.close_time:
                raise ReplayInputError("replay close times must be strictly increasing")
            if candle.received_at < previous.received_at:
                raise ReplayInputError("replay observation times must be non-decreasing")
        previous = candle
    return instrument_id, timeframe


def _build_manifest(
    *,
    strategy: StrategyPlugin[StateT],
    instrument_id: InstrumentId,
    timeframe: str,
    candle_count: int,
    input_fingerprint: str,
) -> ReplayRunManifest:
    _require_token(strategy.strategy_id, "strategy_id")
    _require_token(strategy.strategy_version, "strategy_version")
    _require_sha256(strategy.strategy_fingerprint, "strategy_fingerprint")
    identity = {
        "engine_version": ENGINE_VERSION,
        "strategy_id": strategy.strategy_id,
        "strategy_version": strategy.strategy_version,
        "strategy_fingerprint": strategy.strategy_fingerprint,
        "instrument_id": instrument_id.value,
        "timeframe": timeframe,
        "candle_count": candle_count,
        "input_fingerprint": input_fingerprint,
    }
    return ReplayRunManifest(
        engine_version=ENGINE_VERSION,
        strategy_id=strategy.strategy_id,
        strategy_version=strategy.strategy_version,
        strategy_fingerprint=strategy.strategy_fingerprint,
        instrument_id=instrument_id,
        timeframe=timeframe,
        candle_count=candle_count,
        input_fingerprint=input_fingerprint,
        run_fingerprint=_fingerprint(identity),
    )


def _validate_decision(
    strategy: StrategyPlugin[StateT],
    candle: Candle,
    decision: StrategyDecision,
) -> None:
    if decision.strategy_id != strategy.strategy_id:
        raise StrategyContractError("strategy decision id does not match plugin")
    if decision.strategy_version != strategy.strategy_version:
        raise StrategyContractError("strategy decision version does not match plugin")
    if decision.strategy_fingerprint != strategy.strategy_fingerprint:
        raise StrategyContractError("strategy decision fingerprint does not match plugin")
    if decision.instrument_id != candle.instrument_id:
        raise StrategyContractError("strategy decision instrument does not match candle")
    if decision.event_time != candle.close_time:
        raise StrategyContractError("strategy decision time must equal candle close_time")


def _candle_identity(candle: Candle) -> dict[str, object]:
    return {
        "instrument_id": candle.instrument_id.value,
        "timeframe": candle.timeframe,
        "event_time": candle.event_time.isoformat(),
        "close_time": candle.close_time.isoformat(),
        "open": float(candle.open),
        "high": float(candle.high),
        "low": float(candle.low),
        "close": float(candle.close),
        "volume": None if candle.volume is None else float(candle.volume),
        "source": candle.source,
        "received_at": candle.received_at.isoformat(),
        "is_closed": candle.is_closed,
        "quality_state": candle.quality_state.value,
    }


def _fingerprint(payload: object) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256(canonical.encode("utf-8")).hexdigest()


def _require_token(value: str, field_name: str) -> None:
    if not value or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty normalized token")


def _require_sha256(value: str, field_name: str) -> None:
    if len(value) != 64:
        raise ValueError(f"{field_name} must be sha256 hex")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be sha256 hex") from exc
