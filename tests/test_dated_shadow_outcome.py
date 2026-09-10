from dataclasses import replace
from datetime import datetime, timezone

import pytest

from daxlab.research.dated_shadow_outcome import build_dated_shadow_outcome
from daxlab.runtime.decision import DecisionRecord, FinalAction


def _decision(*, final_action: FinalAction = FinalAction.TRADE, event_time=None):
    event_time = event_time or datetime(2026, 9, 10, 8, 35, tzinfo=timezone.utc)
    return DecisionRecord.build(
        event_time=event_time,
        data_fingerprint="a" * 64,
        regime="TREND",
        structure="BREAKOUT",
        setup="ORB",
        filter_results={"session": True},
        blockers=(),
        risk_result="SHADOW_ONLY",
        config={"mode": "SHADOW"},
        core_version="V11.2",
        final_action=final_action,
    )


def test_outcome_is_utc_normalized_and_no_order():
    report = build_dated_shadow_outcome(_decision(), r_result=1.25)
    assert report.event_time_utc == "2026-09-10T08:35:00+00:00"
    assert report.r_result == 1.25
    assert report.regime == "TREND"
    assert report.structure == "BREAKOUT"
    assert report.setup == "ORB"
    assert report.simulated_only is True
    assert report.broker_balance is False
    assert report.execution_capability == "NONE"
    assert report.order_execution_enabled is False


def test_outcome_sha_is_deterministic():
    decision = _decision()
    first = build_dated_shadow_outcome(decision, r_result=-0.5)
    second = build_dated_shadow_outcome(decision, r_result=-0.5)
    assert first.outcome_sha256 == second.outcome_sha256
    assert first.to_payload() == second.to_payload()


def test_timezone_offset_is_normalized_to_same_utc_instant():
    local = datetime.fromisoformat("2026-09-10T10:35:00+02:00")
    report = build_dated_shadow_outcome(_decision(event_time=local), r_result=0.0)
    assert report.event_time_utc == "2026-09-10T08:35:00+00:00"


def test_no_trade_decision_is_rejected():
    with pytest.raises(ValueError, match="TRADE decision"):
        build_dated_shadow_outcome(_decision(final_action=FinalAction.NO_TRADE), r_result=1.0)


def test_naive_decision_time_is_rejected():
    decision = replace(_decision(), event_time=datetime(2026, 9, 10, 8, 35))
    with pytest.raises(ValueError, match="timezone-aware"):
        build_dated_shadow_outcome(decision, r_result=1.0)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_r_is_rejected(value):
    with pytest.raises(ValueError, match="finite"):
        build_dated_shadow_outcome(_decision(), r_result=value)
