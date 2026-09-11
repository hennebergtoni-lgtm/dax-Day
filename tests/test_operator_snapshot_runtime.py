from dataclasses import replace
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

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
from daxlab.runtime.operator_snapshot import SCHEMA_VERSION, build_operator_snapshot
from daxlab.runtime.paper_contracts import ExecutionIntent, Side


BERLIN = ZoneInfo("Europe/Berlin")


def _trade_stack():
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
    config = Cand001Config()
    plan = build_cand001_trade_plan(signal, config=config)
    assert plan is not None
    admission = admit_cand001_trade(
        Cand001AdmissionState(), signal, plan, config=config
    )
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
    next_bar = Candle(
        symbol="DE40",
        timeframe="M5",
        event_time=decision.event_time,
        close_time=decision.event_time + timedelta(minutes=5),
        open=104.0,
        high=114.0,
        low=103.0,
        close=112.0,
        volume=None,
        source="TEST",
        received_at=decision.event_time + timedelta(minutes=5, seconds=1),
        is_closed=True,
    )
    lifecycle = advance_cand001_virtual_lifecycle(lifecycle, next_bar)
    assert lifecycle.status is VirtualPositionStatus.CLOSED
    outcome = build_cand001_virtual_outcome(decision=decision, lifecycle=lifecycle)
    return config, signal, plan, admission, decision, lifecycle, outcome, next_bar


def test_closed_virtual_trade_is_visible_in_operator_snapshot() -> None:
    config, signal, plan, admission, decision, lifecycle, outcome, next_bar = _trade_stack()

    snapshot = build_operator_snapshot(
        generated_at=next_bar.close_time,
        config=config,
        signal=signal,
        proposed_trade_plan=plan,
        admission=admission,
        decision=decision,
        lifecycle=lifecycle,
        outcome=outcome,
    )
    payload = snapshot.as_dict()

    assert SCHEMA_VERSION == "DAX_BOT_OPERATOR_SNAPSHOT_V2"
    assert payload["virtual_position"]["status"] == "CLOSED"
    assert payload["virtual_position"]["side"] == "BUY"
    assert payload["virtual_position"]["filled_price"] == 104.0
    assert payload["virtual_position"]["exit_price"] == 113.0
    assert payload["virtual_position"]["exit_reason"] == "target"
    assert payload["outcome"]["outcome_id"] == outcome.outcome_id
    assert payload["outcome"]["gross_r"] == pytest.approx(1.5)
    assert payload["outcome"]["cost_r"] == pytest.approx(0.4 / 6.0)
    assert payload["outcome"]["net_r"] == pytest.approx(1.5 - 0.4 / 6.0)
    assert payload["safety"] == {
        "execution_capability": "NONE",
        "order_execution_enabled": False,
    }


def test_snapshot_without_lifecycle_remains_valid_decision_view() -> None:
    config, signal, plan, admission, decision, _, _, next_bar = _trade_stack()

    snapshot = build_operator_snapshot(
        generated_at=next_bar.close_time,
        config=config,
        signal=signal,
        proposed_trade_plan=plan,
        admission=admission,
        decision=decision,
    )

    assert snapshot.as_dict()["virtual_position"]["status"] is None
    assert snapshot.as_dict()["outcome"]["net_r"] is None


def test_outcome_lifecycle_identity_drift_fails_closed() -> None:
    config, signal, plan, admission, decision, lifecycle, outcome, next_bar = _trade_stack()
    wrong = replace(outcome, lifecycle_id="f" * 64)

    with pytest.raises(ValueError, match="lifecycle identity drift"):
        build_operator_snapshot(
            generated_at=next_bar.close_time,
            config=config,
            signal=signal,
            proposed_trade_plan=plan,
            admission=admission,
            decision=decision,
            lifecycle=lifecycle,
            outcome=wrong,
        )


def test_snapshot_cannot_observe_future_lifecycle_close() -> None:
    config, signal, plan, admission, decision, lifecycle, outcome, _ = _trade_stack()

    with pytest.raises(ValueError, match="future virtual close"):
        build_operator_snapshot(
            generated_at=decision.event_time,
            config=config,
            signal=signal,
            proposed_trade_plan=plan,
            admission=admission,
            decision=decision,
            lifecycle=lifecycle,
            outcome=outcome,
        )
