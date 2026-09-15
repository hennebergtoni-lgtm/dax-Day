from copy import deepcopy
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from daxlab.runtime.atomic_json import atomic_write_json, read_json_object
from daxlab.runtime.candidate_active_trade_state import (
    Cand001ActiveTradeState,
    candidate_active_trade_payload,
    parse_candidate_active_trade_payload,
)
from daxlab.runtime.candidate_admission import Cand001AdmissionState, admit_cand001_trade
from daxlab.runtime.candidate_config import Cand001Config
from daxlab.runtime.candidate_decision import build_cand001_decision
from daxlab.runtime.candidate_signal import Cand001Signal, SignalDirection, SignalReason
from daxlab.runtime.candidate_trade_plan import build_cand001_trade_plan
from daxlab.runtime.candidate_virtual_lifecycle import (
    VirtualPositionStatus,
    advance_cand001_virtual_lifecycle,
    start_cand001_virtual_lifecycle,
)
from daxlab.runtime.candidate_virtual_outcome import build_cand001_virtual_outcome
from daxlab.runtime.contracts import Candle
from daxlab.runtime.decision import stable_fingerprint
from daxlab.runtime.paper_contracts import ExecutionIntent, Side


BERLIN = ZoneInfo("Europe/Berlin")


def _open_trade():
    config = Cand001Config()
    event = datetime(2026, 9, 11, 9, 15, tzinfo=BERLIN)
    signal = Cand001Signal(
        event_time=event,
        close_time=event + timedelta(minutes=5),
        direction=SignalDirection.LONG,
        reason=SignalReason.LONG_BREAKOUT,
        or_high=103.0,
        or_low=98.0,
        trigger_price=104.0,
        data_fingerprint="a" * 64,
    )
    plan = build_cand001_trade_plan(signal, config=config)
    assert plan is not None
    admission = admit_cand001_trade(Cand001AdmissionState(), signal, plan, config=config)
    decision = build_cand001_decision(signal, admission, config=config)
    intent = ExecutionIntent.build(
        decision_id=decision.decision_id,
        run_manifest_fingerprint="b" * 64,
        created_at=decision.event_time,
        symbol="DE40",
        side=Side.BUY,
        quantity=1.0,
        requested_price=plan.entry_price,
        stop_price=plan.stop_price,
        target_price=plan.target_price,
    )
    lifecycle = start_cand001_virtual_lifecycle(intent)
    fill_bar = Candle(
        symbol="DE40",
        timeframe="M5",
        event_time=decision.event_time,
        close_time=decision.event_time + timedelta(minutes=5),
        open=104.0,
        high=108.0,
        low=101.0,
        close=106.0,
        volume=None,
        source="TEST",
        received_at=decision.event_time + timedelta(minutes=5, seconds=1),
        is_closed=True,
    )
    lifecycle = advance_cand001_virtual_lifecycle(lifecycle, fill_bar)
    assert lifecycle.status is VirtualPositionStatus.OPEN
    state = Cand001ActiveTradeState(
        core_version=config.product_identity().core_version,
        origin_decision=decision,
        lifecycle=lifecycle,
    )
    return config, state, fill_bar


def _target_bar(fill_bar: Candle) -> Candle:
    return Candle(
        symbol="DE40",
        timeframe="M5",
        event_time=fill_bar.close_time,
        close_time=fill_bar.close_time + timedelta(minutes=5),
        open=106.0,
        high=114.0,
        low=103.0,
        close=113.0,
        volume=None,
        source="TEST",
        received_at=fill_bar.close_time + timedelta(minutes=5, seconds=1),
        is_closed=True,
    )


def test_active_trade_restart_produces_identical_later_outcome(tmp_path) -> None:
    _, state, fill_bar = _open_trade()
    later_bar = _target_bar(fill_bar)

    uninterrupted_lifecycle = advance_cand001_virtual_lifecycle(state.lifecycle, later_bar)
    uninterrupted = build_cand001_virtual_outcome(
        decision=state.origin_decision,
        lifecycle=uninterrupted_lifecycle,
    )

    path = tmp_path / "active_trade.json"
    atomic_write_json(path, candidate_active_trade_payload(state))
    restored = parse_candidate_active_trade_payload(read_json_object(path))
    restored_lifecycle = advance_cand001_virtual_lifecycle(restored.lifecycle, later_bar)
    resumed = build_cand001_virtual_outcome(
        decision=restored.origin_decision,
        lifecycle=restored_lifecycle,
    )

    assert restored.origin_decision == state.origin_decision
    assert restored.lifecycle == state.lifecycle
    assert restored_lifecycle == uninterrupted_lifecycle
    assert resumed.outcome_id == uninterrupted.outcome_id
    assert resumed.net_r == pytest.approx(uninterrupted.net_r)
    assert resumed.execution_capability == "NONE"
    assert resumed.order_execution_enabled is False


def test_active_trade_payload_rejects_rehashed_decision_identity_tamper() -> None:
    _, state, _ = _open_trade()
    payload = deepcopy(candidate_active_trade_payload(state))
    payload["origin_decision"]["decision_id"] = "f" * 64
    payload.pop("payload_fingerprint")
    payload["payload_fingerprint"] = stable_fingerprint(payload)

    with pytest.raises(ValueError, match="deterministic identity drift"):
        parse_candidate_active_trade_payload(payload)


def test_active_trade_payload_rejects_execution_safety_escalation() -> None:
    _, state, _ = _open_trade()
    payload = deepcopy(candidate_active_trade_payload(state))
    payload["execution_capability"] = "BROKER"
    payload.pop("payload_fingerprint")
    payload["payload_fingerprint"] = stable_fingerprint(payload)

    with pytest.raises(ValueError, match="execution capability"):
        parse_candidate_active_trade_payload(payload)
