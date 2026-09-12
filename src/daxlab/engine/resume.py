"""Deterministic offline interruption and restart/resume for NextGen replay.

This module proves stateful continuation semantics only. It has no host scheduler,
broker connectivity, reconciliation, risk sizing or order-submission capability.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Generic, Sequence, TypeVar

from daxlab.domain.market import Candle
from daxlab.domain.strategy import StrategyDecision
from daxlab.engine.replay import (
    ReplayRunManifest,
    assert_replay_decision_compatible,
    fingerprint_decision_ids,
    prepare_replay_manifest,
)
from daxlab.state.codecs import StrategyStateCodec
from daxlab.state.replay_checkpoint import (
    CheckpointCompatibilityError,
    ProductCheckpointV1,
    assert_checkpoint_compatible,
    build_product_checkpoint,
)
from daxlab.strategies.contracts import StrategyPlugin


StateT = TypeVar("StateT")


@dataclass(frozen=True, slots=True)
class ReplayInterruptionResult(Generic[StateT]):
    manifest: ReplayRunManifest
    decisions: tuple[StrategyDecision, ...]
    state: StateT
    checkpoint: ProductCheckpointV1
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.execution_capability != "NONE" or self.order_execution_enabled:
            raise ValueError("replay interruption cannot authorize execution")
        if len(self.decisions) != self.checkpoint.processed_event_count:
            raise ValueError("interruption decision count must match checkpoint progress")
        if self.checkpoint.run_fingerprint != self.manifest.run_fingerprint:
            raise ValueError("interruption checkpoint run identity mismatch")


@dataclass(frozen=True, slots=True)
class ReplayContinuationResult(Generic[StateT]):
    manifest: ReplayRunManifest
    checkpoint_fingerprint: str
    resumed_from_event_count: int
    decisions: tuple[StrategyDecision, ...]
    final_state: StateT
    suffix_decision_ids_fingerprint: str
    final_state_sha256: str
    continuation_fingerprint: str
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.execution_capability != "NONE" or self.order_execution_enabled:
            raise ValueError("replay continuation cannot authorize execution")
        _require_sha256(self.checkpoint_fingerprint, "checkpoint_fingerprint")
        _require_sha256(
            self.suffix_decision_ids_fingerprint,
            "suffix_decision_ids_fingerprint",
        )
        _require_sha256(self.final_state_sha256, "final_state_sha256")
        _require_sha256(self.continuation_fingerprint, "continuation_fingerprint")
        expected_count = self.manifest.candle_count - self.resumed_from_event_count
        if not 0 <= self.resumed_from_event_count <= self.manifest.candle_count:
            raise ValueError("resumed_from_event_count outside run bounds")
        if len(self.decisions) != expected_count:
            raise ValueError("continuation decision count must equal remaining event count")
        expected = _fingerprint(
            {
                "run_fingerprint": self.manifest.run_fingerprint,
                "checkpoint_fingerprint": self.checkpoint_fingerprint,
                "resumed_from_event_count": self.resumed_from_event_count,
                "suffix_decision_ids_fingerprint": self.suffix_decision_ids_fingerprint,
                "final_state_sha256": self.final_state_sha256,
            }
        )
        if self.continuation_fingerprint != expected:
            raise ValueError("replay continuation fingerprint mismatch")


def interrupt_replay_candles(
    strategy: StrategyPlugin[StateT],
    candles: Sequence[Candle],
    *,
    stop_after: int,
    codec: StrategyStateCodec[StateT],
    config_fingerprint: str,
    source_commit: str,
) -> ReplayInterruptionResult[StateT]:
    """Process only a prefix while binding the checkpoint to the complete run identity."""

    stream = tuple(candles)
    manifest = prepare_replay_manifest(strategy, stream)
    if not 0 <= stop_after <= manifest.candle_count:
        raise ValueError("stop_after outside run bounds")
    codec_id = _codec_id(codec)

    state = strategy.initial_state()
    decisions: list[StrategyDecision] = []
    for candle in stream[:stop_after]:
        transition = strategy.on_candle(state, candle)
        assert_replay_decision_compatible(manifest, candle, transition.decision)
        state = transition.state
        decisions.append(transition.decision)

    state_bytes = _encode_state(codec, state)
    frozen_decisions = tuple(decisions)
    decision_ids_fingerprint = fingerprint_decision_ids(
        tuple(decision.decision_id for decision in frozen_decisions)
    )
    last_event_time = stream[stop_after - 1].close_time if stop_after else None
    last_decision_id = frozen_decisions[-1].decision_id if frozen_decisions else None
    checkpoint = build_product_checkpoint(
        engine_version=manifest.engine_version,
        run_fingerprint=manifest.run_fingerprint,
        strategy_id=manifest.strategy_id,
        strategy_version=manifest.strategy_version,
        strategy_fingerprint=manifest.strategy_fingerprint,
        config_fingerprint=config_fingerprint,
        source_commit=source_commit,
        instrument_id=manifest.instrument_id.value,
        timeframe=manifest.timeframe,
        total_event_count=manifest.candle_count,
        input_fingerprint=manifest.input_fingerprint,
        processed_event_count=stop_after,
        last_event_time=last_event_time,
        last_decision_id=last_decision_id,
        decision_ids_fingerprint=decision_ids_fingerprint,
        state_codec_id=codec_id,
        strategy_state=state_bytes,
    )
    return ReplayInterruptionResult(
        manifest=manifest,
        decisions=frozen_decisions,
        state=state,
        checkpoint=checkpoint,
    )


def resume_replay_candles(
    strategy: StrategyPlugin[StateT],
    candles: Sequence[Candle],
    *,
    checkpoint: ProductCheckpointV1,
    codec: StrategyStateCodec[StateT],
    config_fingerprint: str,
    source_commit: str,
) -> ReplayContinuationResult[StateT]:
    """Restore strategy state and process only events after checkpoint progress."""

    stream = tuple(candles)
    manifest = prepare_replay_manifest(strategy, stream)
    codec_id = _codec_id(codec)
    assert_checkpoint_compatible(
        checkpoint,
        engine_version=manifest.engine_version,
        run_fingerprint=manifest.run_fingerprint,
        strategy_id=manifest.strategy_id,
        strategy_version=manifest.strategy_version,
        strategy_fingerprint=manifest.strategy_fingerprint,
        config_fingerprint=config_fingerprint,
        source_commit=source_commit,
        instrument_id=manifest.instrument_id.value,
        timeframe=manifest.timeframe,
        total_event_count=manifest.candle_count,
        input_fingerprint=manifest.input_fingerprint,
        state_codec_id=codec_id,
    )
    processed = checkpoint.processed_event_count
    if processed:
        expected_last_event = stream[processed - 1].close_time
        if checkpoint.last_event_time != expected_last_event:
            raise CheckpointCompatibilityError("checkpoint last_event_time mismatch")

    restored_state = _decode_state(codec, checkpoint.strategy_state_bytes)
    if _encode_state(codec, restored_state) != checkpoint.strategy_state_bytes:
        raise CheckpointCompatibilityError("checkpoint strategy state is not codec-canonical")

    state = restored_state
    decisions: list[StrategyDecision] = []
    for candle in stream[processed:]:
        transition = strategy.on_candle(state, candle)
        assert_replay_decision_compatible(manifest, candle, transition.decision)
        state = transition.state
        decisions.append(transition.decision)

    frozen_decisions = tuple(decisions)
    suffix_fingerprint = fingerprint_decision_ids(
        tuple(decision.decision_id for decision in frozen_decisions)
    )
    final_state_bytes = _encode_state(codec, state)
    final_state_sha256 = sha256(final_state_bytes).hexdigest()
    continuation_fingerprint = _fingerprint(
        {
            "run_fingerprint": manifest.run_fingerprint,
            "checkpoint_fingerprint": checkpoint.checkpoint_fingerprint,
            "resumed_from_event_count": processed,
            "suffix_decision_ids_fingerprint": suffix_fingerprint,
            "final_state_sha256": final_state_sha256,
        }
    )
    return ReplayContinuationResult(
        manifest=manifest,
        checkpoint_fingerprint=checkpoint.checkpoint_fingerprint,
        resumed_from_event_count=processed,
        decisions=frozen_decisions,
        final_state=state,
        suffix_decision_ids_fingerprint=suffix_fingerprint,
        final_state_sha256=final_state_sha256,
        continuation_fingerprint=continuation_fingerprint,
    )


def _codec_id(codec: StrategyStateCodec[StateT]) -> str:
    value = codec.codec_id
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError("strategy state codec_id must be normalized non-empty text")
    return value


def _encode_state(codec: StrategyStateCodec[StateT], state: StateT) -> bytes:
    payload = codec.encode(state)
    if not isinstance(payload, bytes):
        raise TypeError("strategy state codec encode() must return bytes")
    return payload


def _decode_state(codec: StrategyStateCodec[StateT], payload: bytes) -> StateT:
    return codec.decode(payload)


def _fingerprint(payload: object) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256(canonical.encode("utf-8")).hexdigest()


def _require_sha256(value: str, field_name: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{field_name} must be sha256 hex")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be sha256 hex") from exc
