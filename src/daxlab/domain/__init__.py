"""Canonical broker- and storage-neutral domain contracts for DAX-BOT NextGen."""

from daxlab.domain.execution import ExecutionIntent, OrderSide
from daxlab.domain.loss_admission import (
    LossExposureAdmissionAction,
    LossExposureAdmissionDecision,
    LossExposureObservation,
    LossExposurePolicy,
    evaluate_loss_exposure_admission,
)
from daxlab.domain.market import Candle, DataQualityState, InstrumentId
from daxlab.domain.risk import (
    InstrumentRiskInputs,
    RiskDecision,
    RiskDecisionAction,
    RiskRequest,
    evaluate_fixed_cash_risk,
)
from daxlab.domain.risk_execution import build_execution_intent_from_risk
from daxlab.domain.risk_policy import (
    FixedCashRiskPolicy,
    build_risk_request_from_policy,
)
from daxlab.domain.session_admission import (
    SessionAdmissionAction,
    SessionAdmissionDecision,
    SessionAdmissionObservation,
    SessionAdmissionPolicy,
    evaluate_session_admission,
)
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
    "FixedCashRiskPolicy",
    "InstrumentId",
    "InstrumentRiskInputs",
    "LossExposureAdmissionAction",
    "LossExposureAdmissionDecision",
    "LossExposureObservation",
    "LossExposurePolicy",
    "OrderSide",
    "RiskDecision",
    "RiskDecisionAction",
    "RiskRequest",
    "SessionAdmissionAction",
    "SessionAdmissionDecision",
    "SessionAdmissionObservation",
    "SessionAdmissionPolicy",
    "StrategyAction",
    "StrategyDecision",
    "TradeDirection",
    "TradePlan",
    "build_execution_intent_from_risk",
    "build_risk_request_from_policy",
    "evaluate_fixed_cash_risk",
    "evaluate_loss_exposure_admission",
    "evaluate_session_admission",
]
