from dataclasses import replace
from datetime import datetime

import pytest

from daxlab.research.dated_shadow_outcome import build_dated_shadow_outcome
from daxlab.research.weekly_shadow_performance import build_weekly_shadow_performance
from daxlab.runtime.decision import DecisionRecord, FinalAction


def _outcome(event_time: str, r_result: float, suffix: str):
    decision = DecisionRecord.build(
        event_time=datetime.fromisoformat(event_time),
        data_fingerprint=(suffix * 64)[:64],
        regime="TREND",
        structure="BREAKOUT",
        setup="ORB",
        filter_results={"session": True},
        blockers=(),
        risk_result="SHADOW_ONLY",
        config={"mode": "SHADOW", "suffix": suffix},
        core_version="V11.2",
        final_action=FinalAction.TRADE,
    )
    return build_dated_shadow_outcome(decision, r_result=r_result)


def test_groups_by_berlin_iso_week_and_carries_balance_forward():
    outcomes = (
        _outcome("2026-09-06T21:30:00+00:00", 1.0, "a"),  # Sunday Berlin, W36
        _outcome("2026-09-07T08:00:00+00:00", -0.5, "b"),  # Monday Berlin, W37
        _outcome("2026-09-08T08:00:00+00:00", 2.0, "c"),
    )
    reports = build_weekly_shadow_performance(
        outcomes, starting_balance_eur=2000.0, fixed_risk_eur=10.0
    )

    assert [item.week_key for item in reports] == ["2026-W36", "2026-W37"]
    assert reports[0].trades == 1
    assert reports[0].net_r == 1.0
    assert reports[0].cash_ledger.starting_balance_eur == 2000.0
    assert reports[0].cash_ledger.final_balance_eur == 2010.0
    assert reports[1].trades == 2
    assert reports[1].net_r == 1.5
    assert reports[1].cash_ledger.starting_balance_eur == 2010.0
    assert reports[1].cash_ledger.final_balance_eur == 2025.0


def test_input_order_is_normalized_chronologically():
    later = _outcome("2026-09-09T10:00:00+00:00", -1.0, "d")
    earlier = _outcome("2026-09-08T10:00:00+00:00", 2.0, "e")
    report = build_weekly_shadow_performance(
        (later, earlier), starting_balance_eur=1000.0, fixed_risk_eur=20.0
    )[0]
    assert report.source_outcome_sha256_order == (
        earlier.outcome_sha256,
        later.outcome_sha256,
    )
    assert report.net_r == 1.0
    assert report.cash_ledger.cash_pnl_eur == 20.0


def test_berlin_week_assignment_uses_local_time_not_raw_utc_date():
    # Sunday 22:30 UTC is Monday 00:30 CEST, therefore ISO week 37 in Berlin.
    outcome = _outcome("2026-09-06T22:30:00+00:00", 0.5, "f")
    report = build_weekly_shadow_performance(
        (outcome,), starting_balance_eur=1000.0, fixed_risk_eur=10.0
    )[0]
    assert report.week_key == "2026-W37"
    assert report.timezone == "Europe/Berlin"


def test_report_is_deterministic():
    outcomes = (
        _outcome("2026-09-07T08:00:00+00:00", 1.0, "1"),
        _outcome("2026-09-08T08:00:00+00:00", -0.25, "2"),
    )
    first = build_weekly_shadow_performance(
        outcomes, starting_balance_eur=2000.0, fixed_risk_eur=10.0
    )
    second = build_weekly_shadow_performance(
        outcomes, starting_balance_eur=2000.0, fixed_risk_eur=10.0
    )
    assert first == second
    assert first[0].report_sha256 == second[0].report_sha256


def test_empty_outcomes_return_no_weeks():
    assert build_weekly_shadow_performance(
        (), starting_balance_eur=2000.0, fixed_risk_eur=10.0
    ) == ()


def test_duplicate_decision_id_is_rejected():
    outcome = _outcome("2026-09-07T08:00:00+00:00", 1.0, "3")
    with pytest.raises(ValueError, match="unique decision_id"):
        build_weekly_shadow_performance(
            (outcome, outcome), starting_balance_eur=2000.0, fixed_risk_eur=10.0
        )


@pytest.mark.parametrize(
    "unsafe",
    [
        {"execution_capability": "BROKER"},
        {"order_execution_enabled": True},
        {"simulated_only": False},
        {"broker_balance": True},
    ],
)
def test_unsafe_outcome_is_rejected(unsafe):
    outcome = replace(
        _outcome("2026-09-07T08:00:00+00:00", 1.0, "4"), **unsafe
    )
    with pytest.raises(ValueError):
        build_weekly_shadow_performance(
            (outcome,), starting_balance_eur=2000.0, fixed_risk_eur=10.0
        )
