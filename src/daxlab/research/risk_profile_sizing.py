"""Research-only bridge from explicit risk profiles to broker sizing estimates.

No account percentage, allocation amount or equity is inferred here. Every profile
must declare an explicit cash-at-stop budget and remain under one explicit hard
cash-risk cap. The bridge delegates venue translation to broker_risk_sizing and
never creates an ExecutionIntent or broker order.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from daxlab.research.broker_risk_sizing import (
    BrokerRiskSizingEstimate,
    estimate_volume_for_cash_risk,
)
from daxlab.runtime.decision import stable_fingerprint
from daxlab.runtime.mt5_readonly import BrokerSymbol


RISK_PROFILE_SIZING_RESEARCH_VERSION = "RISK_PROFILE_SIZING_RESEARCH_V1"


class RiskProfile(StrEnum):
    BASE = "BASE"
    BOOST = "BOOST"
    HIGH = "HIGH"


@dataclass(frozen=True, slots=True)
class RiskProfileBudgetSpec:
    currency: str
    base_cash_risk: float
    boost_cash_risk: float
    high_cash_risk: float
    hard_cap_cash_risk: float
    policy_version: str = RISK_PROFILE_SIZING_RESEARCH_VERSION

    def __post_init__(self) -> None:
        if self.policy_version != RISK_PROFILE_SIZING_RESEARCH_VERSION:
            raise ValueError("risk profile sizing research version mismatch")
        if not isinstance(self.currency, str) or not self.currency.strip():
            raise ValueError("currency must be non-empty")
        if self.currency != self.currency.strip():
            raise ValueError("currency cannot contain outer whitespace")
        values = (
            self.base_cash_risk,
            self.boost_cash_risk,
            self.high_cash_risk,
            self.hard_cap_cash_risk,
        )
        if any(isinstance(value, bool) or value <= 0 for value in values):
            raise ValueError("all cash-risk values must be positive")
        if not (
            self.base_cash_risk
            <= self.boost_cash_risk
            <= self.high_cash_risk
            <= self.hard_cap_cash_risk
        ):
            raise ValueError(
                "risk profiles must satisfy BASE <= BOOST <= HIGH <= hard cap"
            )

    def cash_risk_for(self, profile: RiskProfile) -> float:
        if not isinstance(profile, RiskProfile):
            raise TypeError("profile must be RiskProfile")
        return {
            RiskProfile.BASE: self.base_cash_risk,
            RiskProfile.BOOST: self.boost_cash_risk,
            RiskProfile.HIGH: self.high_cash_risk,
        }[profile]

    @property
    def fingerprint(self) -> str:
        return stable_fingerprint(
            {
                "policy_version": self.policy_version,
                "currency": self.currency,
                "base_cash_risk": self.base_cash_risk,
                "boost_cash_risk": self.boost_cash_risk,
                "high_cash_risk": self.high_cash_risk,
                "hard_cap_cash_risk": self.hard_cap_cash_risk,
            }
        )


@dataclass(frozen=True, slots=True)
class RiskProfileSizingResearchResult:
    profile: RiskProfile
    policy_version: str
    profile_spec_fingerprint: str
    risk_currency: str
    requested_cash_risk: float
    hard_cap_cash_risk: float
    estimate: BrokerRiskSizingEstimate
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.policy_version != RISK_PROFILE_SIZING_RESEARCH_VERSION:
            raise ValueError("risk profile sizing result version mismatch")
        if self.execution_capability != "NONE" or self.order_execution_enabled:
            raise ValueError("risk profile sizing research cannot authorize execution")
        if len(self.profile_spec_fingerprint) != 64:
            raise ValueError("profile_spec_fingerprint must be sha256 hex")
        try:
            int(self.profile_spec_fingerprint, 16)
        except ValueError as exc:
            raise ValueError("profile_spec_fingerprint must be sha256 hex") from exc
        if self.requested_cash_risk > self.hard_cap_cash_risk:
            raise ValueError("requested cash risk exceeds hard cap")
        if self.estimate.risk_budget_cash != self.requested_cash_risk:
            raise ValueError("sizing estimate is not bound to requested cash risk")
        if self.estimate.risk_currency != self.risk_currency:
            raise ValueError("sizing estimate currency is not bound to profile currency")

    @property
    def fingerprint(self) -> str:
        return stable_fingerprint(
            {
                "profile": self.profile.value,
                "policy_version": self.policy_version,
                "profile_spec_fingerprint": self.profile_spec_fingerprint,
                "risk_currency": self.risk_currency,
                "requested_cash_risk": self.requested_cash_risk,
                "hard_cap_cash_risk": self.hard_cap_cash_risk,
                "estimate_fingerprint": self.estimate.fingerprint,
                "execution_capability": self.execution_capability,
                "order_execution_enabled": self.order_execution_enabled,
            }
        )


def estimate_profile_volume(
    *,
    spec: RiskProfileBudgetSpec,
    profile: RiskProfile,
    symbol: BrokerSymbol,
    stop_distance_price: float,
) -> RiskProfileSizingResearchResult:
    """Resolve one explicit research profile into a non-executable volume estimate."""
    requested = spec.cash_risk_for(profile)
    estimate = estimate_volume_for_cash_risk(
        symbol=symbol,
        stop_distance_price=stop_distance_price,
        risk_budget_cash=requested,
        risk_currency=spec.currency,
    )
    return RiskProfileSizingResearchResult(
        profile=profile,
        policy_version=RISK_PROFILE_SIZING_RESEARCH_VERSION,
        profile_spec_fingerprint=spec.fingerprint,
        risk_currency=spec.currency,
        requested_cash_risk=requested,
        hard_cap_cash_risk=spec.hard_cap_cash_risk,
        estimate=estimate,
    )
