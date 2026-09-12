"""Deterministic SHADOW-only virtual position lifecycle for CAND-001.

This module fills the narrow stateful gap between an existing ExecutionIntent and
an eventual virtual stop/target result. It does not authorize PAPER or LIVE,
does not submit orders, and does not create a broker adapter.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum

from daxlab.core.execution import Bar, Bracket, ExitReason, Side as CoreSide, resolve_bracket_bar
from daxlab.runtime.bar_identity import closed_bar_identity
from daxlab.runtime.contracts import Candle
from daxlab.runtime.decision import stable_fingerprint
from daxlab.runtime.paper_contracts import (
    ExecutionIntent,
    GapPolicy,
    PaperFillModelConfig,
    PartialFillPolicy,
    SameBarPolicy,
    Side,
)

_SCHEMA_VERSION = "DAXLAB_CAND001_VIRTUAL_LIFECYCLE_V1"
_CANONICAL_TIMEFRAME = "5m"
_LEGACY_TEST_TIMEFRAME_ALIAS = "M5"


class VirtualPositionStatus(StrEnum):
    PENDING_ENTRY = "PENDING_ENTRY"
    OPEN = "OPEN"
    CLOSED = "CLOSED"


@dataclass(frozen=True, slots=True)
class Cand001VirtualLifecycleState:
    schema_version: str
    lifecycle_id: str
    client_order_id: str
    decision_id: str
    run_manifest_fingerprint: str
    fill_model_fingerprint: str
    symbol: str
    side: Side
    quantity: float
    requested_price: float
    stop_price: float
    target_price: float
    requested_at: datetime
    status: VirtualPositionStatus
    filled_at: datetime | None = None
    filled_price: float | None = None
    closed_at: datetime | None = None
    exit_price: float | None = None
    exit_reason: ExitReason = ExitReason.NONE
    last_bar_id: str | None = None
    last_close_time: datetime | None = None
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported virtual lifecycle schema")
        if self.requested_at.tzinfo is None:
            raise ValueError("requested_at must be timezone-aware")
        for value in (self.filled_at, self.closed_at, self.last_close_time):
            if value is not None and value.tzinfo is None:
                raise ValueError("virtual lifecycle timestamps must be timezone-aware")
        if self.execution_capability != "NONE" or self.order_execution_enabled:
            raise ValueError("virtual lifecycle cannot authorize order execution")
        if self.status is VirtualPositionStatus.PENDING_ENTRY:
            if any(value is not None for value in (self.filled_at, self.filled_price, self.closed_at, self.exit_price)):
                raise ValueError("pending lifecycle cannot carry fill or exit fields")
            if self.exit_reason is not ExitReason.NONE:
                raise ValueError("pending lifecycle cannot carry an exit reason")
        elif self.status is VirtualPositionStatus.OPEN:
            if self.filled_at is None or self.filled_price is None:
                raise ValueError("open lifecycle requires a fill")
            if self.closed_at is not None or self.exit_price is not None:
                raise ValueError("open lifecycle cannot carry closed fields")
            if self.exit_reason is not ExitReason.NONE:
                raise ValueError("open lifecycle cannot carry an exit reason")
        elif self.status is VirtualPositionStatus.CLOSED:
            if None in (self.filled_at, self.filled_price, self.closed_at, self.exit_price):
                raise ValueError("closed lifecycle requires fill and exit fields")
            if self.exit_reason is ExitReason.NONE:
                raise ValueError("closed lifecycle requires STOP or TARGET")


def start_cand001_virtual_lifecycle(
    intent: ExecutionIntent,
    *,
    fill_model: PaperFillModelConfig | None = None,
) -> Cand001VirtualLifecycleState:
    """Create a deterministic SHADOW simulation state from an existing intent."""
    model = fill_model or PaperFillModelConfig()
    _require_supported_model(model)
    _validate_intent_geometry(intent)
    lifecycle_id = stable_fingerprint(
        {
            "schema_version": _SCHEMA_VERSION,
            "client_order_id": intent.client_order_id,
            "fill_model_fingerprint": model.fingerprint,
        }
    )
    return Cand001VirtualLifecycleState(
        schema_version=_SCHEMA_VERSION,
        lifecycle_id=lifecycle_id,
        client_order_id=intent.client_order_id,
        decision_id=intent.decision_id,
        run_manifest_fingerprint=intent.run_manifest_fingerprint,
        fill_model_fingerprint=model.fingerprint,
        symbol=intent.symbol,
        side=intent.side,
        quantity=intent.quantity,
        requested_price=intent.requested_price,
        stop_price=intent.stop_price,
        target_price=intent.target_price,
        requested_at=intent.created_at,
        status=VirtualPositionStatus.PENDING_ENTRY,
    )


def advance_cand001_virtual_lifecycle(
    state: Cand001VirtualLifecycleState,
    candle: Candle,
    *,
    fill_model: PaperFillModelConfig | None = None,
) -> Cand001VirtualLifecycleState:
    """Advance one virtual position using one closed, safe, chronological 5m candle."""
    model = fill_model or PaperFillModelConfig()
    _require_supported_model(model)
    if model.fingerprint != state.fill_model_fingerprint:
        raise ValueError("fill-model fingerprint drift")
    if candle.symbol != state.symbol:
        raise ValueError("candle symbol does not match virtual lifecycle")
    if candle.timeframe not in {_CANONICAL_TIMEFRAME, _LEGACY_TEST_TIMEFRAME_ALIAS}:
        raise ValueError("CAND-001 virtual lifecycle requires five-minute candles")
    if state.status is VirtualPositionStatus.CLOSED:
        return state
    if not candle.safe_for_decision:
        return state

    bar_id = closed_bar_identity(
        canonical_symbol=candle.symbol,
        timeframe=candle.timeframe,
        close_time=candle.close_time,
    )
    if state.last_bar_id == bar_id:
        return state
    if state.last_close_time is not None and candle.close_time <= state.last_close_time:
        raise ValueError("virtual lifecycle candle is duplicate or out of order")

    # Never let the decision candle itself create a trade effect. The earliest
    # eligible virtual fill is the first safe 5m bar starting at/after requested_at.
    if state.status is VirtualPositionStatus.PENDING_ENTRY:
        if candle.close_time <= state.requested_at or candle.event_time < state.requested_at:
            return state
        filled = replace(
            state,
            status=VirtualPositionStatus.OPEN,
            filled_at=candle.event_time,
            filled_price=float(candle.open),
            last_bar_id=bar_id,
            last_close_time=candle.close_time,
        )
        return _resolve_exit(filled, candle)

    advanced = replace(
        state,
        last_bar_id=bar_id,
        last_close_time=candle.close_time,
    )
    return _resolve_exit(advanced, candle)


def _resolve_exit(
    state: Cand001VirtualLifecycleState,
    candle: Candle,
) -> Cand001VirtualLifecycleState:
    if state.status is not VirtualPositionStatus.OPEN:
        return state

    core_side = CoreSide.LONG if state.side is Side.BUY else CoreSide.SHORT
    gap_reason = _gap_exit_reason(
        open_price=float(candle.open),
        stop=state.stop_price,
        target=state.target_price,
        side=core_side,
    )
    if gap_reason is not ExitReason.NONE:
        return replace(
            state,
            status=VirtualPositionStatus.CLOSED,
            closed_at=candle.event_time,
            exit_price=float(candle.open),
            exit_reason=gap_reason,
        )

    bar = Bar(
        open=float(candle.open),
        high=float(candle.high),
        low=float(candle.low),
        close=float(candle.close),
    )
    reason = resolve_bracket_bar(
        bar,
        Bracket(stop=state.stop_price, target=state.target_price),
        core_side,
    )
    if reason is ExitReason.NONE:
        return state
    exit_price = state.stop_price if reason is ExitReason.STOP else state.target_price
    return replace(
        state,
        status=VirtualPositionStatus.CLOSED,
        closed_at=candle.close_time,
        exit_price=float(exit_price),
        exit_reason=reason,
    )


def _gap_exit_reason(
    *,
    open_price: float,
    stop: float,
    target: float,
    side: CoreSide,
) -> ExitReason:
    if side is CoreSide.LONG:
        if open_price <= stop:
            return ExitReason.STOP
        if open_price >= target:
            return ExitReason.TARGET
    else:
        if open_price >= stop:
            return ExitReason.STOP
        if open_price <= target:
            return ExitReason.TARGET
    return ExitReason.NONE


def _validate_intent_geometry(intent: ExecutionIntent) -> None:
    if intent.side is Side.BUY and not (
        intent.stop_price < intent.requested_price < intent.target_price
    ):
        raise ValueError("BUY intent geometry is invalid")
    if intent.side is Side.SELL and not (
        intent.target_price < intent.requested_price < intent.stop_price
    ):
        raise ValueError("SELL intent geometry is invalid")


def _require_supported_model(model: PaperFillModelConfig) -> None:
    if model.same_bar_policy is not SameBarPolicy.CONSERVATIVE_STOP_FIRST:
        raise ValueError("unsupported same-bar policy")
    if model.gap_policy is not GapPolicy.FILL_AT_FIRST_AVAILABLE:
        raise ValueError("unsupported gap policy")
    if model.partial_fill_policy is not PartialFillPolicy.DISABLED:
        raise ValueError("CAND-001 virtual lifecycle does not support partial fills")
