"""FAIL001 failure-mode catalog and technical-control mapping."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class GateCategory(StrEnum):
    DATA_GATE = "DATA_GATE"
    RESEARCH_GATE = "RESEARCH_GATE"
    SETUP_GATE = "SETUP_GATE"
    RISK_GATE = "RISK_GATE"
    EXECUTION_GATE = "EXECUTION_GATE"
    MONITORING_GATE = "MONITORING_GATE"
    UI_GUARDRAIL = "UI_GUARDRAIL"


@dataclass(frozen=True, slots=True)
class FailureControl:
    failure_id: str
    categories: tuple[GateCategory, ...]
    safeguard: str

    def __post_init__(self) -> None:
        if not self.failure_id.strip() or not self.safeguard.strip():
            raise ValueError("failure_id and safeguard are required")
        if not self.categories:
            raise ValueError("at least one technical gate category is required")


FAILURE_CONTROLS = (
    FailureControl("OVERTRADING", (GateCategory.SETUP_GATE,), "NO_SETUP_NO_TRADE"),
    FailureControl("FORCED_TRADES", (GateCategory.SETUP_GATE,), "TRADE_COUNT_NOT_TARGET"),
    FailureControl("OVERCONFIDENCE", (GateCategory.RESEARCH_GATE,), "NO_SHORT_SAMPLE_PROMOTION"),
    FailureControl("REVENGE_RISK", (GateCategory.RISK_GATE,), "NO_LOSS_TRIGGERED_RISK_INCREASE"),
    FailureControl(
        "COST_NEGLECT",
        (GateCategory.RESEARCH_GATE, GateCategory.EXECUTION_GATE),
        "COST_STRESS_AND_EXECUTION_HEALTH",
    ),
    FailureControl("EXCESS_LEVERAGE", (GateCategory.RISK_GATE,), "BOUNDED_RISK_ENGINE"),
    FailureControl("LOOKAHEAD", (GateCategory.RESEARCH_GATE,), "CLOSED_CANDLE_REPLAY_PARITY"),
    FailureControl("OVERFITTING", (GateCategory.RESEARCH_GATE,), "WF_OOS_NEIGHBOURHOOD_VALIDATION"),
    FailureControl("PARAMETER_PROLIFERATION", (GateCategory.RESEARCH_GATE,), "HYPOTHESIS_LED_SEARCH"),
    FailureControl("REGIME_BLINDNESS", (GateCategory.SETUP_GATE,), "REGIME_ELIGIBILITY_GATE"),
    FailureControl("DATA_QUALITY", (GateCategory.DATA_GATE,), "UNSAFE_DATA_NO_TRADE"),
    FailureControl("UNREALISTIC_FILLS", (GateCategory.EXECUTION_GATE,), "EXECUTION_STRESS"),
    FailureControl("STRATEGY_DRIFT", (GateCategory.MONITORING_GATE,), "WARN_OR_BLOCK_NO_SELF_OPTIMIZE"),
    FailureControl(
        "LOSING_STREAK_RULE_CHANGE",
        (GateCategory.RESEARCH_GATE, GateCategory.UI_GUARDRAIL),
        "NO_LIVE_SELF_MODIFICATION",
    ),
    FailureControl("SELECTION_BIAS", (GateCategory.RESEARCH_GATE,), "RETAIN_REJECTED_EVIDENCE"),
    FailureControl("NO_TRADE_BLINDNESS", (GateCategory.MONITORING_GATE,), "LOG_BLOCKED_DECISIONS"),
)


def control_for(failure_id: str) -> FailureControl:
    """Return the single registered technical control for a normalized failure id."""
    normalized = failure_id.strip().upper()
    for control in FAILURE_CONTROLS:
        if control.failure_id == normalized:
            return control
    raise KeyError(normalized)
