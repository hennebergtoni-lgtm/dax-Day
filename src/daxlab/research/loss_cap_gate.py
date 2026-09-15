"""Research-only loss/drawdown admission gate.

The gate consumes already-computed risk observations. It does not calculate PnL,
read an account, size positions, alter strategy signals or submit orders. Its only
job is to produce an auditable ALLOW/BLOCK research decision from explicit caps.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from daxlab.runtime.decision import stable_fingerprint


LOSS_CAP_GATE_RESEARCH_VERSION = "LOSS_CAP_GATE_RESEARCH_V1"


class LossCapGateState(StrEnum):
    ALLOW_RESEARCH_ADMISSION = "ALLOW_RESEARCH_ADMISSION"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True, slots=True)
class LossCapPolicy:
    currency: str
    daily_drawdown_cap_cash: float
    weekly_drawdown_cap_cash: float
    max_consecutive_losses: int
    max_open_positions: int
    policy_version: str = LOSS_CAP_GATE_RESEARCH_VERSION

    def __post_init__(self) -> None:
        if self.policy_version != LOSS_CAP_GATE_RESEARCH_VERSION:
            raise ValueError("loss-cap policy version mismatch")
        if not isinstance(self.currency, str) or not self.currency.strip():
            raise ValueError("currency must be non-empty")
        if self.currency != self.currency.strip():
            raise ValueError("currency cannot contain outer whitespace")
        for value, field in (
            (self.daily_drawdown_cap_cash, "daily_drawdown_cap_cash"),
            (self.weekly_drawdown_cap_cash, "weekly_drawdown_cap_cash"),
        ):
            if isinstance(value, bool) or value <= 0:
                raise ValueError(f"{field} must be positive")
        for value, field in (
            (self.max_consecutive_losses, "max_consecutive_losses"),
            (self.max_open_positions, "max_open_positions"),
        ):
            if type(value) is not int or value < 1:
                raise ValueError(f"{field} must be an integer >= 1")

    @property
    def fingerprint(self) -> str:
        return stable_fingerprint(
            {
                "policy_version": self.policy_version,
                "currency": self.currency,
                "daily_drawdown_cap_cash": self.daily_drawdown_cap_cash,
                "weekly_drawdown_cap_cash": self.weekly_drawdown_cap_cash,
                "max_consecutive_losses": self.max_consecutive_losses,
                "max_open_positions": self.max_open_positions,
            }
        )


@dataclass(frozen=True, slots=True)
class LossCapObservation:
    currency: str
    daily_drawdown_cash: float
    weekly_drawdown_cash: float
    consecutive_losses: int
    open_positions: int

    def __post_init__(self) -> None:
        if not isinstance(self.currency, str) or not self.currency.strip():
            raise ValueError("currency must be non-empty")
        if self.currency != self.currency.strip():
            raise ValueError("currency cannot contain outer whitespace")
        for value, field in (
            (self.daily_drawdown_cash, "daily_drawdown_cash"),
            (self.weekly_drawdown_cash, "weekly_drawdown_cash"),
        ):
            if isinstance(value, bool) or value < 0:
                raise ValueError(f"{field} must be non-negative")
        for value, field in (
            (self.consecutive_losses, "consecutive_losses"),
            (self.open_positions, "open_positions"),
        ):
            if type(value) is not int or value < 0:
                raise ValueError(f"{field} must be a non-negative integer")

    @property
    def fingerprint(self) -> str:
        return stable_fingerprint(
            {
                "currency": self.currency,
                "daily_drawdown_cash": self.daily_drawdown_cash,
                "weekly_drawdown_cash": self.weekly_drawdown_cash,
                "consecutive_losses": self.consecutive_losses,
                "open_positions": self.open_positions,
            }
        )


@dataclass(frozen=True, slots=True)
class LossCapGateDecision:
    state: LossCapGateState
    policy_fingerprint: str
    observation_fingerprint: str
    blockers: tuple[str, ...]
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.execution_capability != "NONE" or self.order_execution_enabled:
            raise ValueError("loss-cap research gate cannot authorize execution")
        for value, field in (
            (self.policy_fingerprint, "policy_fingerprint"),
            (self.observation_fingerprint, "observation_fingerprint"),
        ):
            if len(value) != 64:
                raise ValueError(f"{field} must be sha256 hex")
            try:
                int(value, 16)
            except ValueError as exc:
                raise ValueError(f"{field} must be sha256 hex") from exc
        if self.state is LossCapGateState.ALLOW_RESEARCH_ADMISSION and self.blockers:
            raise ValueError("ALLOW decision cannot carry blockers")
        if self.state is LossCapGateState.BLOCKED and not self.blockers:
            raise ValueError("BLOCKED decision requires blockers")

    @property
    def allowed(self) -> bool:
        return self.state is LossCapGateState.ALLOW_RESEARCH_ADMISSION

    @property
    def fingerprint(self) -> str:
        return stable_fingerprint(
            {
                "state": self.state.value,
                "policy_fingerprint": self.policy_fingerprint,
                "observation_fingerprint": self.observation_fingerprint,
                "blockers": list(self.blockers),
                "execution_capability": self.execution_capability,
                "order_execution_enabled": self.order_execution_enabled,
            }
        )


def evaluate_loss_caps(
    *,
    policy: LossCapPolicy,
    observation: LossCapObservation,
) -> LossCapGateDecision:
    """Evaluate explicit caps; boundary equality blocks new research admission."""
    blockers: list[str] = []
    if observation.currency != policy.currency:
        blockers.append("RISK_CURRENCY_MISMATCH")
    if observation.daily_drawdown_cash >= policy.daily_drawdown_cap_cash:
        blockers.append("DAILY_DRAWDOWN_CAP")
    if observation.weekly_drawdown_cash >= policy.weekly_drawdown_cap_cash:
        blockers.append("WEEKLY_DRAWDOWN_CAP")
    if observation.consecutive_losses >= policy.max_consecutive_losses:
        blockers.append("CONSECUTIVE_LOSS_COOLDOWN")
    if observation.open_positions >= policy.max_open_positions:
        blockers.append("MAX_OPEN_POSITIONS")

    unique = tuple(dict.fromkeys(blockers))
    return LossCapGateDecision(
        state=(
            LossCapGateState.BLOCKED
            if unique
            else LossCapGateState.ALLOW_RESEARCH_ADMISSION
        ),
        policy_fingerprint=policy.fingerprint,
        observation_fingerprint=observation.fingerprint,
        blockers=unique,
    )
