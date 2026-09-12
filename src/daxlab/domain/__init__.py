"""Canonical broker- and storage-neutral domain contracts for DAX-BOT NextGen."""

from daxlab.domain.execution import ExecutionIntent, OrderSide
from daxlab.domain.market import Candle, DataQualityState, InstrumentId
from daxlab.domain.risk import (
    InstrumentRiskInputs,
    RiskDecision,
    RiskDecisionAction,
    RiskRequest,
    evaluate_fixed_cash_risk,
)
from daxlab.domain.risk_execution import build_execution_intent_from_risk
from daxlab.domain.strategy import (
    StrategyAction,
    StrategyDecision,
    TradeDirection,
    TradePlan,
)

__all__ = [
    "Candle",
    "DataQualityState",
    "ExecutionIntent",
    "InstrumentId",
    "InstrumentRiskInputs",
    "OrderSide",
    "RiskDecision",
    "RiskDecisionAction",
    "RiskRequest",
    "StrategyAction",
    "StrategyDecision",
    "TradeDirection",
    "TradePlan",
    "build_execution_intent_from_risk",
    "evaluate_fixed_cash_risk",
]
