"""Read-only bridge from verified broker economics to canonical Risk V1 inputs.

The bridge consumes normalized BrokerSymbol evidence only. It performs no account
query, no sizing decision, no venue submission and grants no PAPER/LIVE capability.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from math import isfinite

from daxlab.domain.market import InstrumentId
from daxlab.domain.risk import InstrumentRiskInputs
from daxlab.runtime.broker_economics_readiness import assess_broker_economics
from daxlab.runtime.mt5_readonly import BrokerSymbol


BROKER_RISK_INPUT_BINDING_SCHEMA = "DAXLAB_BROKER_RISK_INPUT_BINDING_V1"


@dataclass(frozen=True, slots=True)
class BrokerRiskInputBinding:
    schema_version: str
    canonical_instrument_id: InstrumentId
    broker_symbol: str
    risk_inputs: InstrumentRiskInputs
    source_fingerprint: str
    broker_economics_verified: bool
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != BROKER_RISK_INPUT_BINDING_SCHEMA:
            raise ValueError("broker risk-input binding schema mismatch")
        if self.risk_inputs.instrument_id != self.canonical_instrument_id:
            raise ValueError("risk inputs must preserve canonical instrument identity")
        _require_sha256(self.source_fingerprint, "source_fingerprint")
        if not self.broker_symbol or self.broker_symbol != self.broker_symbol.strip():
            raise ValueError("broker_symbol must be a non-empty normalized token")
        if not self.broker_economics_verified:
            raise ValueError("binding requires verified broker economics")
        if self.execution_capability != "NONE" or self.order_execution_enabled:
            raise ValueError("broker risk-input binding cannot authorize execution")


def bind_verified_broker_economics_to_risk_inputs(
    *,
    canonical_instrument_id: InstrumentId,
    symbol: BrokerSymbol,
    broker_economics_verified: bool,
) -> BrokerRiskInputBinding:
    """Translate verified venue economics into canonical sizing economics."""

    if not broker_economics_verified:
        raise ValueError("broker economics must be externally verified before canonical binding")
    if not symbol.name or symbol.name != symbol.name.strip():
        raise ValueError("broker symbol name must be a non-empty normalized token")
    if symbol.trade_mode.upper() != "FULL":
        raise ValueError("broker symbol trade_mode must be FULL for product risk binding")

    readiness = assess_broker_economics(symbol)
    if not readiness.ready:
        joined = ",".join(readiness.blockers)
        raise ValueError(f"broker economics incomplete: {joined}")

    assert symbol.volume_min is not None
    assert symbol.volume_step is not None
    assert symbol.volume_max is not None
    assert symbol.tick_size is not None
    assert symbol.currency_profit is not None
    assert readiness.risk_tick_value is not None

    numeric = {
        "volume_min": symbol.volume_min,
        "volume_step": symbol.volume_step,
        "volume_max": symbol.volume_max,
        "tick_size": symbol.tick_size,
        "risk_tick_value": readiness.risk_tick_value,
    }
    for field_name, value in numeric.items():
        if not isfinite(value) or value <= 0:
            raise ValueError(f"{field_name} must be finite and positive")

    if not symbol.currency_profit or symbol.currency_profit != symbol.currency_profit.strip():
        raise ValueError("currency_profit must be a non-empty normalized token")

    effective_max = float(symbol.volume_max)
    if symbol.volume_limit is not None:
        if not isfinite(symbol.volume_limit) or symbol.volume_limit <= 0:
            raise ValueError("volume_limit must be finite and positive when supplied")
        effective_max = min(effective_max, float(symbol.volume_limit))

    cash_per_price_unit = float(readiness.risk_tick_value) / float(symbol.tick_size)
    if not isfinite(cash_per_price_unit) or cash_per_price_unit <= 0:
        raise ValueError("derived cash loss per price unit must be finite and positive")

    risk_inputs = InstrumentRiskInputs(
        instrument_id=canonical_instrument_id,
        quantity_min=float(symbol.volume_min),
        quantity_step=float(symbol.volume_step),
        quantity_max=effective_max,
        cash_loss_per_price_unit_per_quantity=cash_per_price_unit,
        currency=symbol.currency_profit,
    )
    source_fingerprint = _fingerprint(
        {
            "schema_version": BROKER_RISK_INPUT_BINDING_SCHEMA,
            "canonical_instrument_id": canonical_instrument_id.value,
            "broker_symbol": symbol.name,
            "trade_mode": symbol.trade_mode.upper(),
            "volume_min": float(symbol.volume_min),
            "volume_step": float(symbol.volume_step),
            "volume_max": float(symbol.volume_max),
            "volume_limit": None if symbol.volume_limit is None else float(symbol.volume_limit),
            "effective_volume_max": effective_max,
            "tick_size": float(symbol.tick_size),
            "risk_tick_value": float(readiness.risk_tick_value),
            "currency_profit": symbol.currency_profit,
            "cash_loss_per_price_unit_per_quantity": cash_per_price_unit,
            "broker_economics_verified": True,
        }
    )
    return BrokerRiskInputBinding(
        schema_version=BROKER_RISK_INPUT_BINDING_SCHEMA,
        canonical_instrument_id=canonical_instrument_id,
        broker_symbol=symbol.name,
        risk_inputs=risk_inputs,
        source_fingerprint=source_fingerprint,
        broker_economics_verified=True,
    )


def _require_sha256(value: str, field_name: str) -> None:
    if len(value) != 64:
        raise ValueError(f"{field_name} must be sha256 hex")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be sha256 hex") from exc


def _fingerprint(payload: object) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256(canonical.encode("utf-8")).hexdigest()
