"""Canonical loss/exposure admission policy for new-trade eligibility.

This module consumes explicit already-computed observations. It does not calculate
PnL, size positions, read accounts/brokers, or authorize order submission.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from hashlib import sha256
import json
from math import isfinite


LOSS_EXPOSURE_POLICY_SCHEMA = "DAXLAB_LOSS_EXPOSURE_POLICY_V1"
LOSS_EXPOSURE_OBSERVATION_SCHEMA = "DAXLAB_LOSS_EXPOSURE_OBSERVATION_V1"
LOSS_EXPOSURE_DECISION_SCHEMA = "DAXLAB_LOSS_EXPOSURE_DECISION_V1"


class LossExposureAdmissionAction(StrEnum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"


@dataclass(frozen=True, slots=True)
class LossExposurePolicy:
    currency: str
    daily_drawdown_cap_cash: float
    weekly_drawdown_cap_cash: float
    max_consecutive_losses: int
    max_open_positions: int
    policy_fingerprint: str
    schema_version: str = LOSS_EXPOSURE_POLICY_SCHEMA

    @classmethod
    def build(
        cls,
        *,
        currency: str,
        daily_drawdown_cap_cash: float,
        weekly_drawdown_cap_cash: float,
        max_consecutive_losses: int,
        max_open_positions: int,
    ) -> "LossExposurePolicy":
        payload = _policy_payload(
            currency=currency,
            daily_drawdown_cap_cash=daily_drawdown_cap_cash,
            weekly_drawdown_cap_cash=weekly_drawdown_cap_cash,
            max_consecutive_losses=max_consecutive_losses,
            max_open_positions=max_open_positions,
        )
        return cls(
            currency=currency,
            daily_drawdown_cap_cash=float(daily_drawdown_cap_cash),
            weekly_drawdown_cap_cash=float(weekly_drawdown_cap_cash),
            max_consecutive_losses=max_consecutive_losses,
            max_open_positions=max_open_positions,
            policy_fingerprint=_fingerprint(payload),
        )

    def __post_init__(self) -> None:
        if self.schema_version != LOSS_EXPOSURE_POLICY_SCHEMA:
            raise ValueError("loss/exposure policy schema mismatch")
        expected = _fingerprint(
            _policy_payload(
                currency=self.currency,
                daily_drawdown_cap_cash=self.daily_drawdown_cap_cash,
                weekly_drawdown_cap_cash=self.weekly_drawdown_cap_cash,
                max_consecutive_losses=self.max_consecutive_losses,
                max_open_positions=self.max_open_positions,
            )
        )
        if self.policy_fingerprint != expected:
            raise ValueError("loss/exposure policy fingerprint mismatch")


@dataclass(frozen=True, slots=True)
class LossExposureObservation:
    currency: str
    daily_drawdown_cash: float
    weekly_drawdown_cash: float
    consecutive_losses: int
    open_positions: int
    observation_fingerprint: str
    schema_version: str = LOSS_EXPOSURE_OBSERVATION_SCHEMA

    @classmethod
    def build(
        cls,
        *,
        currency: str,
        daily_drawdown_cash: float,
        weekly_drawdown_cash: float,
        consecutive_losses: int,
        open_positions: int,
    ) -> "LossExposureObservation":
        payload = _observation_payload(
            currency=currency,
            daily_drawdown_cash=daily_drawdown_cash,
            weekly_drawdown_cash=weekly_drawdown_cash,
            consecutive_losses=consecutive_losses,
            open_positions=open_positions,
        )
        return cls(
            currency=currency,
            daily_drawdown_cash=float(daily_drawdown_cash),
            weekly_drawdown_cash=float(weekly_drawdown_cash),
            consecutive_losses=consecutive_losses,
            open_positions=open_positions,
            observation_fingerprint=_fingerprint(payload),
        )

    def __post_init__(self) -> None:
        if self.schema_version != LOSS_EXPOSURE_OBSERVATION_SCHEMA:
            raise ValueError("loss/exposure observation schema mismatch")
        expected = _fingerprint(
            _observation_payload(
                currency=self.currency,
                daily_drawdown_cash=self.daily_drawdown_cash,
                weekly_drawdown_cash=self.weekly_drawdown_cash,
                consecutive_losses=self.consecutive_losses,
                open_positions=self.open_positions,
            )
        )
        if self.observation_fingerprint != expected:
            raise ValueError("loss/exposure observation fingerprint mismatch")


@dataclass(frozen=True, slots=True)
class LossExposureAdmissionDecision:
    action: LossExposureAdmissionAction
    policy_fingerprint: str
    observation_fingerprint: str
    reason_codes: tuple[str, ...]
    decision_fingerprint: str
    schema_version: str = LOSS_EXPOSURE_DECISION_SCHEMA

    @property
    def allowed(self) -> bool:
        return self.action is LossExposureAdmissionAction.ALLOW


def evaluate_loss_exposure_admission(
    *,
    policy: LossExposurePolicy,
    observation: LossExposureObservation,
) -> LossExposureAdmissionDecision:
    blockers: list[str] = []
    if observation.currency != policy.currency:
        blockers.append("RISK_CURRENCY_MISMATCH")
    if observation.daily_drawdown_cash >= policy.daily_drawdown_cap_cash:
        blockers.append("DAILY_DRAWDOWN_CAP")
    if observation.weekly_drawdown_cash >= policy.weekly_drawdown_cap_cash:
        blockers.append("WEEKLY_DRAWDOWN_CAP")
    if observation.consecutive_losses >= policy.max_consecutive_losses:
        blockers.append("CONSECUTIVE_LOSS_LIMIT")
    if observation.open_positions >= policy.max_open_positions:
        blockers.append("MAX_OPEN_POSITIONS")

    reasons = tuple(blockers) if blockers else ("WITHIN_LOSS_EXPOSURE_LIMITS",)
    action = (
        LossExposureAdmissionAction.BLOCK
        if blockers
        else LossExposureAdmissionAction.ALLOW
    )
    payload = {
        "schema_version": LOSS_EXPOSURE_DECISION_SCHEMA,
        "action": action.value,
        "policy_fingerprint": policy.policy_fingerprint,
        "observation_fingerprint": observation.observation_fingerprint,
        "reason_codes": list(reasons),
    }
    return LossExposureAdmissionDecision(
        action=action,
        policy_fingerprint=policy.policy_fingerprint,
        observation_fingerprint=observation.observation_fingerprint,
        reason_codes=reasons,
        decision_fingerprint=_fingerprint(payload),
    )


def _policy_payload(
    *,
    currency: str,
    daily_drawdown_cap_cash: float,
    weekly_drawdown_cap_cash: float,
    max_consecutive_losses: int,
    max_open_positions: int,
) -> dict[str, object]:
    _require_token(currency, "currency")
    _require_positive_finite(daily_drawdown_cap_cash, "daily_drawdown_cap_cash")
    _require_positive_finite(weekly_drawdown_cap_cash, "weekly_drawdown_cap_cash")
    _require_positive_int(max_consecutive_losses, "max_consecutive_losses")
    _require_positive_int(max_open_positions, "max_open_positions")
    return {
        "schema_version": LOSS_EXPOSURE_POLICY_SCHEMA,
        "currency": currency,
        "daily_drawdown_cap_cash": _decimal_text(daily_drawdown_cap_cash),
        "weekly_drawdown_cap_cash": _decimal_text(weekly_drawdown_cap_cash),
        "max_consecutive_losses": max_consecutive_losses,
        "max_open_positions": max_open_positions,
    }


def _observation_payload(
    *,
    currency: str,
    daily_drawdown_cash: float,
    weekly_drawdown_cash: float,
    consecutive_losses: int,
    open_positions: int,
) -> dict[str, object]:
    _require_token(currency, "currency")
    _require_non_negative_finite(daily_drawdown_cash, "daily_drawdown_cash")
    _require_non_negative_finite(weekly_drawdown_cash, "weekly_drawdown_cash")
    _require_non_negative_int(consecutive_losses, "consecutive_losses")
    _require_non_negative_int(open_positions, "open_positions")
    return {
        "schema_version": LOSS_EXPOSURE_OBSERVATION_SCHEMA,
        "currency": currency,
        "daily_drawdown_cash": _decimal_text(daily_drawdown_cash),
        "weekly_drawdown_cash": _decimal_text(weekly_drawdown_cash),
        "consecutive_losses": consecutive_losses,
        "open_positions": open_positions,
    }


def _require_token(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty normalized token")


def _require_positive_finite(value: float, field_name: str) -> None:
    if isinstance(value, bool) or not isfinite(value) or value <= 0:
        raise ValueError(f"{field_name} must be finite and positive")


def _require_non_negative_finite(value: float, field_name: str) -> None:
    if isinstance(value, bool) or not isfinite(value) or value < 0:
        raise ValueError(f"{field_name} must be finite and non-negative")


def _require_positive_int(value: int, field_name: str) -> None:
    if type(value) is not int or value < 1:
        raise ValueError(f"{field_name} must be an integer >= 1")


def _require_non_negative_int(value: int, field_name: str) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field_name} must be a non-negative integer")


def _decimal_text(value: float) -> str:
    return format(Decimal(str(value)).normalize(), "f")


def _fingerprint(payload: object) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256(canonical.encode("utf-8")).hexdigest()
