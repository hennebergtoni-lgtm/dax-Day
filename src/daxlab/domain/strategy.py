"""Canonical strategy-domain contracts for DAX-BOT NextGen.

Strategy output stops before risk sizing and execution authorization. A trade plan
expresses market intent only; it has no quantity, broker, account or order fields.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from hashlib import sha256
import json
from math import isfinite

from daxlab.domain.market import InstrumentId


class StrategyAction(StrEnum):
    NO_TRADE = "NO_TRADE"
    TRADE_PLAN = "TRADE_PLAN"


class TradeDirection(StrEnum):
    LONG = "LONG"
    SHORT = "SHORT"


@dataclass(frozen=True, slots=True)
class TradePlan:
    """Broker-neutral price plan with deliberately no risk-authorized quantity."""

    instrument_id: InstrumentId
    direction: TradeDirection
    entry_price: float
    stop_price: float
    target_price: float

    def __post_init__(self) -> None:
        for field_name, value in (
            ("entry_price", self.entry_price),
            ("stop_price", self.stop_price),
            ("target_price", self.target_price),
        ):
            if not isfinite(value) or value <= 0:
                raise ValueError(f"{field_name} must be finite and positive")
        if self.direction is TradeDirection.LONG:
            if not self.stop_price < self.entry_price < self.target_price:
                raise ValueError("LONG plan requires stop < entry < target")
        elif not self.target_price < self.entry_price < self.stop_price:
            raise ValueError("SHORT plan requires target < entry < stop")


@dataclass(frozen=True, slots=True)
class StrategyDecision:
    """Deterministic strategy output before portfolio/risk/execution processing."""

    strategy_id: str
    strategy_version: str
    strategy_fingerprint: str
    event_time: datetime
    instrument_id: InstrumentId
    action: StrategyAction
    reason_codes: tuple[str, ...]
    trade_plan: TradePlan | None
    decision_id: str
    schema_version: str = "DAXLAB_STRATEGY_DECISION_V1"

    @classmethod
    def no_trade(
        cls,
        *,
        strategy_id: str,
        strategy_version: str,
        strategy_fingerprint: str,
        event_time: datetime,
        instrument_id: InstrumentId,
        reason_codes: tuple[str, ...],
    ) -> "StrategyDecision":
        return cls._build(
            strategy_id=strategy_id,
            strategy_version=strategy_version,
            strategy_fingerprint=strategy_fingerprint,
            event_time=event_time,
            instrument_id=instrument_id,
            action=StrategyAction.NO_TRADE,
            reason_codes=reason_codes,
            trade_plan=None,
        )

    @classmethod
    def trade(
        cls,
        *,
        strategy_id: str,
        strategy_version: str,
        strategy_fingerprint: str,
        event_time: datetime,
        instrument_id: InstrumentId,
        reason_codes: tuple[str, ...],
        trade_plan: TradePlan,
    ) -> "StrategyDecision":
        if trade_plan.instrument_id != instrument_id:
            raise ValueError("trade plan instrument must match strategy decision instrument")
        return cls._build(
            strategy_id=strategy_id,
            strategy_version=strategy_version,
            strategy_fingerprint=strategy_fingerprint,
            event_time=event_time,
            instrument_id=instrument_id,
            action=StrategyAction.TRADE_PLAN,
            reason_codes=reason_codes,
            trade_plan=trade_plan,
        )

    @classmethod
    def _build(
        cls,
        *,
        strategy_id: str,
        strategy_version: str,
        strategy_fingerprint: str,
        event_time: datetime,
        instrument_id: InstrumentId,
        action: StrategyAction,
        reason_codes: tuple[str, ...],
        trade_plan: TradePlan | None,
    ) -> "StrategyDecision":
        _require_token(strategy_id, "strategy_id")
        _require_token(strategy_version, "strategy_version")
        _require_sha256(strategy_fingerprint, "strategy_fingerprint")
        _require_utc(event_time, "event_time")
        normalized_reasons = tuple(reason.strip() for reason in reason_codes)
        if not normalized_reasons or any(not reason for reason in normalized_reasons):
            raise ValueError("reason_codes must contain at least one non-empty reason")
        if len(set(normalized_reasons)) != len(normalized_reasons):
            raise ValueError("reason_codes must be unique and ordered")
        if action is StrategyAction.NO_TRADE and trade_plan is not None:
            raise ValueError("NO_TRADE cannot contain a trade plan")
        if action is StrategyAction.TRADE_PLAN and trade_plan is None:
            raise ValueError("TRADE_PLAN requires a trade plan")

        plan_payload: dict[str, object] | None = None
        if trade_plan is not None:
            plan_payload = {
                "instrument_id": trade_plan.instrument_id.value,
                "direction": trade_plan.direction.value,
                "entry_price": float(trade_plan.entry_price),
                "stop_price": float(trade_plan.stop_price),
                "target_price": float(trade_plan.target_price),
            }
        identity = {
            "schema_version": "DAXLAB_STRATEGY_DECISION_V1",
            "strategy_id": strategy_id,
            "strategy_version": strategy_version,
            "strategy_fingerprint": strategy_fingerprint,
            "event_time": event_time.isoformat(),
            "instrument_id": instrument_id.value,
            "action": action.value,
            "reason_codes": normalized_reasons,
            "trade_plan": plan_payload,
        }
        return cls(
            strategy_id=strategy_id,
            strategy_version=strategy_version,
            strategy_fingerprint=strategy_fingerprint,
            event_time=event_time,
            instrument_id=instrument_id,
            action=action,
            reason_codes=normalized_reasons,
            trade_plan=trade_plan,
            decision_id=_fingerprint(identity),
        )


def _fingerprint(payload: object) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256(canonical.encode("utf-8")).hexdigest()


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


def _require_utc(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError(f"{field_name} must be timezone-aware UTC")
