from dataclasses import replace
from datetime import datetime, timedelta
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest

from daxlab.runtime.candidate_dual_compare import (
    OutcomeDomain,
    StrategyParityStatus,
    build_cand001_shadow_dual_compare,
)
from daxlab.runtime.candidate_pipeline import Cand001PipelineState, process_cand001_candle
from daxlab.runtime.component_transition import ComponentRoute, ProviderSlot, TransitionMode
from daxlab.runtime.contracts import Candle
from daxlab.runtime.shadow_observation import ShadowObservationInput, build_shadow_decision


BERLIN = ZoneInfo("Europe/Berlin")


def _bar(hour, minute, *, open_price, high_price, low_price, close_price):
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


def _candidate_result():
    state = Cand001PipelineState()
    for candle in (
        _bar(9, 0, open_price=100, high_price=102, low_price=99, close_price=101),
        _bar(9, 5, open_price=101, high_price=103, low_price=98, close_price=102),
        _bar(9, 10, open_price=102, high_price=102.5, low_price=98.5, close_price=101),
    ):
        result = process_cand001_candle(
            state,
            candle,
            observed_at=candle.close_time + timedelta(seconds=1),
        )
        state = result.state
    breakout = _bar(9, 15, open_price=102, high_price=105, low_price=101, close_price=104)
    return process_cand001_candle(
        state,
        breakout,
        observed_at=breakout.close_time + timedelta(seconds=1),
    )


def _route(result, *, authoritative_slot=ProviderSlot.LEGACY):
    return ComponentRoute(
        component_id="strategy",
        contract_version="v1",
        mode=TransitionMode.DUAL_COMPARE,
        legacy_provider_id="legacy.v112.shadow.v1",
        bot_1x_provider_id="bot1x.cand001.strategy.v1",
        authoritative_slot=authoritative_slot,
        active_config_fingerprint=result.decision.config_fingerprint,
        comparison_policy_version="cand001-shadow-domain-v1",
    )


def _legacy_decision(result, fingerprint):
    return build_shadow_decision(
        ShadowObservationInput(
            observed_at=result.decision.event_time + timedelta(seconds=1),
            symbol="DE40",
            closed_bar_fingerprint=fingerprint,
            host_read_only_healthy=True,
            feed_fresh=True,
            clock_ok=True,
            single_instance_lock_held=True,
        )
    )


def test_dual_compare_keeps_legacy_authoritative_and_marks_domains_not_comparable():
    candidate = _candidate_result()
    bar_fingerprint = "a" * 64
    legacy = _legacy_decision(candidate, bar_fingerprint)

    record = build_cand001_shadow_dual_compare(
        route=_route(candidate),
        legacy_decision=legacy,
        candidate_result=candidate,
        candidate_bar_fingerprint=bar_fingerprint,
    )

    assert record.authoritative_slot == "legacy"
    assert record.authoritative_provider_id == "legacy.v112.shadow.v1"
    assert record.legacy.domain is OutcomeDomain.SHADOW_ORDER_SAFETY
    assert record.legacy.outcome == "NO_ORDER"
    assert record.bot_1x.domain is OutcomeDomain.STRATEGY_DECISION
    assert record.bot_1x.outcome == "TRADE"
    assert record.strategy_parity_status is StrategyParityStatus.UNAVAILABLE_DOMAIN_MISMATCH
    assert record.execution_capability == "NONE"
    assert record.order_execution_enabled is False
    assert len(record.comparison_fingerprint) == 64


def test_dual_compare_rejects_silent_bot_1x_authority_promotion():
    candidate = _candidate_result()
    bar_fingerprint = "b" * 64
    legacy = _legacy_decision(candidate, bar_fingerprint)

    with pytest.raises(ValueError, match="LEGACY to remain authoritative"):
        build_cand001_shadow_dual_compare(
            route=_route(candidate, authoritative_slot=ProviderSlot.BOT_1X),
            legacy_decision=legacy,
            candidate_result=candidate,
            candidate_bar_fingerprint=bar_fingerprint,
        )


def test_dual_compare_rejects_cross_bar_evidence():
    candidate = _candidate_result()
    legacy = _legacy_decision(candidate, "c" * 64)

    with pytest.raises(ValueError, match="same closed bar"):
        build_cand001_shadow_dual_compare(
            route=_route(candidate),
            legacy_decision=legacy,
            candidate_result=candidate,
            candidate_bar_fingerprint="d" * 64,
        )


def test_dual_compare_rejects_candidate_safety_escalation():
    candidate = _candidate_result()
    bar_fingerprint = "e" * 64
    legacy = _legacy_decision(candidate, bar_fingerprint)
    unsafe_snapshot = SimpleNamespace(
        execution_capability="PAPER",
        order_execution_enabled=False,
        decision_id=candidate.operator_snapshot.decision_id,
        snapshot_fingerprint=candidate.operator_snapshot.snapshot_fingerprint,
    )
    unsafe_candidate = replace(candidate, operator_snapshot=unsafe_snapshot)

    with pytest.raises(ValueError, match="cannot carry execution capability"):
        build_cand001_shadow_dual_compare(
            route=_route(candidate),
            legacy_decision=legacy,
            candidate_result=unsafe_candidate,
            candidate_bar_fingerprint=bar_fingerprint,
        )


def test_dual_compare_is_deterministic_for_identical_evidence():
    candidate = _candidate_result()
    bar_fingerprint = "f" * 64
    legacy = _legacy_decision(candidate, bar_fingerprint)
    route = _route(candidate)

    first = build_cand001_shadow_dual_compare(
        route=route,
        legacy_decision=legacy,
        candidate_result=candidate,
        candidate_bar_fingerprint=bar_fingerprint,
    )
    second = build_cand001_shadow_dual_compare(
        route=route,
        legacy_decision=legacy,
        candidate_result=candidate,
        candidate_bar_fingerprint=bar_fingerprint,
    )

    assert first == second
