"""Canonical single fixed-cash product risk policy.

The policy binds one explicit currency and one per-trade maximum cash-loss ceiling
into Risk V1. It owns no sizing algorithm, broker/account access, execution
capability, research profile or automatic escalation.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
import json
from math import isfinite

from daxlab.domain.risk import InstrumentRiskInputs, RiskRequest
from daxlab.domain.strategy import TradePlan


FIXED_CASH_RISK_POLICY_SCHEMA = "DAXLAB_FIXED_CASH_RISK_POLICY_V1"


@dataclass(frozen=True, slots=True)
class FixedCashRiskPolicy:
    """One explicit product risk ceiling, independent from research profiles."""

    currency: str
    max_loss_cash: float
    policy_fingerprint: str
    schema_version: str = FIXED_CASH_RISK_POLICY_SCHEMA

    @classmethod
    def build(cls, *, currency: str, max_loss_cash: float) -> "FixedCashRiskPolicy":
        _require_token(currency, "currency")
        _require_positive_finite(max_loss_cash, "max_loss_cash")
        identity = {
            "schema_version": FIXED_CASH_RISK_POLICY_SCHEMA,
            "currency": currency,
            "max_loss_cash": _decimal_text(max_loss_cash),
        }
        return cls(
            currency=currency,
            max_loss_cash=float(max_loss_cash),
            policy_fingerprint=_fingerprint(identity),
        )

    def __post_init__(self) -> None:
        if self.schema_version != FIXED_CASH_RISK_POLICY_SCHEMA:
            raise ValueError("fixed-cash risk policy schema mismatch")
        _require_token(self.currency, "currency")
        _require_positive_finite(self.max_loss_cash, "max_loss_cash")
        expected = _fingerprint(
            {
                "schema_version": self.schema_version,
                "currency": self.currency,
                "max_loss_cash": _decimal_text(self.max_loss_cash),
            }
        )
        if self.policy_fingerprint != expected:
            raise ValueError("fixed-cash risk policy fingerprint mismatch")


def build_risk_request_from_policy(
    *,
    policy: FixedCashRiskPolicy,
    strategy_decision_id: str,
    trade_plan: TradePlan,
    instrument: InstrumentRiskInputs,
) -> RiskRequest:
    """Bind policy values into the existing canonical Risk V1 request."""

    if policy.currency != instrument.currency:
        raise ValueError("risk policy currency must match instrument risk currency")
    return RiskRequest.build(
        strategy_decision_id=strategy_decision_id,
        trade_plan=trade_plan,
        max_loss_cash=policy.max_loss_cash,
        loss_currency=policy.currency,
        instrument=instrument,
    )


def _require_positive_finite(value: float, field_name: str) -> None:
    if isinstance(value, bool) or not isfinite(value) or value <= 0:
        raise ValueError(f"{field_name} must be finite and positive")


def _require_token(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty normalized token")


def _decimal_text(value: float) -> str:
    return format(Decimal(str(value)).normalize(), "f")


def _fingerprint(payload: object) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256(canonical.encode("utf-8")).hexdigest()
