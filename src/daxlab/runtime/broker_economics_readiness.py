"""Read-only broker-economics readiness assessment for future demo sizing research.

This module does NOT calculate an order quantity, does NOT inspect account balance,
does NOT authorize PAPER/LIVE and has no broker API. It only classifies whether a
resolved ``BrokerSymbol`` carries enough positive venue metadata to begin a
separate, versioned sizing/economics research step.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from daxlab.runtime.mt5_readonly import BrokerSymbol


class BrokerEconomicsState(StrEnum):
    READY_FOR_SIZING_RESEARCH = "READY_FOR_SIZING_RESEARCH"
    INCOMPLETE = "INCOMPLETE"


@dataclass(frozen=True, slots=True)
class BrokerEconomicsReadiness:
    state: BrokerEconomicsState
    blockers: tuple[str, ...]
    symbol: str
    risk_tick_value: float | None
    margin_metadata_observed: bool
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.execution_capability != "NONE" or self.order_execution_enabled:
            raise ValueError("broker economics readiness cannot authorize execution")
        if self.state is BrokerEconomicsState.READY_FOR_SIZING_RESEARCH and self.blockers:
            raise ValueError("ready broker economics cannot carry blockers")
        if self.state is BrokerEconomicsState.INCOMPLETE and not self.blockers:
            raise ValueError("incomplete broker economics requires blockers")

    @property
    def ready(self) -> bool:
        return self.state is BrokerEconomicsState.READY_FOR_SIZING_RESEARCH


def assess_broker_economics(symbol: BrokerSymbol) -> BrokerEconomicsReadiness:
    """Assess venue metadata only; readiness is not PAPER/demo authorization."""
    blockers: list[str] = []

    for field, blocker in (
        (symbol.contract_size, "CONTRACT_SIZE_MISSING"),
        (symbol.volume_min, "VOLUME_MIN_MISSING"),
        (symbol.volume_step, "VOLUME_STEP_MISSING"),
        (symbol.volume_max, "VOLUME_MAX_MISSING"),
        (symbol.tick_size, "TICK_SIZE_MISSING"),
    ):
        if field is None or field <= 0:
            blockers.append(blocker)

    if symbol.currency_profit is None:
        blockers.append("CURRENCY_PROFIT_MISSING")
    if symbol.currency_margin is None:
        blockers.append("CURRENCY_MARGIN_MISSING")

    tick_candidates = tuple(
        value
        for value in (
            symbol.tick_value_loss,
            symbol.tick_value_profit,
            symbol.tick_value,
        )
        if value is not None and value > 0
    )
    risk_tick_value = max(tick_candidates) if tick_candidates else None
    if risk_tick_value is None:
        blockers.append("POSITIVE_TICK_VALUE_UNVERIFIED")

    if (
        symbol.volume_min is not None
        and symbol.volume_max is not None
        and symbol.volume_min > symbol.volume_max
    ):
        blockers.append("VOLUME_RANGE_INVALID")
    if (
        symbol.volume_step is not None
        and symbol.volume_max is not None
        and symbol.volume_step > symbol.volume_max
    ):
        blockers.append("VOLUME_STEP_INVALID")

    margin_metadata_observed = bool(
        symbol.currency_margin
        and (
            (symbol.margin_initial is not None and symbol.margin_initial > 0)
            or (symbol.margin_maintenance is not None and symbol.margin_maintenance > 0)
        )
    )

    unique = tuple(dict.fromkeys(blockers))
    state = (
        BrokerEconomicsState.READY_FOR_SIZING_RESEARCH
        if not unique
        else BrokerEconomicsState.INCOMPLETE
    )
    return BrokerEconomicsReadiness(
        state=state,
        blockers=unique,
        symbol=symbol.name,
        risk_tick_value=risk_tick_value,
        margin_metadata_observed=margin_metadata_observed,
    )
