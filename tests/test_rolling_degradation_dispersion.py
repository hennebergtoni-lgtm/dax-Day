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
from daxlab.research.rolling_degradation_dispersion import (
    build_rolling_degradation_dispersion_report,
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


def test_dispersion_reports_observed_min_max_and_span():
    reports = (
        shadow_report("W1", (1.0, -0.5), blocked=1),
        shadow_report("W2", (0.5,)),
        shadow_report("W3", (-1.0,)),
        shadow_report("W4", (1.5,)),
    )
    series = build_rolling_backtest_forward_degradation_series(
        v11_2_active_reference(), reports, rolling_width=2
    )
    result = build_rolling_degradation_dispersion_report(series)

    values = [point.degradation.forward_r_per_trade for point in series.points]
    observed = [value for value in values if value is not None]
    assert result.point_count == 3
    assert result.forward_r_per_trade.minimum == pytest.approx(min(observed))
    assert result.forward_r_per_trade.maximum == pytest.approx(max(observed))
    assert result.forward_r_per_trade.span == pytest.approx(max(observed) - min(observed))
    assert result.forward_r_per_trade.observed_count == len(observed)
    assert result.monitoring_only is True
    assert result.statistical_significance_claimed is False
    assert result.composite_score is None
    assert result.automatic_promotion is False
    assert result.execution_capability == "NONE"
    assert result.order_execution_enabled is False


def test_missing_r_per_trade_is_excluded_not_zero_filled():
    series = build_rolling_backtest_forward_degradation_series(
        v11_2_active_reference(),
        (
            shadow_report("W1", (), blocked=1),
            shadow_report("W2", (1.0,)),
            shadow_report("W3", (), blocked=1),
        ),
        rolling_width=1,
    )
    result = build_rolling_degradation_dispersion_report(series)
    assert result.forward_r_per_trade.observed_count == 1
    assert result.forward_r_per_trade.minimum == pytest.approx(1.0)
    assert result.forward_r_per_trade.maximum == pytest.approx(1.0)
    assert result.forward_r_per_trade.span == pytest.approx(0.0)


def test_hash_is_deterministic_for_same_series():
    series = build_rolling_backtest_forward_degradation_series(
        v11_2_active_reference(),
        (shadow_report("W1", (1.0,)), shadow_report("W2", (-0.5,))),
        rolling_width=1,
    )
    first = build_rolling_degradation_dispersion_report(series)
    second = build_rolling_degradation_dispersion_report(series)
    assert first.report_sha256 == second.report_sha256
    assert len(first.report_sha256) == 64


def test_unsafe_or_non_monitoring_series_fails_closed():
    series = build_rolling_backtest_forward_degradation_series(
        v11_2_active_reference(), (shadow_report("W1", (1.0,)),), rolling_width=1
    )
    unsafe = series.__class__(
        **{**series.__dict__, "execution_capability": "ORDER", "order_execution_enabled": True}
    )
    with pytest.raises(ValueError, match="NO_ORDER"):
        build_rolling_degradation_dispersion_report(unsafe)

    non_monitoring = series.__class__(**{**series.__dict__, "monitoring_only": False})
    with pytest.raises(ValueError, match="monitoring-only governance"):
        build_rolling_degradation_dispersion_report(non_monitoring)
