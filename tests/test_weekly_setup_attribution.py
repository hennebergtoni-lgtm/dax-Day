from dataclasses import replace
from datetime import datetime

import pytest

from daxlab.research.dated_shadow_outcome import build_dated_shadow_outcome
from daxlab.research.weekly_setup_attribution import build_weekly_setup_attribution
from daxlab.runtime.decision import DecisionRecord, FinalAction


def _outcome(event_time: str, r_result: float, suffix: str, *, regime="TREND", structure="BREAKOUT", setup="ORB"):
    decision = DecisionRecord.build(
        event_time=datetime.fromisoformat(event_time),
        data_fingerprint=(suffix * 64)[:64],
        regime=regime,
        structure=structure,
        setup=setup,
        filter_results={"session": True},
        blockers=(),
        risk_result="SHADOW_ONLY",
        config={"mode": "SHADOW", "suffix": suffix},
        core_version="V11.2",
        final_action=FinalAction.TRADE,
    )
    return build_dated_shadow_outcome(decision, r_result=r_result)


def test_groups_by_week_regime_structure_and_setup():
    reports = build_weekly_setup_attribution(
        (
            _outcome("2026-09-07T08:00:00+00:00", 1.0, "a"),
            _outcome("2026-09-08T08:00:00+00:00", -0.5, "b"),
            _outcome("2026-09-08T09:00:00+00:00", 2.0, "c", regime="RANGE", structure="RETEST", setup="ORB15"),
        )
    )
    assert len(reports) == 2
    first = reports[0]
    assert first.week_key == "2026-W37"
    assert first.trades == 2
    assert first.winning_trades == 1
    assert first.losing_trades == 1
    assert first.net_r == 0.5
    assert first.average_r_per_trade == 0.25
    assert first.descriptive_only is True
    assert first.automatic_selection is False
    assert first.execution_capability == "NONE"
    assert first.order_execution_enabled is False


def test_deterministic_and_chronological_source_evidence():
    later = _outcome("2026-09-08T09:00:00+00:00", -1.0, "d")
    earlier = _outcome("2026-09-08T08:00:00+00:00", 2.0, "e")
    first = build_weekly_setup_attribution((later, earlier))[0]
    second = build_weekly_setup_attribution((earlier, later))[0]
    assert first == second
    assert first.source_outcome_sha256_order == (earlier.outcome_sha256, later.outcome_sha256)


def test_berlin_week_assignment():
    report = build_weekly_setup_attribution(
        (_outcome("2026-09-06T22:30:00+00:00", 0.5, "f"),)
    )[0]
    assert report.week_key == "2026-W37"


def test_duplicate_decision_rejected():
    outcome = _outcome("2026-09-07T08:00:00+00:00", 1.0, "g")
    with pytest.raises(ValueError, match="unique decision_id"):
        build_weekly_setup_attribution((outcome, outcome))


@pytest.mark.parametrize(
    "unsafe",
    [
        {"execution_capability": "BROKER"},
        {"order_execution_enabled": True},
        {"simulated_only": False},
        {"broker_balance": True},
    ],
)
def test_unsafe_outcome_rejected(unsafe):
    outcome = replace(_outcome("2026-09-07T08:00:00+00:00", 1.0, "h"), **unsafe)
    with pytest.raises(ValueError):
        build_weekly_setup_attribution((outcome,))
