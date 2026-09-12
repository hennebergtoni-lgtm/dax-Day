"""Deterministic product-engine surfaces for DAX-BOT NextGen."""

from daxlab.engine.replay import (
    ENGINE_VERSION,
    ReplayInputError,
    ReplayResult,
    ReplayRunManifest,
    StrategyContractError,
    replay_candles,
)

__all__ = [
    "ENGINE_VERSION",
    "ReplayInputError",
    "ReplayResult",
    "ReplayRunManifest",
    "StrategyContractError",
    "replay_candles",
]
