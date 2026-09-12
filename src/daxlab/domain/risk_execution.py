"""Canonical bridge from approved pre-trade risk to broker-neutral execution intent.

The bridge preserves StrategyDecision identity as ExecutionIntent.decision_id and
binds the complete Risk V1 approval chain into provenance_fingerprint. It creates
product intent only; it has no broker adapter, submission API, PAPER or LIVE
capability.
"""

from __future__ import annotations

from datetime import datetime
from hashlib import sha256
import json

from daxlab.domain.execution import ExecutionIntent, OrderSide
from daxlab.domain.risk import (
    RiskDecision,
    RiskDecisionAction,
    RiskRequest,
    evaluate_fixed_cash_risk,
)
from daxlab.domain.strategy import TradeDirection


_PROVENANCE_SCHEMA = "DAXLAB_RISK_TO_EXECUTION_PROVENANCE_V1"


def build_execution_intent_from_risk(
    *,
    request: RiskRequest,
    decision: RiskDecision,
    created_at: datetime,
) -> ExecutionIntent:
    """Build deterministic intent only from the exact canonical ALLOW decision."""

    canonical_request = RiskRequest.build(
        strategy_decision_id=request.strategy_decision_id,
        trade_plan=request.trade_plan,
        max_loss_cash=request.max_loss_cash,
        loss_currency=request.loss_currency,
        instrument=request.instrument,
    )
    if canonical_request != request:
        raise ValueError("risk request identity does not match canonical request")

    expected_decision = evaluate_fixed_cash_risk(canonical_request)
    if expected_decision != decision:
        raise ValueError("risk decision does not match canonical risk evaluation")
    if decision.action is not RiskDecisionAction.ALLOW or decision.quantity is None:
        raise ValueError("ExecutionIntent requires an ALLOW risk decision with quantity")

    plan = canonical_request.trade_plan
    if plan.direction is TradeDirection.LONG:
        side = OrderSide.BUY
    elif plan.direction is TradeDirection.SHORT:
        side = OrderSide.SELL
    else:  # pragma: no cover - TradePlan constrains the enum
        raise ValueError("trade plan direction must be LONG or SHORT")

    provenance_fingerprint = _fingerprint(
        {
            "schema_version": _PROVENANCE_SCHEMA,
            "strategy_decision_id": canonical_request.strategy_decision_id,
            "risk_request_id": canonical_request.request_id,
            "risk_decision_id": decision.decision_id,
        }
    )

    return ExecutionIntent.build(
        decision_id=canonical_request.strategy_decision_id,
        provenance_fingerprint=provenance_fingerprint,
        created_at=created_at,
        instrument_id=plan.instrument_id,
        side=side,
        quantity=decision.quantity,
        requested_price=plan.entry_price,
        stop_price=plan.stop_price,
        target_price=plan.target_price,
    )


def _fingerprint(payload: object) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256(canonical.encode("utf-8")).hexdigest()
