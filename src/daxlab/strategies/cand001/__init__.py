"""CAND-001 compatibility adapter for the canonical Strategy Plugin V1 boundary."""

from daxlab.strategies.cand001.adapter import (
    Cand001StrategyBinding,
    Cand001StrategyPlugin,
    adapt_cand001_runtime_candle,
    map_cand001_strategy_decision,
)

__all__ = [
    "Cand001StrategyBinding",
    "Cand001StrategyPlugin",
    "adapt_cand001_runtime_candle",
    "map_cand001_strategy_decision",
]
