from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from daxlab.runtime.candidate_admission import AdmissionStatus
from daxlab.runtime.candidate_pipeline import Cand001PipelineState, process_cand001_candle
from daxlab.runtime.candidate_signal import SignalDirection, SignalReason
from daxlab.runtime.contracts import Candle
from daxlab.runtime.decision import FinalAction


BERLIN = ZoneInfo("Europe/Berlin")


def bar(hour, minute, *, open_price, high_price, low_price, close_price):
    event = datetime(2026, 9, 11, hour, minute, tzinfo=BERLIN)
    return Candle(
        symbol="DE40",
        timeframe="5m",
        event_time=event,
        close_time=event + timedelta(minutes=5),
        open=open_price,
        high=high_price,
        low=low_price,
        close=close_price,
        volume=None,
        source="TEST",
        received_at=event + timedelta(minutes=5, seconds=1),
        is_closed=True,
    )


def step(state, candle):
    return process_cand001_candle(
        state,
        candle,
        observed_at=candle.close_time + timedelta(seconds=1),
    )


def build_or(state=None):
    current = state or Cand001PipelineState()
    for candle in (
        bar(9, 0, open_price=100, high_price=102, low_price=99, close_price=101),
        bar(9, 5, open_price=101, high_price=103, low_price=98, close_price=102),
        bar(9, 10, open_price=102, high_price=102.5, low_price=98.5, close_price=101),
    ):
        current = step(current, candle).state
    return current


def test_full_closed_bar_sequence_produces_one_observable_trade():
    state = build_or()
    breakout = bar(9, 15, open_price=102, high_price=105, low_price=101, close_price=104)

    result = step(state, breakout)

    assert result.signal.direction is SignalDirection.LONG
    assert result.signal.reason is SignalReason.LONG_BREAKOUT
    assert result.proposed_trade_plan is not None
    assert result.proposed_trade_plan.entry_price == 104
    assert result.proposed_trade_plan.stop_price == 98
    assert result.proposed_trade_plan.target_price == 113
    assert result.admission.status is AdmissionStatus.ALLOWED
    assert result.decision.final_action is FinalAction.TRADE
    assert result.state.admission.trades_admitted == 1
    assert result.operator_snapshot.decision_action == "TRADE"
    assert result.operator_snapshot.execution_capability == "NONE"
    assert result.operator_snapshot.order_execution_enabled is False


def test_second_breakout_same_session_remains_visible_but_is_not_admitted():
    state = build_or()
    first = step(
        state,
        bar(9, 15, open_price=102, high_price=105, low_price=101, close_price=104),
    )
    second = step(
        first.state,
        bar(9, 20, open_price=100, high_price=101, low_price=95, close_price=97),
    )

    assert second.signal.direction is SignalDirection.SHORT
    assert second.proposed_trade_plan is not None
    assert second.admission.status is AdmissionStatus.SESSION_LIMIT
    assert second.decision.final_action is FinalAction.NO_TRADE
    assert second.decision.blockers == ("SESSION_TRADE_LIMIT",)
    assert second.operator_snapshot.proposed_entry == 97
    assert second.state.admission.trades_admitted == 1


def test_same_initial_state_and_sequence_replay_identically():
    sequence = (
        bar(9, 0, open_price=100, high_price=102, low_price=99, close_price=101),
        bar(9, 5, open_price=101, high_price=103, low_price=98, close_price=102),
        bar(9, 10, open_price=102, high_price=102.5, low_price=98.5, close_price=101),
        bar(9, 15, open_price=102, high_price=105, low_price=101, close_price=104),
    )

    def run():
        state = Cand001PipelineState()
        results = []
        for candle in sequence:
            result = step(state, candle)
            state = result.state
            results.append(result)
        return tuple(results)

    assert run() == run()


def test_observation_time_cannot_precede_closed_bar():
    candle = bar(9, 0, open_price=100, high_price=102, low_price=99, close_price=101)
    try:
        process_cand001_candle(
            Cand001PipelineState(),
            candle,
            observed_at=candle.event_time,
        )
    except ValueError as exc:
        assert "cannot precede candle close_time" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected fail-closed observation-time validation")
