from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from daxlab.runtime.candidate_virtual_lifecycle import (
    VirtualPositionStatus,
    advance_cand001_virtual_lifecycle,
    start_cand001_virtual_lifecycle,
)
from daxlab.runtime.contracts import Candle
from daxlab.runtime.paper_contracts import ExecutionIntent, Side


BERLIN = ZoneInfo("Europe/Berlin")


def _intent() -> ExecutionIntent:
    created = datetime(2026, 9, 11, 9, 20, tzinfo=BERLIN)
    return ExecutionIntent.build(
        decision_id="a" * 64,
        run_manifest_fingerprint="b" * 64,
        created_at=created,
        symbol="DE40",
        side=Side.BUY,
        quantity=1.0,
        requested_price=104.0,
        stop_price=98.0,
        target_price=113.0,
    )


def _candle(timeframe: str) -> Candle:
    event = datetime(2026, 9, 11, 9, 20, tzinfo=BERLIN)
    return Candle(
        symbol="DE40",
        timeframe=timeframe,
        event_time=event,
        close_time=event + timedelta(minutes=5),
        open=104.0,
        high=108.0,
        low=101.0,
        close=106.0,
        volume=None,
        source="TEST",
        received_at=event + timedelta(minutes=5, seconds=1),
        is_closed=True,
    )


def test_canonical_candidate_5m_candle_advances_lifecycle() -> None:
    state = start_cand001_virtual_lifecycle(_intent())

    advanced = advance_cand001_virtual_lifecycle(state, _candle("5m"))

    assert advanced.status is VirtualPositionStatus.OPEN
    assert advanced.filled_price == 104.0


def test_non_five_minute_label_fails_closed() -> None:
    state = start_cand001_virtual_lifecycle(_intent())

    with pytest.raises(ValueError, match="five-minute"):
        advance_cand001_virtual_lifecycle(state, _candle("15m"))
