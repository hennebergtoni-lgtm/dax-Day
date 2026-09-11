from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from daxlab.runtime.candidate_config import Cand001Config
from daxlab.runtime.candidate_shadow_orchestrator import (
    Cand001ShadowState,
    process_cand001_shadow_candle,
)
from daxlab.runtime.candidate_sizing import Cand001SimulationSizingPolicy
from daxlab.runtime.candidate_virtual_lifecycle import VirtualPositionStatus
from daxlab.runtime.contracts import Candle, RuntimeMode
from daxlab.runtime.manifests import RunManifest


BERLIN = ZoneInfo("Europe/Berlin")


def _manifest(config: Cand001Config, sizing: Cand001SimulationSizingPolicy) -> RunManifest:
    return RunManifest.build(
        dataset_fingerprint="d" * 64,
        engine_fingerprint="e" * 64,
        config={"candidate": config, "sizing": sizing},
        mode=RuntimeMode.SHADOW,
    )


def _candle(hour: int, minute: int, *, open_: float, high: float, low: float, close: float) -> Candle:
    event = datetime(2026, 9, 11, hour, minute, tzinfo=BERLIN)
    return Candle(
        symbol="DE40",
        timeframe="5m",
        event_time=event,
        close_time=event + timedelta(minutes=5),
        open=open_,
        high=high,
        low=low,
        close=close,
        volume=None,
        source="TEST",
        received_at=event + timedelta(minutes=5, seconds=1),
        is_closed=True,
    )


def test_shadow_orchestrator_runs_trade_fill_exit_and_publication_once() -> None:
    config = Cand001Config()
    sizing = Cand001SimulationSizingPolicy()
    manifest = _manifest(config, sizing)
    state = Cand001ShadowState()

    bars = (
        _candle(9, 0, open_=100.0, high=102.0, low=99.0, close=101.0),
        _candle(9, 5, open_=101.0, high=103.0, low=100.0, close=102.0),
        _candle(9, 10, open_=102.0, high=103.0, low=98.0, close=101.0),
    )
    for candle in bars:
        result = process_cand001_shadow_candle(
            state,
            candle,
            observed_at=candle.received_at,
            run_manifest=manifest,
            config=config,
            sizing=sizing,
        )
        state = result.state
        assert result.intent_to_publish is None
        assert result.outcome_to_publish is None

    breakout = _candle(9, 15, open_=101.0, high=105.0, low=100.0, close=104.0)
    trade = process_cand001_shadow_candle(
        state,
        breakout,
        observed_at=breakout.received_at,
        run_manifest=manifest,
        config=config,
        sizing=sizing,
    )
    state = trade.state

    assert trade.pipeline_result.decision.final_action.value == "TRADE"
    assert trade.intent_to_publish is not None
    assert trade.intent_publication is not None and trade.intent_publication.accepted
    assert state.active_trade is not None
    assert state.active_trade.lifecycle.status is VirtualPositionStatus.PENDING_ENTRY
    origin_decision_id = trade.pipeline_result.decision.decision_id
    assert trade.operator_snapshot.as_dict()["virtual_position"]["origin_decision_id"] == origin_decision_id

    fill_bar = _candle(9, 20, open_=104.0, high=108.0, low=101.0, close=106.0)
    filled = process_cand001_shadow_candle(
        state,
        fill_bar,
        observed_at=fill_bar.received_at,
        run_manifest=manifest,
        config=config,
        sizing=sizing,
    )
    state = filled.state

    assert filled.pipeline_result.decision.final_action.value == "NO_TRADE"
    assert "SESSION_TRADE_LIMIT" in filled.pipeline_result.decision.blockers
    assert filled.intent_to_publish is None
    assert state.active_trade is not None
    assert state.active_trade.lifecycle.status is VirtualPositionStatus.OPEN
    fill_payload = filled.operator_snapshot.as_dict()
    assert fill_payload["decision"]["decision_id"] != origin_decision_id
    assert fill_payload["virtual_position"]["origin_decision_id"] == origin_decision_id
    assert fill_payload["virtual_position"]["status"] == "OPEN"

    target_bar = _candle(9, 25, open_=106.0, high=114.0, low=103.0, close=113.0)
    closed = process_cand001_shadow_candle(
        state,
        target_bar,
        observed_at=target_bar.received_at,
        run_manifest=manifest,
        config=config,
        sizing=sizing,
    )
    state = closed.state

    assert state.active_trade is None
    assert closed.outcome_to_publish is not None
    assert closed.outcome_publication is not None and closed.outcome_publication.accepted
    assert closed.outcome_to_publish.decision_id == origin_decision_id
    assert closed.outcome_to_publish.net_r < closed.outcome_to_publish.gross_r
    closed_payload = closed.operator_snapshot.as_dict()
    assert closed_payload["decision"]["action"] == "NO_TRADE"
    assert closed_payload["virtual_position"]["origin_decision_id"] == origin_decision_id
    assert closed_payload["virtual_position"]["status"] == "CLOSED"
    assert closed_payload["outcome"]["outcome_id"] == closed.outcome_to_publish.outcome_id
    assert len(state.publication.published_intent_ids) == 1
    assert len(state.publication.published_outcome_ids) == 1
    assert closed.execution_capability == "NONE"
    assert closed.order_execution_enabled is False


def test_shadow_orchestrator_rejects_non_shadow_manifest() -> None:
    config = Cand001Config()
    sizing = Cand001SimulationSizingPolicy()
    manifest = RunManifest.build(
        dataset_fingerprint="d" * 64,
        engine_fingerprint="e" * 64,
        config={"candidate": config, "sizing": sizing},
        mode=RuntimeMode.PAPER,
    )
    candle = _candle(9, 0, open_=100.0, high=102.0, low=99.0, close=101.0)

    with pytest.raises(ValueError, match="SHADOW RunManifest"):
        process_cand001_shadow_candle(
            Cand001ShadowState(),
            candle,
            observed_at=candle.received_at,
            run_manifest=manifest,
            config=config,
            sizing=sizing,
        )
