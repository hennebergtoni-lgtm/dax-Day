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

__all__ = [
    "ENGINE_VERSION",
    "ReplayInputError",
    "ReplayResult",
    "ReplayRunManifest",
    "StrategyContractError",
    "assert_replay_decision_compatible",
    "fingerprint_decision_ids",
    "prepare_replay_manifest",
    "replay_candles",
]
