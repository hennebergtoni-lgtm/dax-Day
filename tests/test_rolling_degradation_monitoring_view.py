import pytest

from daxlab.research.backtest_forward_degradation import v11_2_active_reference
from daxlab.research.forward_shadow_performance import (
    ALLOWED,
    ShadowSignalObservation,
    build_forward_shadow_performance_report,
)
from daxlab.research.rolling_backtest_forward_degradation import (
    build_rolling_backtest_forward_degradation_series,
)
from daxlab.research.rolling_degradation_monitoring_view import (
    build_rolling_degradation_monitoring_view,
)


def shadow_report(window: str, r_result: float):
    return build_forward_shadow_performance_report(
        window,
        (ShadowSignalObservation(f"{window}-a", ALLOWED, r_result=r_result),),
        starting_balance_eur=1000.0,
        fixed_risk_eur=20.0,
    )


def test_monitoring_view_composes_same_source_series_without_new_score():
    series = build_rolling_backtest_forward_degradation_series(
        v11_2_active_reference(),
        (
            shadow_report("W1", 1.0),
            shadow_report("W2", -0.5),
            shadow_report("W3", 0.25),
        ),
        rolling_width=2,
    )
    result = build_rolling_degradation_monitoring_view(series)

    assert result.source_series_sha256 == series.series_sha256
    assert result.trend.source_series_sha256 == series.series_sha256
    assert result.dispersion.source_series_sha256 == series.series_sha256
    assert result.extremes.source_series_sha256 == series.series_sha256
    assert result.point_count == len(series.points)
    assert result.monitoring_only is True
    assert result.statistical_significance_claimed is False
    assert result.composite_score is None
    assert result.automatic_promotion is False
    assert result.execution_capability == "NONE"
    assert result.order_execution_enabled is False


def test_view_hash_is_deterministic():
    series = build_rolling_backtest_forward_degradation_series(
        v11_2_active_reference(),
        (shadow_report("W1", 1.0), shadow_report("W2", -0.5)),
        rolling_width=1,
    )
    first = build_rolling_degradation_monitoring_view(series)
    second = build_rolling_degradation_monitoring_view(series)
    assert first.view_sha256 == second.view_sha256
    assert first.trend.summary_sha256 == second.trend.summary_sha256
    assert first.dispersion.report_sha256 == second.dispersion.report_sha256
    assert first.extremes.report_sha256 == second.extremes.report_sha256
    assert len(first.view_sha256) == 64


def test_unsafe_or_non_monitoring_series_fails_closed():
    series = build_rolling_backtest_forward_degradation_series(
        v11_2_active_reference(), (shadow_report("W1", 1.0),), rolling_width=1
    )
    unsafe = series.__class__(
        **{**series.__dict__, "execution_capability": "ORDER", "order_execution_enabled": True}
    )
    with pytest.raises(ValueError, match="NO_ORDER"):
        build_rolling_degradation_monitoring_view(unsafe)

    non_monitoring = series.__class__(**{**series.__dict__, "monitoring_only": False})
    with pytest.raises(ValueError, match="monitoring-only governance"):
        build_rolling_degradation_monitoring_view(non_monitoring)
