from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from daxlab.research.forward_shadow_performance import (
    ALLOWED,
    BLOCKED,
    build_forward_shadow_performance_report,
)
from daxlab.runtime.candidate_admission import Cand001AdmissionState, admit_cand001_trade
from daxlab.runtime.candidate_config import Cand001Config
from daxlab.runtime.candidate_decision import build_cand001_decision
from daxlab.runtime.candidate_execution_intent import build_cand001_execution_intent
from daxlab.runtime.candidate_forward_observation import build_cand001_forward_observation
from daxlab.runtime.candidate_signal import Cand001Signal, SignalDirection, SignalReason
from daxlab.runtime.candidate_sizing import Cand001SimulationSizingPolicy
from daxlab.runtime.candidate_trade_plan import build_cand001_trade_plan
from daxlab.runtime.candidate_virtual_lifecycle import (
    advance_cand001_virtual_lifecycle,
    start_cand001_virtual_lifecycle,
)
from daxlab.runtime.candidate_virtual_outcome import build_cand001_virtual_outcome
from daxlab.runtime.contracts import Candle, RuntimeMode
from daxlab.runtime.manifests import RunManifest

BERLIN = ZoneInfo("Europe/Berlin")
EVENT = datetime(2026, 9, 11, 9, 15, tzinfo=BERLIN)


def _signal(
    *,
    direction: SignalDirection,
    reason: SignalReason,
    fingerprint: str,
    event_time: datetime = EVENT,
) -> Cand001Signal:
    return Cand001Signal(
        event_time=event_time,
        close_time=event_time + timedelta(minutes=5),
        direction=direction,
        reason=reason,
        or_high=103.0,
        or_low=98.0,
        trigger_price=(
            104.0
            if direction is SignalDirection.LONG
            else 97.0 if direction is SignalDirection.SHORT else None
        ),
        data_fingerprint=fingerprint,
    )


def _manifest(config: Cand001Config, sizing: Cand001SimulationSizingPolicy) -> RunManifest:
    return RunManifest.build(
        dataset_fingerprint="d" * 64,
        engine_fingerprint="e" * 64,
        config={"candidate": config, "sizing": sizing},
        mode=RuntimeMode.SHADOW,
    )


def _next_bar(event_time: datetime) -> Candle:
    return Candle(
        symbol="DE40",
        timeframe="M5",
        event_time=event_time,
        close_time=event_time + timedelta(minutes=5),
        open=104.0,
        high=114.0,
        low=102.0,
        close=112.0,
        volume=None,
        source="TEST",
        received_at=event_time + timedelta(minutes=5, seconds=1),
        is_closed=True,
    )


def _allowed_terminal_observation():
    config = Cand001Config()
    sizing = Cand001SimulationSizingPolicy()
    signal = _signal(
        direction=SignalDirection.LONG,
        reason=SignalReason.LONG_BREAKOUT,
        fingerprint="a" * 64,
    )
    plan = build_cand001_trade_plan(signal, config=config)
    assert plan is not None
    admission = admit_cand001_trade(Cand001AdmissionState(), signal, plan, config=config)
    decision = build_cand001_decision(signal, admission, config=config)
    intent = build_cand001_execution_intent(
        decision=decision,
        trade_plan=plan,
        run_manifest=_manifest(config, sizing),
        config=config,
        sizing=sizing,
    )
    lifecycle = start_cand001_virtual_lifecycle(intent)
    lifecycle = advance_cand001_virtual_lifecycle(lifecycle, _next_bar(signal.close_time))
    outcome = build_cand001_virtual_outcome(decision=decision, lifecycle=lifecycle)
    observation = build_cand001_forward_observation(
        signal=signal,
        admission=admission,
        decision=decision,
        outcome=outcome,
    )
    return admission, observation, outcome


def test_allowed_terminal_signal_maps_to_existing_forward_contract() -> None:
    _, observation, outcome = _allowed_terminal_observation()

    assert observation is not None
    assert observation.status == ALLOWED
    assert observation.r_result == pytest.approx(outcome.net_r)
    assert observation.signal_id == outcome.decision_id


def test_second_directional_signal_is_visible_as_session_limit_block() -> None:
    first_admission, _, _ = _allowed_terminal_observation()
    signal = _signal(
        direction=SignalDirection.LONG,
        reason=SignalReason.LONG_BREAKOUT,
        fingerprint="b" * 64,
        event_time=EVENT + timedelta(minutes=10),
    )
    plan = build_cand001_trade_plan(signal)
    assert plan is not None
    admission = admit_cand001_trade(first_admission.state, signal, plan)
    decision = build_cand001_decision(signal, admission)

    observation = build_cand001_forward_observation(
        signal=signal,
        admission=admission,
        decision=decision,
    )

    assert observation is not None
    assert observation.status == BLOCKED
    assert observation.r_result is None
    assert observation.block_reason == "SESSION_TRADE_LIMIT"


def test_non_directional_bar_does_not_inflate_generated_signal_count() -> None:
    signal = _signal(
        direction=SignalDirection.NONE,
        reason=SignalReason.NO_BREAKOUT,
        fingerprint="c" * 64,
    )
    admission = admit_cand001_trade(Cand001AdmissionState(), signal, None)
    decision = build_cand001_decision(signal, admission)

    assert (
        build_cand001_forward_observation(
            signal=signal,
            admission=admission,
            decision=decision,
        )
        is None
    )


def test_allowed_signal_without_closed_outcome_fails_closed() -> None:
    config = Cand001Config()
    signal = _signal(
        direction=SignalDirection.LONG,
        reason=SignalReason.LONG_BREAKOUT,
        fingerprint="d" * 64,
    )
    plan = build_cand001_trade_plan(signal, config=config)
    assert plan is not None
    admission = admit_cand001_trade(Cand001AdmissionState(), signal, plan, config=config)
    decision = build_cand001_decision(signal, admission, config=config)

    with pytest.raises(ValueError, match="closed virtual outcome"):
        build_cand001_forward_observation(
            signal=signal,
            admission=admission,
            decision=decision,
        )


def test_terminal_candidate_observations_feed_existing_cash_performance_report() -> None:
    first_admission, allowed, outcome = _allowed_terminal_observation()
    assert allowed is not None

    blocked_signal = _signal(
        direction=SignalDirection.LONG,
        reason=SignalReason.LONG_BREAKOUT,
        fingerprint="e" * 64,
        event_time=EVENT + timedelta(minutes=10),
    )
    blocked_plan = build_cand001_trade_plan(blocked_signal)
    assert blocked_plan is not None
    blocked_admission = admit_cand001_trade(
        first_admission.state,
        blocked_signal,
        blocked_plan,
    )
    blocked_decision = build_cand001_decision(blocked_signal, blocked_admission)
    blocked = build_cand001_forward_observation(
        signal=blocked_signal,
        admission=blocked_admission,
        decision=blocked_decision,
    )
    assert blocked is not None

    report = build_forward_shadow_performance_report(
        "cand001-window",
        (allowed, blocked),
        starting_balance_eur=1000.0,
        fixed_risk_eur=20.0,
    )

    assert report.generated_signals == 2
    assert report.allowed_shadow_trades == 1
    assert report.blocked_signals == 1
    assert report.signal_to_trade_conversion == pytest.approx(0.5)
    assert dict(report.block_reason_counts) == {"SESSION_TRADE_LIMIT": 1}
    assert report.net_r == pytest.approx(outcome.net_r)
    assert report.cash_ledger.cash_pnl_eur == pytest.approx(outcome.net_r * 20.0)
    assert report.cash_ledger.final_balance_eur == pytest.approx(
        1000.0 + outcome.net_r * 20.0
    )
    assert report.execution_capability == "NONE"
    assert report.order_execution_enabled is False
