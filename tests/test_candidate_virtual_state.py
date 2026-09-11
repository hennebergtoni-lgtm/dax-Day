from copy import deepcopy
from datetime import datetime, timedelta, timezone

import pytest

from daxlab.runtime.atomic_json import atomic_write_json, read_json_object
from daxlab.runtime.candidate_state import (
    candidate_virtual_lifecycle_payload,
    parse_candidate_virtual_lifecycle_payload,
)
from daxlab.runtime.candidate_virtual_lifecycle import (
    VirtualPositionStatus,
    advance_cand001_virtual_lifecycle,
    start_cand001_virtual_lifecycle,
)
from daxlab.runtime.candidate_virtual_outcome import build_cand001_virtual_outcome
from daxlab.runtime.contracts import Candle
from daxlab.runtime.decision import DecisionRecord, FinalAction
from daxlab.runtime.paper_contracts import ExecutionIntent, Side


UTC = timezone.utc
DECISION_TIME = datetime(2026, 9, 11, 9, 20, tzinfo=UTC)


def _decision() -> DecisionRecord:
    return DecisionRecord.build(
        event_time=DECISION_TIME,
        data_fingerprint="a" * 64,
        regime="ALL_SESSIONS",
        structure="CONFIRMED_BREAKOUT_CLOSE/OR15",
        setup="LONG_BREAKOUT",
        filter_results={"entry_confirmed": True},
        blockers=(),
        risk_result="ADMITTED",
        config={"candidate_id": "CAND-001"},
        core_version="DAX-BOT/1.0-alpha/CAND-001",
        final_action=FinalAction.TRADE,
    )


def _intent(decision: DecisionRecord) -> ExecutionIntent:
    return ExecutionIntent.build(
        decision_id=decision.decision_id,
        run_manifest_fingerprint="b" * 64,
        created_at=decision.event_time,
        symbol="DE40",
        side=Side.BUY,
        quantity=1.0,
        requested_price=100.0,
        stop_price=90.0,
        target_price=110.0,
    )


def _bar(
    event_time: datetime,
    *,
    open_: float = 100.0,
    high: float = 105.0,
    low: float = 95.0,
    close: float = 102.0,
) -> Candle:
    return Candle(
        symbol="DE40",
        timeframe="M5",
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
    )


def _opened_state():
    decision = _decision()
    pending = start_cand001_virtual_lifecycle(_intent(decision))
    first = _bar(DECISION_TIME)
    opened = advance_cand001_virtual_lifecycle(pending, first)
    assert opened.status is VirtualPositionStatus.OPEN
    return decision, first, opened


def test_open_virtual_state_atomic_round_trip_and_resume_matches_continuous(tmp_path) -> None:
    _, first, opened = _opened_state()
    target_bar = _bar(
        first.close_time,
        open_=103.0,
        high=111.0,
        low=99.0,
        close=108.0,
    )
    continuous = advance_cand001_virtual_lifecycle(opened, target_bar)

    path = tmp_path / "cand001_virtual_state.json"
    atomic_write_json(path, candidate_virtual_lifecycle_payload(opened))
    restored = parse_candidate_virtual_lifecycle_payload(read_json_object(path))
    resumed = advance_cand001_virtual_lifecycle(restored, target_bar)

    assert restored == opened
    assert resumed == continuous
    assert resumed.status is VirtualPositionStatus.CLOSED
    assert resumed.execution_capability == "NONE"
    assert resumed.order_execution_enabled is False


def test_duplicate_bar_after_restart_is_idempotent() -> None:
    _, first, opened = _opened_state()
    restored = parse_candidate_virtual_lifecycle_payload(
        candidate_virtual_lifecycle_payload(opened)
    )

    assert advance_cand001_virtual_lifecycle(restored, first) == restored


def test_tampered_virtual_state_fails_closed() -> None:
    _, _, opened = _opened_state()
    payload = candidate_virtual_lifecycle_payload(opened)
    tampered = deepcopy(payload)
    tampered["lifecycle"]["filled_price"] = 99999.0

    with pytest.raises(ValueError, match="fingerprint mismatch"):
        parse_candidate_virtual_lifecycle_payload(tampered)


def test_closed_state_round_trip_rebuilds_identical_costed_outcome() -> None:
    decision, first, opened = _opened_state()
    target_bar = _bar(
        first.close_time,
        open_=103.0,
        high=111.0,
        low=99.0,
        close=108.0,
    )
    closed = advance_cand001_virtual_lifecycle(opened, target_bar)
    before = build_cand001_virtual_outcome(decision=decision, lifecycle=closed)

    restored = parse_candidate_virtual_lifecycle_payload(
        candidate_virtual_lifecycle_payload(closed)
    )
    after = build_cand001_virtual_outcome(decision=decision, lifecycle=restored)

    assert restored == closed
    assert after == before
    assert after.outcome_id == before.outcome_id
    assert after.net_r == pytest.approx(before.net_r)


def test_virtual_state_execution_escalation_fails_closed() -> None:
    _, _, opened = _opened_state()
    payload = candidate_virtual_lifecycle_payload(opened)
    tampered = deepcopy(payload)
    tampered["execution_capability"] = "BROKER"

    with pytest.raises(ValueError, match="execution capability"):
        parse_candidate_virtual_lifecycle_payload(tampered)
