"""Canonical broker-neutral pre-trade risk and sizing contracts.

Risk V1 converts a validated strategy TradePlan plus canonical instrument economics
into a deterministic ALLOW/DENY decision. It does not authorize order submission,
PAPER, LIVE, or any broker adapter.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_FLOOR
from enum import StrEnum
from hashlib import sha256
import json
from math import isfinite

from daxlab.domain.market import InstrumentId
from daxlab.domain.strategy import TradePlan


class RiskDecisionAction(StrEnum):
    ALLOW = "ALLOW"
    DENY = "DENY"


@dataclass(frozen=True, slots=True)
class InstrumentRiskInputs:
    """Canonical sizing economics independent from any broker SDK object."""

    instrument_id: InstrumentId
    quantity_min: float
    quantity_step: float
    quantity_max: float
    cash_loss_per_price_unit_per_quantity: float
    currency: str

    def __post_init__(self) -> None:
        for field_name, value in (
            ("quantity_min", self.quantity_min),
            ("quantity_step", self.quantity_step),
            ("quantity_max", self.quantity_max),
            ("cash_loss_per_price_unit_per_quantity", self.cash_loss_per_price_unit_per_quantity),
        ):
            _require_positive_finite(value, field_name)
        _require_token(self.currency, "currency")
        if self.quantity_min > self.quantity_max:
            raise ValueError("quantity_min must be <= quantity_max")
        if not _step_aligned(self.quantity_min, self.quantity_step):
            raise ValueError("quantity_min must align to quantity_step")
        if not _step_aligned(self.quantity_max, self.quantity_step):
            raise ValueError("quantity_max must align to quantity_step")


@dataclass(frozen=True, slots=True)
class RiskRequest:
    """Deterministic sizing request bound to one strategy decision and trade plan."""

    strategy_decision_id: str
    trade_plan: TradePlan
    max_loss_cash: float
    loss_currency: str
    instrument: InstrumentRiskInputs
    request_id: str
    schema_version: str = "DAXLAB_RISK_REQUEST_V1"

    @classmethod
    def build(
        cls,
        *,
        strategy_decision_id: str,
        trade_plan: TradePlan,
        max_loss_cash: float,
        loss_currency: str,
        instrument: InstrumentRiskInputs,
    ) -> "RiskRequest":
        _require_sha256(strategy_decision_id, "strategy_decision_id")
        _require_positive_finite(max_loss_cash, "max_loss_cash")
        _require_token(loss_currency, "loss_currency")
        if trade_plan.instrument_id != instrument.instrument_id:
            raise ValueError("trade plan instrument must match risk instrument")

        identity = {
            "schema_version": "DAXLAB_RISK_REQUEST_V1",
            "strategy_decision_id": strategy_decision_id,
            "trade_plan": {
                "instrument_id": trade_plan.instrument_id.value,
                "direction": trade_plan.direction.value,
                "entry_price": _decimal_text(trade_plan.entry_price),
                "stop_price": _decimal_text(trade_plan.stop_price),
                "target_price": _decimal_text(trade_plan.target_price),
            },
            "max_loss_cash": _decimal_text(max_loss_cash),
            "loss_currency": loss_currency,
            "instrument": {
                "instrument_id": instrument.instrument_id.value,
                "quantity_min": _decimal_text(instrument.quantity_min),
                "quantity_step": _decimal_text(instrument.quantity_step),
                "quantity_max": _decimal_text(instrument.quantity_max),
                "cash_loss_per_price_unit_per_quantity": _decimal_text(
                    instrument.cash_loss_per_price_unit_per_quantity
                ),
                "currency": instrument.currency,
            },
        }
        return cls(
            strategy_decision_id=strategy_decision_id,
            trade_plan=trade_plan,
            max_loss_cash=float(max_loss_cash),
            loss_currency=loss_currency,
            instrument=instrument,
            request_id=_fingerprint(identity),
        )


@dataclass(frozen=True, slots=True)
class RiskDecision:
    """Fail-closed deterministic pre-trade decision; quantity exists only on ALLOW."""

    request_id: str
    action: RiskDecisionAction
    reason_codes: tuple[str, ...]
    quantity: float | None
    decision_id: str
    schema_version: str = "DAXLAB_RISK_DECISION_V1"

    @property
    def allowed(self) -> bool:
        return self.action is RiskDecisionAction.ALLOW

    @classmethod
    def _build(
        cls,
        *,
        request_id: str,
        action: RiskDecisionAction,
        reason_codes: tuple[str, ...],
        quantity: float | None,
    ) -> "RiskDecision":
        _require_sha256(request_id, "request_id")
        normalized_reasons = tuple(reason.strip() for reason in reason_codes)
        if not normalized_reasons or any(not reason for reason in normalized_reasons):
            raise ValueError("reason_codes must contain at least one non-empty reason")
        if len(set(normalized_reasons)) != len(normalized_reasons):
            raise ValueError("reason_codes must be unique and ordered")
        if action is RiskDecisionAction.ALLOW:
            if quantity is None:
                raise ValueError("ALLOW requires quantity")
            _require_positive_finite(quantity, "quantity")
        elif quantity is not None:
            raise ValueError("DENY cannot contain quantity")

        identity = {
            "schema_version": "DAXLAB_RISK_DECISION_V1",
            "request_id": request_id,
            "action": action.value,
            "reason_codes": normalized_reasons,
            "quantity": None if quantity is None else _decimal_text(quantity),
        }
        return cls(
            request_id=request_id,
            action=action,
            reason_codes=normalized_reasons,
            quantity=None if quantity is None else float(quantity),
            decision_id=_fingerprint(identity),
        )


def evaluate_fixed_cash_risk(request: RiskRequest) -> RiskDecision:
    """Size deterministically under a maximum cash-loss budget, or deny safely."""

    instrument = request.instrument
    if request.loss_currency != instrument.currency:
        return RiskDecision._build(
            request_id=request.request_id,
            action=RiskDecisionAction.DENY,
            reason_codes=("CURRENCY_MISMATCH",),
            quantity=None,
        )

    stop_distance = abs(
        Decimal(str(request.trade_plan.entry_price)) - Decimal(str(request.trade_plan.stop_price))
    )
    cash_per_price_unit = Decimal(str(instrument.cash_loss_per_price_unit_per_quantity))
    loss_per_quantity = stop_distance * cash_per_price_unit
    if loss_per_quantity <= 0:
        return RiskDecision._build(
            request_id=request.request_id,
            action=RiskDecisionAction.DENY,
            reason_codes=("NON_POSITIVE_STOP_RISK",),
            quantity=None,
        )

    budget = Decimal(str(request.max_loss_cash))
    step = Decimal(str(instrument.quantity_step))
    raw_quantity = budget / loss_per_quantity
    stepped_quantity = (raw_quantity / step).to_integral_value(rounding=ROUND_FLOOR) * step
    max_quantity = Decimal(str(instrument.quantity_max))
    quantity = min(stepped_quantity, max_quantity)
    min_quantity = Decimal(str(instrument.quantity_min))

    if quantity < min_quantity:
        return RiskDecision._build(
            request_id=request.request_id,
            action=RiskDecisionAction.DENY,
            reason_codes=("RISK_BUDGET_BELOW_MIN_QUANTITY",),
            quantity=None,
        )

    reasons = ("FIXED_CASH_RISK_WITHIN_LIMIT",)
    if stepped_quantity > max_quantity:
        reasons = ("FIXED_CASH_RISK_WITHIN_LIMIT", "CAPPED_AT_MAX_QUANTITY")

    return RiskDecision._build(
        request_id=request.request_id,
        action=RiskDecisionAction.ALLOW,
        reason_codes=reasons,
        quantity=float(quantity),
    )


def _require_positive_finite(value: float, field_name: str) -> None:
    if not isfinite(value) or value <= 0:
        raise ValueError(f"{field_name} must be finite and positive")


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


def _step_aligned(value: float, step: float) -> bool:
    units = Decimal(str(value)) / Decimal(str(step))
    return units == units.to_integral_value()


def _decimal_text(value: float) -> str:
    return format(Decimal(str(value)).normalize(), "f")


def _fingerprint(payload: object) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256(canonical.encode("utf-8")).hexdigest()
