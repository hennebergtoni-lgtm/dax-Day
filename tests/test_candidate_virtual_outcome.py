from datetime import datetime, timedelta, timezone

import pytest

from daxlab.core.execution import ExitReason
from daxlab.runtime.candidate_virtual_lifecycle import (
    advance_cand001_virtual_lifecycle,
    start_cand001_virtual_lifecycle,
)
from daxlab.runtime.candidate_virtual_outcome import build_cand001_virtual_outcome
from daxlab.runtime.contracts import Candle
from daxlab.runtime.decision import DecisionRecord, FinalAction
from daxlab.runtime.paper_contracts import ExecutionIntent, PaperFillModelConfig, Side

UTC = timezone.utc
DECISION_TIME = datetime(2026, 9, 11, 9, 20, tzinfo=UTC)


def _decision() -> DecisionRecord:
    return DecisionRecord.build(
        event_time=DECISION_TIME,
        data_fingerprint="a" * 64,
        regime="ALL",
        structure="CONFIRMED_BREAKOUT_CLOSE/OR15",
        setup="LONG_BREAKOUT",
        filter_results={"entry_confirmed": True},
        blockers=(),
        risk_result="ADMITTED",
        config={"candidate_id": "CAND-001"},
        core_version="1.0-alpha",
        final_action=FinalAction.TRADE,
    )


def _intent(decision: DecisionRecord, side: Side = Side.BUY) -> ExecutionIntent:
    if side is Side.BUY:
        requested, stop, target = 100.0, 90.0, 115.0
    else:
        requested, stop, target = 100.0, 110.0, 85.0
    return ExecutionIntent.build(
        decision_id=decision.decision_id,
        run_manifest_fingerprint="2" * 64,
        created_at=decision.event_time,
        symbol="DE40",
        side=side,
        quantity=1.0,
        requested_price=requested,
        stop_price=stop,
        target_price=target,
    )


def _bar(
    *,
    open_: float,
    high: float,
    low: float,
    close: float,
    event_time: datetime = DECISION_TIME,
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


def _closed_lifecycle(
    *,
    side: Side = Side.BUY,
    open_: float = 100.0,
    high: float = 116.0,
    low: float = 95.0,
    close: float = 114.0,
    fill_model: PaperFillModelConfig | None = None,
):
    decision = _decision()
    intent = _intent(decision, side)
    lifecycle = start_cand001_virtual_lifecycle(intent, fill_model=fill_model)
    lifecycle = advance_cand001_virtual_lifecycle(
        lifecycle,
        _bar(open_=open_, high=high, low=low, close=close),
        fill_model=fill_model,
    )
    return decision, lifecycle


def test_long_target_is_costed_and_reuses_dated_shadow_outcome() -> None:
    decision, lifecycle = _closed_lifecycle()

    result = build_cand001_virtual_outcome(decision=decision, lifecycle=lifecycle)

    assert lifecycle.exit_reason is ExitReason.TARGET
    assert result.planned_risk_points == 10.0
    assert result.gross_points == 15.0
    assert result.configured_cost_points == pytest.approx(0.40)
    assert result.gross_r == pytest.approx(1.5)
    assert result.cost_r == pytest.approx(0.04)
    assert result.net_r == pytest.approx(1.46)
    assert result.dated_outcome.r_result == pytest.approx(1.46)
    assert result.dated_outcome.decision_id == decision.decision_id
    assert result.execution_capability == "NONE"
    assert result.order_execution_enabled is False
    assert len(result.outcome_id) == 64


def test_adverse_next_bar_fill_reduces_achieved_r_without_redefining_risk_unit() -> None:
    decision, lifecycle = _closed_lifecycle(
        open_=102.0,
        high=116.0,
        low=99.0,
        close=114.0,
    )

    result = build_cand001_virtual_outcome(decision=decision, lifecycle=lifecycle)

    assert lifecycle.filled_price == 102.0
    assert result.planned_risk_points == 10.0
    assert result.gross_points == 13.0
    assert result.gross_r == pytest.approx(1.3)
    assert result.net_r == pytest.approx(1.26)


def test_stop_loss_is_worse_than_minus_one_r_after_costs() -> None:
    decision, lifecycle = _closed_lifecycle(
        open_=100.0,
        high=104.0,
        low=89.0,
        close=92.0,
    )

    result = build_cand001_virtual_outcome(decision=decision, lifecycle=lifecycle)

    assert lifecycle.exit_reason is ExitReason.STOP
    assert result.gross_r == pytest.approx(-1.0)
    assert result.cost_r == pytest.approx(0.04)
    assert result.net_r == pytest.approx(-1.04)


def test_short_target_is_symmetric() -> None:
    decision, lifecycle = _closed_lifecycle(
        side=Side.SELL,
        open_=100.0,
        high=104.0,
        low=84.0,
        close=87.0,
    )

    result = build_cand001_virtual_outcome(decision=decision, lifecycle=lifecycle)

    assert lifecycle.exit_reason is ExitReason.TARGET
    assert result.gross_points == 15.0
    assert result.net_r == pytest.approx(1.46)


def test_configured_costs_are_bound_to_outcome_and_change_net_r() -> None:
    model = PaperFillModelConfig(
        spread_points=0.40,
        slippage_points=0.20,
        commission_points=0.20,
    )
    decision, lifecycle = _closed_lifecycle(fill_model=model)

    result = build_cand001_virtual_outcome(
        decision=decision,
        lifecycle=lifecycle,
        fill_model=model,
    )

    assert result.configured_cost_points == pytest.approx(0.80)
    assert result.cost_r == pytest.approx(0.08)
    assert result.net_r == pytest.approx(1.42)


def test_open_lifecycle_cannot_emit_an_outcome() -> None:
    decision = _decision()
    lifecycle = start_cand001_virtual_lifecycle(_intent(decision))
    lifecycle = advance_cand001_virtual_lifecycle(
        lifecycle,
        _bar(open_=100.0, high=105.0, low=95.0, close=102.0),
    )

    with pytest.raises(ValueError, match="CLOSED lifecycle"):
        build_cand001_virtual_outcome(decision=decision, lifecycle=lifecycle)


def test_decision_identity_mismatch_fails_closed() -> None:
    decision, lifecycle = _closed_lifecycle()
    other = DecisionRecord.build(
        event_time=DECISION_TIME,
        data_fingerprint="b" * 64,
        regime="ALL",
        structure="CONFIRMED_BREAKOUT_CLOSE/OR15",
        setup="LONG_BREAKOUT",
        filter_results={"entry_confirmed": True},
        blockers=(),
        risk_result="ADMITTED",
        config={"candidate_id": "CAND-001"},
        core_version="1.0-alpha",
        final_action=FinalAction.TRADE,
    )

    with pytest.raises(ValueError, match="decision_id"):
        build_cand001_virtual_outcome(decision=other, lifecycle=lifecycle)


def test_fill_model_drift_fails_closed() -> None:
    decision, lifecycle = _closed_lifecycle()
    changed_model = PaperFillModelConfig(spread_points=0.30)

    with pytest.raises(ValueError, match="fingerprint drift"):
        build_cand001_virtual_outcome(
            decision=decision,
            lifecycle=lifecycle,
            fill_model=changed_model,
        )


def test_non_trade_decision_cannot_emit_virtual_outcome() -> None:
    decision, lifecycle = _closed_lifecycle()
    blocked = DecisionRecord.build(
        event_time=decision.event_time,
        data_fingerprint=decision.data_fingerprint,
        regime=decision.regime,
        structure=decision.structure,
        setup=decision.setup,
        filter_results={"entry_confirmed": False},
        blockers=("TEST_BLOCK",),
        risk_result="BLOCKED",
        config={"candidate_id": "CAND-001"},
        core_version="1.0-alpha",
        final_action=FinalAction.NO_TRADE,
    )

    with pytest.raises(ValueError, match="TRADE decision"):
        build_cand001_virtual_outcome(decision=blocked, lifecycle=lifecycle)
