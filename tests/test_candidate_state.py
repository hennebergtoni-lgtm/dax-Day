from copy import deepcopy
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from daxlab.runtime.atomic_json import atomic_write_json, read_json_object
from daxlab.runtime.candidate_pipeline import Cand001PipelineState, process_cand001_candle
from daxlab.runtime.candidate_state import candidate_state_payload, parse_candidate_state_payload
from daxlab.runtime.contracts import Candle


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


def opening_range_state():
    state = Cand001PipelineState()
    for candle in (
        bar(9, 0, open_price=100, high_price=102, low_price=99, close_price=101),
        bar(9, 5, open_price=101, high_price=103, low_price=98, close_price=102),
        bar(9, 10, open_price=102, high_price=102.5, low_price=98.5, close_price=101),
    ):
        state = step(state, candle).state
    return state


def test_state_payload_round_trip_and_atomic_json(tmp_path):
    state = opening_range_state()
    payload = candidate_state_payload(state)
    path = tmp_path / "cand001_state.json"

    atomic_write_json(path, payload)
    restored = parse_candidate_state_payload(read_json_object(path))

    assert restored == state
    assert payload["execution_capability"] == "NONE"
    assert payload["order_execution_enabled"] is False
    assert len(payload["payload_fingerprint"]) == 64


def test_tampered_state_fails_closed():
    payload = candidate_state_payload(opening_range_state())
    tampered = deepcopy(payload)
    tampered["state"]["signal"]["or_high"] = 99999

    with pytest.raises(ValueError, match="fingerprint mismatch"):
        parse_candidate_state_payload(tampered)


def test_execution_capability_escalation_fails_closed():
    payload = candidate_state_payload(opening_range_state())
    tampered = deepcopy(payload)
    tampered["execution_capability"] = "BROKER"

    with pytest.raises(ValueError, match="execution capability"):
        parse_candidate_state_payload(tampered)


def test_restart_after_or15_matches_continuous_processing():
    state = opening_range_state()
    breakout = bar(9, 15, open_price=102, high_price=105, low_price=101, close_price=104)

    continuous = step(state, breakout)
    restored_state = parse_candidate_state_payload(candidate_state_payload(state))
    resumed = step(restored_state, breakout)

    assert resumed == continuous


def test_restart_after_admitted_trade_keeps_session_limit():
    state = opening_range_state()
    first = step(
        state,
        bar(9, 15, open_price=102, high_price=105, low_price=101, close_price=104),
    )
    restored = parse_candidate_state_payload(candidate_state_payload(first.state))
    second = step(
        restored,
        bar(9, 20, open_price=100, high_price=101, low_price=95, close_price=97),
    )

    assert second.decision.final_action.value == "NO_TRADE"
    assert second.decision.blockers == ("SESSION_TRADE_LIMIT",)
    assert second.state.admission.trades_admitted == 1
