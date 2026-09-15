from dataclasses import replace
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from daxlab.runtime.candidate_admission import Cand001AdmissionState, admit_cand001_trade
from daxlab.runtime.candidate_config import Cand001Config
from daxlab.runtime.candidate_decision import build_cand001_decision
from daxlab.runtime.candidate_execution_intent import build_cand001_execution_intent
from daxlab.runtime.candidate_signal import Cand001Signal, SignalDirection, SignalReason
from daxlab.runtime.candidate_sizing import Cand001SimulationSizingPolicy
from daxlab.runtime.candidate_trade_plan import build_cand001_trade_plan
from daxlab.runtime.contracts import RuntimeMode
from daxlab.runtime.decision import FinalAction
from daxlab.runtime.manifests import RunManifest
from daxlab.runtime.paper_contracts import Side


BERLIN = ZoneInfo("Europe/Berlin")


def _trade(direction: SignalDirection):
    event = datetime(2026, 9, 11, 9, 15, tzinfo=BERLIN)
    signal = Cand001Signal(
        event_time=event,
        close_time=event + timedelta(minutes=5),
        direction=direction,
        reason=(
            SignalReason.LONG_BREAKOUT
            if direction is SignalDirection.LONG
            else SignalReason.SHORT_BREAKOUT
        ),
        or_high=103.0,
        or_low=98.0,
        trigger_price=104.0 if direction is SignalDirection.LONG else 97.0,
        data_fingerprint="a" * 64,
    )
    plan = build_cand001_trade_plan(signal)
    assert plan is not None
    admission = admit_cand001_trade(Cand001AdmissionState(), signal, plan)
    decision = build_cand001_decision(signal, admission)
    assert decision.final_action is FinalAction.TRADE
    return plan, decision


def _manifest(
    *,
    config: Cand001Config,
    sizing: Cand001SimulationSizingPolicy,
    mode: RuntimeMode = RuntimeMode.SHADOW,
) -> RunManifest:
    return RunManifest.build(
        dataset_fingerprint="d" * 64,
        engine_fingerprint="e" * 64,
        config={"candidate": config, "sizing": sizing},
        mode=mode,
    )


@pytest.mark.parametrize(
    ("direction", "expected_side"),
    [
        (SignalDirection.LONG, Side.BUY),
        (SignalDirection.SHORT, Side.SELL),
    ],
)
def test_trade_decision_maps_deterministically_to_existing_execution_intent(
    direction, expected_side
) -> None:
    config = Cand001Config()
    sizing = Cand001SimulationSizingPolicy()
    plan, decision = _trade(direction)
    manifest = _manifest(config=config, sizing=sizing)

    left = build_cand001_execution_intent(
        decision=decision,
        trade_plan=plan,
        run_manifest=manifest,
        config=config,
        sizing=sizing,
    )
    right = build_cand001_execution_intent(
        decision=decision,
        trade_plan=plan,
        run_manifest=manifest,
        config=config,
        sizing=sizing,
    )

    assert left == right
    assert left.decision_id == decision.decision_id
    assert left.run_manifest_fingerprint == manifest.manifest_fingerprint
    assert left.created_at == decision.event_time
    assert left.symbol == "DE40"
    assert left.side is expected_side
    assert left.quantity == 1.0
    assert left.requested_price == plan.entry_price
    assert left.stop_price == plan.stop_price
    assert left.target_price == plan.target_price
    assert len(left.client_order_id) == 64


def test_non_trade_decision_cannot_create_execution_intent() -> None:
    config = Cand001Config()
    sizing = Cand001SimulationSizingPolicy()
    plan, decision = _trade(SignalDirection.LONG)
    blocked = replace(decision, final_action=FinalAction.NO_TRADE)

    with pytest.raises(ValueError, match="TRADE decision"):
        build_cand001_execution_intent(
            decision=blocked,
            trade_plan=plan,
            run_manifest=_manifest(config=config, sizing=sizing),
            config=config,
            sizing=sizing,
        )


@pytest.mark.parametrize("mode", [RuntimeMode.HISTORICAL, RuntimeMode.REPLAY, RuntimeMode.PAPER, RuntimeMode.LIVE])
def test_current_adapter_accepts_shadow_manifest_only(mode) -> None:
    config = Cand001Config()
    sizing = Cand001SimulationSizingPolicy()
    plan, decision = _trade(SignalDirection.LONG)

    with pytest.raises(ValueError, match="SHADOW"):
        build_cand001_execution_intent(
            decision=decision,
            trade_plan=plan,
            run_manifest=_manifest(config=config, sizing=sizing, mode=mode),
            config=config,
            sizing=sizing,
        )


def test_manifest_must_bind_candidate_and_sizing_policy() -> None:
    config = Cand001Config()
    sizing = Cand001SimulationSizingPolicy()
    plan, decision = _trade(SignalDirection.SHORT)
    wrong_manifest = RunManifest.build(
        dataset_fingerprint="d" * 64,
        engine_fingerprint="e" * 64,
        config={"candidate": config},
        mode=RuntimeMode.SHADOW,
    )

    with pytest.raises(ValueError, match="config fingerprint"):
        build_cand001_execution_intent(
            decision=decision,
            trade_plan=plan,
            run_manifest=wrong_manifest,
            config=config,
            sizing=sizing,
        )


def test_trade_plan_and_decision_provenance_must_match() -> None:
    config = Cand001Config()
    sizing = Cand001SimulationSizingPolicy()
    plan, decision = _trade(SignalDirection.LONG)
    wrong_plan = replace(plan, signal_data_fingerprint="b" * 64)

    with pytest.raises(ValueError, match="provenance"):
        build_cand001_execution_intent(
            decision=decision,
            trade_plan=wrong_plan,
            run_manifest=_manifest(config=config, sizing=sizing),
            config=config,
            sizing=sizing,
        )
