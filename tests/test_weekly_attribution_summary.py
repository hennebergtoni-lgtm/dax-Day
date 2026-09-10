from dataclasses import replace

import pytest

from daxlab.research.weekly_attribution_summary import build_weekly_attribution_summary
from daxlab.research.weekly_setup_attribution import WeeklySetupAttribution


def _report(regime: str, structure: str, setup: str, net_r: float, suffix: str):
    return WeeklySetupAttribution(
        week_key="2026-W37",
        regime=regime,
        structure=structure,
        setup=setup,
        trades=2,
        winning_trades=1,
        losing_trades=1,
        flat_trades=0,
        net_r=net_r,
        average_r_per_trade=net_r / 2.0,
        source_outcome_sha256_order=((suffix * 64)[:64],),
        report_sha256=(suffix * 64)[:64],
    )


def test_summary_exposes_observed_best_and_worst_without_selection():
    reports = (
        _report("TREND", "BREAKOUT", "ORB", 1.5, "a"),
        _report("RANGE", "RETEST", "ORB15", -0.5, "b"),
    )
    summary = build_weekly_attribution_summary(reports)[0]
    assert summary.groups == 2
    assert summary.trades == 4
    assert summary.net_r == 1.0
    assert summary.best_observed_group == "TREND / BREAKOUT / ORB"
    assert summary.best_observed_group_net_r == 1.5
    assert summary.worst_observed_group == "RANGE / RETEST / ORB15"
    assert summary.worst_observed_group_net_r == -0.5
    assert summary.descriptive_only is True
    assert summary.statistical_significance_claimed is False
    assert summary.automatic_selection is False
    assert summary.execution_capability == "NONE"
    assert summary.order_execution_enabled is False


def test_summary_is_deterministic_independent_of_input_order():
    first = _report("TREND", "BREAKOUT", "ORB", 1.5, "c")
    second = _report("RANGE", "RETEST", "ORB15", -0.5, "d")
    left = build_weekly_attribution_summary((first, second))[0]
    right = build_weekly_attribution_summary((second, first))[0]
    assert left == right


@pytest.mark.parametrize(
    "unsafe",
    [
        {"execution_capability": "BROKER"},
        {"order_execution_enabled": True},
        {"descriptive_only": False},
        {"automatic_selection": True},
    ],
)
def test_summary_rejects_unsafe_attribution(unsafe):
    report = replace(_report("TREND", "BREAKOUT", "ORB", 1.0, "e"), **unsafe)
    with pytest.raises(ValueError):
        build_weekly_attribution_summary((report,))


def test_empty_input_is_empty():
    assert build_weekly_attribution_summary(()) == ()
