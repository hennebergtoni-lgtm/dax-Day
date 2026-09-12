"""Deterministic product-engine surfaces for DAX-BOT NextGen."""

from daxlab.engine.replay import (
    ENGINE_VERSION,
    ReplayInputError,
    ReplayResult,
    ReplayRunManifest,
    StrategyContractError,
    assert_replay_decision_compatible,
    fingerprint_decision_ids,
    prepare_replay_manifest,
    replay_candles,
)
from daxlab.engine.resume import (
    ReplayContinuationResult,
    ReplayInterruptionResult,
    interrupt_replay_candles,
    resume_replay_candles,
)

__all__ = [
    "ENGINE_VERSION",
    "ReplayContinuationResult",
    "ReplayInputError",
    "ReplayInterruptionResult",
    "ReplayResult",
    "ReplayRunManifest",
    "StrategyContractError",
    "assert_replay_decision_compatible",
    "fingerprint_decision_ids",
    "interrupt_replay_candles",
    "prepare_replay_manifest",
    "replay_candles",
    "resume_replay_candles",
]
