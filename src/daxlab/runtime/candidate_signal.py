"""Pure closed-bar signal-state transition for DAX-BOT CAND-001.

No broker, paper adapter, persistence or side effects live here. The caller owns
state persistence and feeds exactly one canonical closed Candle per transition.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from enum import StrEnum
from zoneinfo import ZoneInfo

from daxlab.runtime.candidate_config import Cand001Config
from daxlab.runtime.contracts import Candle
from daxlab.runtime.decision import stable_fingerprint


_OR_SLOTS = ("09:00", "09:05", "09:10")


class SignalDirection(StrEnum):
    NONE = "NONE"
    LONG = "LONG"
    SHORT = "SHORT"


class SignalReason(StrEnum):
    OUTSIDE_SESSION = "OUTSIDE_SESSION"
    DATA_UNSAFE = "DATA_UNSAFE"
    OR_BUILDING = "OR_BUILDING"
    OR_READY = "OR_READY"
    OR_INCOMPLETE = "OR_INCOMPLETE"
    NO_BREAKOUT = "NO_BREAKOUT"
    LONG_BREAKOUT = "LONG_BREAKOUT"
    SHORT_BREAKOUT = "SHORT_BREAKOUT"
    DUPLICATE_BAR = "DUPLICATE_BAR"
    OUT_OF_ORDER_BAR = "OUT_OF_ORDER_BAR"


@dataclass(frozen=True, slots=True)
class Cand001SignalState:
    """Minimal persisted strategy state required across a sliding market-data window."""

    session_date: str | None = None
    or_high: float | None = None
    or_low: float | None = None
    or_slots: tuple[str, ...] = ()
    last_close_time: datetime | None = None

    def __post_init__(self) -> None:
        if (self.or_high is None) != (self.or_low is None):
            raise ValueError("or_high and or_low must both be set or both be absent")
        if self.or_high is not None and self.or_low is not None and self.or_high < self.or_low:
            raise ValueError("or_high cannot be below or_low")
        if any(slot not in _OR_SLOTS for slot in self.or_slots):
            raise ValueError("unknown opening-range slot")
        canonical = tuple(slot for slot in _OR_SLOTS if slot in self.or_slots)
        if self.or_slots != canonical:
            raise ValueError("opening-range slots must be unique and canonical")
        if self.or_slots and self.session_date is None:
            raise ValueError("opening-range slots require session_date")
        if self.last_close_time is not None and self.last_close_time.tzinfo is None:
            raise ValueError("last_close_time must be timezone-aware")

    @property
    def or_complete(self) -> bool:
        return self.or_slots == _OR_SLOTS and self.or_high is not None and self.or_low is not None


@dataclass(frozen=True, slots=True)
class Cand001Signal:
    event_time: datetime
    close_time: datetime
    direction: SignalDirection
    reason: SignalReason
    or_high: float | None
    or_low: float | None
    trigger_price: float | None
    data_fingerprint: str


@dataclass(frozen=True, slots=True)
class Cand001Transition:
    state: Cand001SignalState
    signal: Cand001Signal


def transition_cand001(
    state: Cand001SignalState,
    candle: Candle,
    *,
    config: Cand001Config | None = None,
) -> Cand001Transition:
    """Advance CAND-001 by one canonical closed M5 candle, without side effects."""
    cfg = config or Cand001Config()
    if candle.symbol != cfg.symbol:
        raise ValueError(f"CAND-001 requires symbol {cfg.symbol!r}")
    if candle.timeframe != cfg.bar_timeframe:
        raise ValueError(f"CAND-001 requires timeframe {cfg.bar_timeframe!r}")
    if candle.close_time - candle.event_time != timedelta(minutes=5):
        raise ValueError("CAND-001 requires exact five-minute candles")

    fingerprint = stable_fingerprint(
        {"state_before": state, "candle": candle, "config": cfg}
    )

    if state.last_close_time is not None:
        if candle.close_time == state.last_close_time:
            return Cand001Transition(
                state=state,
                signal=_signal(candle, state, SignalDirection.NONE, SignalReason.DUPLICATE_BAR, fingerprint),
            )
        if candle.close_time < state.last_close_time:
            return Cand001Transition(
                state=state,
                signal=_signal(candle, state, SignalDirection.NONE, SignalReason.OUT_OF_ORDER_BAR, fingerprint),
            )

    if not candle.safe_for_decision:
        return Cand001Transition(
            state=state,
            signal=_signal(candle, state, SignalDirection.NONE, SignalReason.DATA_UNSAFE, fingerprint),
        )

    tz = ZoneInfo(cfg.session_timezone)
    event_local = candle.event_time.astimezone(tz)
    close_local = candle.close_time.astimezone(tz)
    session_date = event_local.date().isoformat()

    working = state
    if working.session_date != session_date:
        working = Cand001SignalState(session_date=session_date)

    session_start = _clock(cfg.session_start)
    session_end = _clock(cfg.session_end)
    event_clock = event_local.timetz().replace(tzinfo=None)
    close_clock = close_local.timetz().replace(tzinfo=None)

    if event_clock < session_start or close_clock > session_end:
        next_state = _with_last_close(working, candle.close_time)
        return Cand001Transition(
            state=next_state,
            signal=_signal(candle, next_state, SignalDirection.NONE, SignalReason.OUTSIDE_SESSION, fingerprint),
        )

    slot = event_local.strftime("%H:%M")
    if slot in _OR_SLOTS:
        if slot in working.or_slots:
            next_state = _with_last_close(working, candle.close_time)
            return Cand001Transition(
                state=next_state,
                signal=_signal(candle, next_state, SignalDirection.NONE, SignalReason.DUPLICATE_BAR, fingerprint),
            )
        next_high = candle.high if working.or_high is None else max(working.or_high, candle.high)
        next_low = candle.low if working.or_low is None else min(working.or_low, candle.low)
        next_slots = tuple(item for item in _OR_SLOTS if item in (*working.or_slots, slot))
        next_state = Cand001SignalState(
            session_date=session_date,
            or_high=next_high,
            or_low=next_low,
            or_slots=next_slots,
            last_close_time=candle.close_time,
        )
        reason = SignalReason.OR_READY if next_state.or_complete else SignalReason.OR_BUILDING
        return Cand001Transition(
            state=next_state,
            signal=_signal(candle, next_state, SignalDirection.NONE, reason, fingerprint),
        )

    first_breakout_time = time(9, 15)
    next_state = _with_last_close(working, candle.close_time)
    if event_clock < first_breakout_time or not working.or_complete:
        return Cand001Transition(
            state=next_state,
            signal=_signal(candle, next_state, SignalDirection.NONE, SignalReason.OR_INCOMPLETE, fingerprint),
        )

    assert working.or_high is not None and working.or_low is not None
    if candle.close > working.or_high:
        return Cand001Transition(
            state=next_state,
            signal=_signal(
                candle,
                next_state,
                SignalDirection.LONG,
                SignalReason.LONG_BREAKOUT,
                fingerprint,
                trigger_price=candle.close,
            ),
        )
    if candle.close < working.or_low:
        return Cand001Transition(
            state=next_state,
            signal=_signal(
                candle,
                next_state,
                SignalDirection.SHORT,
                SignalReason.SHORT_BREAKOUT,
                fingerprint,
                trigger_price=candle.close,
            ),
        )
    return Cand001Transition(
        state=next_state,
        signal=_signal(candle, next_state, SignalDirection.NONE, SignalReason.NO_BREAKOUT, fingerprint),
    )


def _clock(value: str) -> time:
    hour, minute = value.split(":", 1)
    return time(int(hour), int(minute))


def _with_last_close(state: Cand001SignalState, close_time: datetime) -> Cand001SignalState:
    return Cand001SignalState(
        session_date=state.session_date,
        or_high=state.or_high,
        or_low=state.or_low,
        or_slots=state.or_slots,
        last_close_time=close_time,
    )


def _signal(
    candle: Candle,
    state: Cand001SignalState,
    direction: SignalDirection,
    reason: SignalReason,
    fingerprint: str,
    *,
    trigger_price: float | None = None,
) -> Cand001Signal:
    return Cand001Signal(
        event_time=candle.event_time,
        close_time=candle.close_time,
        direction=direction,
        reason=reason,
        or_high=state.or_high,
        or_low=state.or_low,
        trigger_price=trigger_price,
        data_fingerprint=fingerprint,
    )
