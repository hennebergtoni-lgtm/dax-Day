"""CAND-001 compatibility adapter for the canonical Strategy Plugin V1 boundary."""

from daxlab.strategies.cand001.adapter import (
    Cand001StrategyBinding,
    Cand001StrategyPlugin,
    adapt_cand001_runtime_candle,
    map_cand001_strategy_decision,
)
from daxlab.strategies.cand001.state_codec import (
    CAND001_STATE_CODEC_ID,
    CAND001_STATE_SCHEMA,
    Cand001PipelineStateCodec,
)

__all__ = [
    "CAND001_STATE_CODEC_ID",
    "CAND001_STATE_SCHEMA",
    "Cand001PipelineStateCodec",
    "Cand001StrategyBinding",
    "Cand001StrategyPlugin",
    "adapt_cand001_runtime_candle",
    "map_cand001_strategy_decision",
]
