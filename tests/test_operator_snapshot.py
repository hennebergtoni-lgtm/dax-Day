from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from daxlab.runtime.candidate_admission import Cand001AdmissionState, admit_cand001_trade
from daxlab.runtime.candidate_config import Cand001Config
from daxlab.runtime.candidate_decision import build_cand001_decision
from daxlab.runtime.candidate_signal import Cand001Signal, SignalDirection, SignalReason
from daxlab.runtime.candidate_trade_plan import build_cand001_trade_plan
from daxlab.runtime.operator_snapshot import build_operator_snapshot


BERLIN = ZoneInfo("Europe/Berlin")


def signal(direction: SignalDirection) -> Cand001Signal:
    event = datetime(2026, 9, 11, 9, 15, tzinfo=BERLIN)
    if direction is SignalDirection.LONG:
        trigger = 104.0
        reason = SignalReason.LONG_BREAKOUT
    elif direction is SignalDirection.SHORT:
        trigger = 97.0
        reason = SignalReason.SHORT_BREAKOUT
    else:
        trigger = None
        reason = SignalReason.NO_BREAKOUT
    return Cand001Signal(
        event_time=event,
        close_time=event + timedelta(minutes=5),
        direction=direction,
        reason=reason,
        or_high=103.0,
        or_low=98.0,
        trigger_price=trigger,
        data_fingerprint="a" * 64,
    )


def build_snapshot(direction: SignalDirection, *, prior_trades: int = 0):
    cfg = Cand001Config()
    value = signal(direction)
    plan = build_cand001_trade_plan(value)
    admission = admit_cand001_trade(
        Cand001AdmissionState(
            session_date="2026-09-11" if prior_trades else None,
            trades_admitted=prior_trades,
        ),
        value,
        plan,
        config=cfg,
    )
    decision = build_cand001_decision(value, admission, config=cfg)
    return build_operator_snapshot(
        generated_at=datetime(2026, 9, 11, 7, 20, tzinfo=timezone.utc),
        config=cfg,
        signal=value,
        proposed_trade_plan=plan,
        admission=admission,
        decision=decision,
    )


def test_trade_snapshot_exposes_version_signal_geometry_and_safety():
    snapshot = build_snapshot(SignalDirection.LONG)
    payload = snapshot.as_dict()

    assert snapshot.core_version == "DAX-BOT/1.0-alpha/CAND-001"
    assert payload["signal"] == {"direction": "LONG", "reason": "LONG_BREAKOUT"}
    assert payload["admission"] == {"status": "ALLOWED"}
    assert payload["decision"]["action"] == "TRADE"
    assert payload["trade_plan"] == {
        "entry": 104.0,
        "stop": 98.0,
        "target": 113.0,
        "reward_risk": 1.5,
    }
    assert payload["safety"] == {
        "execution_capability": "NONE",
        "order_execution_enabled": False,
    }
    assert len(snapshot.snapshot_fingerprint) == 64


def test_session_limit_keeps_signal_and_geometry_visible_but_blocks_trade():
    snapshot = build_snapshot(SignalDirection.SHORT, prior_trades=1)
    payload = snapshot.as_dict()

    assert payload["signal"]["direction"] == "SHORT"
    assert payload["admission"]["status"] == "SESSION_LIMIT"
    assert payload["decision"]["action"] == "NO_TRADE"
    assert payload["decision"]["blockers"] == ["SESSION_TRADE_LIMIT"]
    assert payload["trade_plan"]["entry"] == 97.0


def test_no_signal_snapshot_has_no_trade_geometry():
    snapshot = build_snapshot(SignalDirection.NONE)
    payload = snapshot.as_dict()

    assert payload["decision"]["action"] == "NO_TRADE"
    assert payload["trade_plan"] == {
        "entry": None,
        "stop": None,
        "target": None,
        "reward_risk": None,
    }


def test_snapshot_requires_timezone_aware_generation_time():
    cfg = Cand001Config()
    value = signal(SignalDirection.NONE)
    admission = admit_cand001_trade(Cand001AdmissionState(), value, None, config=cfg)
    decision = build_cand001_decision(value, admission, config=cfg)

    with pytest.raises(ValueError, match="timezone-aware"):
        build_operator_snapshot(
            generated_at=datetime(2026, 9, 11, 7, 20),
            config=cfg,
            signal=value,
            proposed_trade_plan=None,
            admission=admission,
            decision=decision,
        )
