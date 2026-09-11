from datetime import datetime, timedelta, timezone

import pytest

from daxlab.core.execution import ExitReason
from daxlab.runtime.candidate_virtual_lifecycle import (
    VirtualPositionStatus,
    advance_cand001_virtual_lifecycle,
    start_cand001_virtual_lifecycle,
)
from daxlab.runtime.contracts import Candle, DataQualityState
from daxlab.runtime.paper_contracts import (
    ExecutionIntent,
    PaperFillModelConfig,
    PartialFillPolicy,
    Side,
)

UTC = timezone.utc
DECISION_TIME = datetime(2026, 9, 11, 9, 20, tzinfo=UTC)


def _intent(side: Side = Side.BUY) -> ExecutionIntent:
    if side is Side.BUY:
        requested, stop, target = 100.0, 90.0, 110.0
    else:
        requested, stop, target = 100.0, 110.0, 90.0
    return ExecutionIntent.build(
        decision_id="1" * 64,
        run_manifest_fingerprint="2" * 64,
        created_at=DECISION_TIME,
        symbol="DE40",
        side=side,
        quantity=1.0,
        requested_price=requested,
        stop_price=stop,
        target_price=target,
    )


def _bar(
    *,
    event_time: datetime,
    open_: float = 100.0,
    high: float = 105.0,
    low: float = 95.0,
    close: float = 102.0,
    symbol: str = "DE40",
    timeframe: str = "5m",
    quality: DataQualityState = DataQualityState.OK,
) -> Candle:
    return Candle(
        symbol=symbol,
        timeframe=timeframe,
        event_time=event_time,
        close_time=event_time + timedelta(minutes=5),
        open=open_,
        high=high,
        low=low,
        close=close,
        volume=None,
        source="TEST",
        received_at=event_time + timedelta(minutes=5, seconds=1),
        is_closed=True,
        quality_state=quality,
    )


def test_start_is_deterministic_and_execution_stays_disabled() -> None:
    left = start_cand001_virtual_lifecycle(_intent())
    right = start_cand001_virtual_lifecycle(_intent())

    assert left == right
    assert len(left.lifecycle_id) == 64
    assert left.status is VirtualPositionStatus.PENDING_ENTRY
    assert left.execution_capability == "NONE"
    assert left.order_execution_enabled is False


def test_decision_bar_cannot_create_same_bar_trade_effect() -> None:
    state = start_cand001_virtual_lifecycle(_intent())
    decision_bar = _bar(event_time=DECISION_TIME - timedelta(minutes=5))

    assert advance_cand001_virtual_lifecycle(state, decision_bar) == state


def test_first_next_safe_m5_bar_fills_at_first_available_open() -> None:
    state = start_cand001_virtual_lifecycle(_intent())
    next_bar = _bar(event_time=DECISION_TIME, open_=101.0, high=106.0, low=96.0)

    observed = advance_cand001_virtual_lifecycle(state, next_bar)

    assert observed.status is VirtualPositionStatus.OPEN
    assert observed.filled_at == next_bar.event_time
    assert observed.filled_price == 101.0
    assert observed.last_close_time == next_bar.close_time
    assert observed.exit_reason is ExitReason.NONE


def test_open_long_position_closes_at_target_on_later_bar() -> None:
    state = start_cand001_virtual_lifecycle(_intent())
    first = _bar(event_time=DECISION_TIME)
    opened = advance_cand001_virtual_lifecycle(state, first)
    target_bar = _bar(
        event_time=first.close_time,
        open_=103.0,
        high=111.0,
        low=99.0,
        close=108.0,
    )

    closed = advance_cand001_virtual_lifecycle(opened, target_bar)

    assert closed.status is VirtualPositionStatus.CLOSED
    assert closed.exit_reason is ExitReason.TARGET
    assert closed.exit_price == 110.0
    assert closed.closed_at == target_bar.close_time


def test_ambiguous_fill_bar_reuses_conservative_stop_first_resolver() -> None:
    state = start_cand001_virtual_lifecycle(_intent())
    ambiguous = _bar(
        event_time=DECISION_TIME,
        open_=100.0,
        high=112.0,
        low=88.0,
        close=105.0,
    )

    closed = advance_cand001_virtual_lifecycle(state, ambiguous)

    assert closed.status is VirtualPositionStatus.CLOSED
    assert closed.exit_reason is ExitReason.STOP
    assert closed.exit_price == 90.0


def test_gap_through_stop_uses_first_available_open() -> None:
    state = start_cand001_virtual_lifecycle(_intent())
    gap_bar = _bar(
        event_time=DECISION_TIME,
        open_=85.0,
        high=88.0,
        low=80.0,
        close=86.0,
    )

    closed = advance_cand001_virtual_lifecycle(state, gap_bar)

    assert closed.status is VirtualPositionStatus.CLOSED
    assert closed.filled_price == 85.0
    assert closed.exit_reason is ExitReason.STOP
    assert closed.exit_price == 85.0
    assert closed.closed_at == gap_bar.event_time


def test_short_side_is_symmetric() -> None:
    state = start_cand001_virtual_lifecycle(_intent(Side.SELL))
    target_bar = _bar(
        event_time=DECISION_TIME,
        open_=100.0,
        high=104.0,
        low=89.0,
        close=92.0,
    )

    closed = advance_cand001_virtual_lifecycle(state, target_bar)

    assert closed.status is VirtualPositionStatus.CLOSED
    assert closed.exit_reason is ExitReason.TARGET
    assert closed.exit_price == 90.0


def test_duplicate_bar_is_idempotent_and_out_of_order_bar_fails_closed() -> None:
    state = start_cand001_virtual_lifecycle(_intent())
    first = _bar(event_time=DECISION_TIME)
    opened = advance_cand001_virtual_lifecycle(state, first)

    assert advance_cand001_virtual_lifecycle(opened, first) == opened

    older = _bar(event_time=DECISION_TIME - timedelta(minutes=1))
    with pytest.raises(ValueError, match="out of order"):
        advance_cand001_virtual_lifecycle(opened, older)


def test_unsafe_bar_does_not_fabricate_a_fill() -> None:
    state = start_cand001_virtual_lifecycle(_intent())
    unsafe = _bar(
        event_time=DECISION_TIME,
        open_=99.0,
        quality=DataQualityState.GAP,
    )

    assert advance_cand001_virtual_lifecycle(state, unsafe) == state

    safe = _bar(event_time=DECISION_TIME + timedelta(minutes=5), open_=102.0)
    opened = advance_cand001_virtual_lifecycle(state, safe)
    assert opened.filled_price == 102.0


def test_wrong_market_identity_and_unsupported_partial_fills_fail_closed() -> None:
    state = start_cand001_virtual_lifecycle(_intent())

    with pytest.raises(ValueError, match="symbol"):
        advance_cand001_virtual_lifecycle(
            state,
            _bar(event_time=DECISION_TIME, symbol="OTHER"),
        )
    with pytest.raises(ValueError, match="five-minute"):
        advance_cand001_virtual_lifecycle(
            state,
            _bar(event_time=DECISION_TIME, timeframe="M1"),
        )

    unsupported = PaperFillModelConfig(partial_fill_policy=PartialFillPolicy.PRO_RATA)
    with pytest.raises(ValueError, match="partial fills"):
        start_cand001_virtual_lifecycle(_intent(), fill_model=unsupported)
