from daxlab.research.backtest_forward_degradation import v11_2_active_reference
from daxlab.research.forward_shadow_performance import (
    ALLOWED,
    ShadowSignalObservation,
    build_forward_shadow_performance_report,
)
from daxlab.research.rolling_backtest_forward_degradation import (
    build_rolling_backtest_forward_degradation_series,
)


def shadow_report(window: str, r_result: float):
    return build_forward_shadow_performance_report(
        window,
        (ShadowSignalObservation(f"{window}-a", ALLOWED, r_result=r_result),),
        starting_balance_eur=1000.0,
        fixed_risk_eur=20.0,
    )


def test_overlapping_rolling_points_are_marked_monitoring_only():
    reports = (
        shadow_report("W1", 1.0),
        shadow_report("W2", -0.5),
        shadow_report("W3", 0.25),
    )
    result = build_rolling_backtest_forward_degradation_series(
        v11_2_active_reference(), reports, rolling_width=2
    )
    assert result.points_overlap is True
    assert result.monitoring_only is True
    assert result.independence_claimed is False
    payload = result.to_payload()
    assert payload["points_overlap"] is True
    assert payload["monitoring_only"] is True
    assert payload["independence_claimed"] is False


def test_width_one_does_not_claim_overlap_or_independence():
    reports = (
        shadow_report("W1", 1.0),
        shadow_report("W2", -0.5),
    )
    result = build_rolling_backtest_forward_degradation_series(
        v11_2_active_reference(), reports, rolling_width=1
    )
    assert result.points_overlap is False
    assert result.monitoring_only is True
    assert result.independence_claimed is False
