import pytest

from daxlab.research.backtest_forward_degradation import v11_2_active_reference
from daxlab.research.forward_shadow_performance import (
    ALLOWED,
    BLOCKED,
    ShadowSignalObservation,
    build_forward_shadow_performance_report,
)
from daxlab.research.rolling_backtest_forward_degradation import (
    build_rolling_backtest_forward_degradation_series,
)
from daxlab.research.rolling_degradation_trend_summary import (
    build_rolling_degradation_trend_summary,
)


def shadow_report(window, r_values=(), blocked=0):
    observations = [
        ShadowSignalObservation(f"{window}-a{i}", ALLOWED, r_result=value)
        for i, value in enumerate(r_values)
    ]
    observations.extend(
        ShadowSignalObservation(f"{window}-b{i}", BLOCKED, block_reason="FILTER")
        for i in range(blocked)
    )
    return build_forward_shadow_performance_report(
        window,
        tuple(observations),
        starting_balance_eur=1000.0,
        fixed_risk_eur=20.0,
    )


def test_trend_summary_reports_endpoint_deltas_without_score():
    reports = (
        shadow_report("W1", (1.0, -0.5), blocked=1),
        shadow_report("W2", (0.5,)),
        shadow_report("W3", (-1.0,)),
        shadow_report("W4", (1.5,)),
    )
    series = build_rolling_backtest_forward_degradation_series(
        v11_2_active_reference(), reports, rolling_width=2
    )
    result = build_rolling_degradation_trend_summary(series)

    first = series.points[0].degradation
    latest = series.points[-1].degradation
    assert result.point_count == 3
    assert result.first_end_window_id == "W2"
    assert result.latest_end_window_id == "W4"
    assert result.trade_activity_ratio_delta == pytest.approx(
        latest.trade_activity_ratio - first.trade_activity_ratio
    )
    assert result.forward_r_per_trade_delta == pytest.approx(
        latest.forward_r_per_trade - first.forward_r_per_trade
    )
    assert result.positive_window_rate_delta == pytest.approx(
        latest.forward_positive_window_rate - first.forward_positive_window_rate
    )
    assert result.negative_window_rate_delta == pytest.approx(
        latest.forward_negative_window_rate - first.forward_negative_window_rate
    )
    assert result.cash_pnl_eur_delta == pytest.approx(
        latest.forward_total_cash_pnl_eur - first.forward_total_cash_pnl_eur
    )
    assert result.monitoring_only is True
    assert result.statistical_significance_claimed is False
    assert result.automatic_promotion is False
    assert result.execution_capability == "NONE"
    assert result.order_execution_enabled is False


def test_missing_endpoint_r_per_trade_returns_none_delta():
    reports = (
        shadow_report("W1", (), blocked=1),
        shadow_report("W2", (1.0,)),
    )
    series = build_rolling_backtest_forward_degradation_series(
        v11_2_active_reference(), reports, rolling_width=1
    )
    result = build_rolling_degradation_trend_summary(series)
    assert result.first_forward_r_per_trade is None
    assert result.latest_forward_r_per_trade == pytest.approx(1.0)
    assert result.forward_r_per_trade_delta is None


def test_hash_is_deterministic():
    series = build_rolling_backtest_forward_degradation_series(
        v11_2_active_reference(),
        (shadow_report("W1", (1.0,)), shadow_report("W2", (-0.5,))),
        rolling_width=1,
    )
    first = build_rolling_degradation_trend_summary(series)
    second = build_rolling_degradation_trend_summary(series)
    assert first.summary_sha256 == second.summary_sha256
    assert len(first.summary_sha256) == 64


def test_unsafe_or_non_monitoring_series_fails_closed():
    series = build_rolling_backtest_forward_degradation_series(
        v11_2_active_reference(), (shadow_report("W1", (1.0,)),), rolling_width=1
    )
    unsafe = series.__class__(
        **{**series.__dict__, "execution_capability": "ORDER", "order_execution_enabled": True}
    )
    with pytest.raises(ValueError, match="NO_ORDER"):
        build_rolling_degradation_trend_summary(unsafe)

    non_monitoring = series.__class__(
        **{**series.__dict__, "monitoring_only": False}
    )
    with pytest.raises(ValueError, match="monitoring-only governance"):
        build_rolling_degradation_trend_summary(non_monitoring)
