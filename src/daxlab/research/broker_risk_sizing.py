"""Pure broker-volume sizing research from explicit cash-at-stop risk.

This module is RESEARCH ONLY. It has no account API, no broker/order API and no
execution path. It converts an explicit cash risk budget plus stop distance and
read-only broker economics into a theoretical broker volume. Volume is always
rounded DOWN to the venue step so quantization cannot increase planned cash risk.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_FLOOR
from enum import StrEnum

from daxlab.runtime.broker_economics_readiness import assess_broker_economics
from daxlab.runtime.mt5_readonly import BrokerSymbol


BROKER_RISK_SIZING_RESEARCH_VERSION = "BROKER_RISK_SIZING_RESEARCH_V1"


class BrokerRiskSizingState(StrEnum):
    ESTIMATE_AVAILABLE = "ESTIMATE_AVAILABLE"
    ECONOMICS_INCOMPLETE = "ECONOMICS_INCOMPLETE"
    BELOW_MINIMUM_VOLUME = "BELOW_MINIMUM_VOLUME"


@dataclass(frozen=True, slots=True)
class BrokerRiskSizingEstimate:
    state: BrokerRiskSizingState
    policy_version: str
    symbol: str
    risk_currency: str
    risk_budget_cash: float
    stop_distance_price: float
    risk_tick_value: float | None
    raw_volume: float | None
    volume: float | None
    projected_stop_loss_cash: float | None
    effective_volume_cap: float | None
    blockers: tuple[str, ...]
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.policy_version != BROKER_RISK_SIZING_RESEARCH_VERSION:
            raise ValueError("broker risk sizing research version mismatch")
        if self.execution_capability != "NONE" or self.order_execution_enabled:
            raise ValueError("broker risk sizing research cannot authorize execution")
        if self.risk_budget_cash <= 0:
            raise ValueError("risk_budget_cash must be positive")
        if self.stop_distance_price <= 0:
            raise ValueError("stop_distance_price must be positive")
        if self.state is BrokerRiskSizingState.ESTIMATE_AVAILABLE:
            if self.blockers:
                raise ValueError("available sizing estimate cannot carry blockers")
            if self.volume is None or self.volume <= 0:
                raise ValueError("available sizing estimate requires positive volume")
            if self.projected_stop_loss_cash is None:
                raise ValueError("available sizing estimate requires projected stop loss")
            # Quantization/capping must never raise cash-at-stop risk above budget.
            tolerance = max(1e-9, self.risk_budget_cash * 1e-12)
            if self.projected_stop_loss_cash > self.risk_budget_cash + tolerance:
                raise ValueError("projected stop loss exceeds explicit risk budget")
        elif not self.blockers:
            raise ValueError("unavailable sizing estimate requires blockers")

    @property
    def available(self) -> bool:
        return self.state is BrokerRiskSizingState.ESTIMATE_AVAILABLE


def estimate_volume_for_cash_risk(
    *,
    symbol: BrokerSymbol,
    stop_distance_price: float,
    risk_budget_cash: float,
    risk_currency: str,
) -> BrokerRiskSizingEstimate:
    """Return a conservative theoretical volume; never an executable order size."""
    if isinstance(stop_distance_price, bool) or stop_distance_price <= 0:
        raise ValueError("stop_distance_price must be positive")
    if isinstance(risk_budget_cash, bool) or risk_budget_cash <= 0:
        raise ValueError("risk_budget_cash must be positive")
    if not isinstance(risk_currency, str) or not risk_currency.strip():
        raise ValueError("risk_currency must be non-empty")

    readiness = assess_broker_economics(symbol)
    if not readiness.ready:
        return _unavailable(
            state=BrokerRiskSizingState.ECONOMICS_INCOMPLETE,
            symbol=symbol,
            stop_distance_price=stop_distance_price,
            risk_budget_cash=risk_budget_cash,
            risk_currency=risk_currency,
            risk_tick_value=readiness.risk_tick_value,
            blockers=readiness.blockers,
        )

    assert readiness.risk_tick_value is not None
    assert symbol.tick_size is not None
    assert symbol.volume_min is not None
    assert symbol.volume_step is not None
    assert symbol.volume_max is not None
    assert symbol.currency_profit is not None

    if risk_currency != symbol.currency_profit:
        return _unavailable(
            state=BrokerRiskSizingState.ECONOMICS_INCOMPLETE,
            symbol=symbol,
            stop_distance_price=stop_distance_price,
            risk_budget_cash=risk_budget_cash,
            risk_currency=risk_currency,
            risk_tick_value=readiness.risk_tick_value,
            blockers=("RISK_CURRENCY_MISMATCH",),
        )

    stop = Decimal(str(stop_distance_price))
    tick_size = Decimal(str(symbol.tick_size))
    tick_value = Decimal(str(readiness.risk_tick_value))
    budget = Decimal(str(risk_budget_cash))
    step = Decimal(str(symbol.volume_step))
    minimum = Decimal(str(symbol.volume_min))
    maximum = Decimal(str(symbol.volume_max))

    ticks_to_stop = stop / tick_size
    loss_per_volume = ticks_to_stop * tick_value
    if loss_per_volume <= 0:
        raise ValueError("derived cash loss per volume must be positive")

    raw_volume = budget / loss_per_volume
    stepped_volume = (raw_volume / step).to_integral_value(rounding=ROUND_FLOOR) * step

    effective_cap = maximum
    if symbol.volume_limit is not None and symbol.volume_limit > 0:
        effective_cap = min(effective_cap, Decimal(str(symbol.volume_limit)))
    capped_volume = min(stepped_volume, effective_cap)
    # Re-quantize after a non-step-aligned cap, always downward.
    capped_volume = (capped_volume / step).to_integral_value(rounding=ROUND_FLOOR) * step

    if capped_volume < minimum or capped_volume <= 0:
        return _unavailable(
            state=BrokerRiskSizingState.BELOW_MINIMUM_VOLUME,
            symbol=symbol,
            stop_distance_price=stop_distance_price,
            risk_budget_cash=risk_budget_cash,
            risk_currency=risk_currency,
            risk_tick_value=readiness.risk_tick_value,
            blockers=("RISK_BUDGET_BELOW_MINIMUM_VOLUME",),
            raw_volume=float(raw_volume),
            effective_volume_cap=float(effective_cap),
        )

    projected = capped_volume * loss_per_volume
    return BrokerRiskSizingEstimate(
        state=BrokerRiskSizingState.ESTIMATE_AVAILABLE,
        policy_version=BROKER_RISK_SIZING_RESEARCH_VERSION,
        symbol=symbol.name,
        risk_currency=risk_currency,
        risk_budget_cash=float(budget),
        stop_distance_price=float(stop),
        risk_tick_value=float(tick_value),
        raw_volume=float(raw_volume),
        volume=float(capped_volume),
        projected_stop_loss_cash=float(projected),
        effective_volume_cap=float(effective_cap),
        blockers=(),
    )


def _unavailable(
    *,
    state: BrokerRiskSizingState,
    symbol: BrokerSymbol,
    stop_distance_price: float,
    risk_budget_cash: float,
    risk_currency: str,
    risk_tick_value: float | None,
    blockers: tuple[str, ...],
    raw_volume: float | None = None,
    effective_volume_cap: float | None = None,
) -> BrokerRiskSizingEstimate:
    return BrokerRiskSizingEstimate(
        state=state,
        policy_version=BROKER_RISK_SIZING_RESEARCH_VERSION,
        symbol=symbol.name,
        risk_currency=risk_currency,
        risk_budget_cash=float(risk_budget_cash),
        stop_distance_price=float(stop_distance_price),
        risk_tick_value=risk_tick_value,
        raw_volume=raw_volume,
        volume=None,
        projected_stop_loss_cash=None,
        effective_volume_cap=effective_volume_cap,
        blockers=tuple(dict.fromkeys(blockers)),
    )
