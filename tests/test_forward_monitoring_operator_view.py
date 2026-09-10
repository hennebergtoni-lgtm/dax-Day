from dataclasses import replace

import pytest

from daxlab.operator.forward_monitoring_view import (
    build_forward_monitoring_operator_view,
)
from daxlab.research.backtest_forward_degradation import v11_2_active_reference
from daxlab.research.forward_shadow_performance import (
    ALLOWED,
    ShadowSignalObservation,
    build_forward_shadow_performance_report,
)
from daxlab.research.rolling_backtest_forward_degradation import (
    build_rolling_backtest_forward_degradation,
)
from daxlab.research.rolling_degradation_monitoring_view import (
    build_rolling_degradation_monitoring_view,
)


def _monitoring_view():
    reports = []
    for idx, net_r in enumerate((1.0, -0.5, 1.5), start=1):
        observations = (
            ShadowSignalObservation(
                signal_id=f"W{idx}-S1",
                status=ALLOWED,
                r_result=net_r,
            ),
            ShadowSignalObservation(
                signal_id=f"W{idx}-S2",
                status=ALLOWED,
                r_result=0.0,
            ),
        )
        reports.append(
            build_forward_shadow_performance_report(
                window_id=f"W{idx}",
                observations=observations,
                starting_balance_eur=2000.0,
                fixed_risk_eur=10.0,
            )
        )
    series = build_rolling_backtest_forward_degradation(
        v11_2_active_reference(), reports, rolling_width=2
    )
    return build_rolling_degradation_monitoring_view(series)


def test_operator_view_is_read_only_and_evidence_linked():
    source = _monitoring_view()
    report = build_forward_monitoring_operator_view(source)
    payload = report.to_payload()

    assert payload["schema_version"] == "DAXLAB_FORWARD_MONITORING_OPERATOR_VIEW_V1"
    assert report.mode == "SHADOW"
    assert report.read_only is True
    assert report.monitoring_only is True
    assert report.execution_capability == "NONE"
    assert report.order_execution_enabled is False
    assert report.automatic_promotion is False
    assert report.composite_score is None
    assert report.monitoring_view_sha256 == source.view_sha256
    assert report.trend_summary_sha256 == source.trend.summary_sha256
    assert report.dispersion_report_sha256 == source.dispersion.report_sha256
    assert report.extremes_report_sha256 == source.extremes.report_sha256


def test_operator_view_is_deterministic():
    source = _monitoring_view()
    first = build_forward_monitoring_operator_view(source)
    second = build_forward_monitoring_operator_view(source)
    assert first.payload_sha256 == second.payload_sha256
    assert first.to_payload() == second.to_payload()


@pytest.mark.parametrize(
    "unsafe",
    [
        {"execution_capability": "BROKER"},
        {"order_execution_enabled": True},
        {"monitoring_only": False},
        {"statistical_significance_claimed": True},
        {"composite_score": 1.0},
        {"automatic_promotion": True},
    ],
)
def test_operator_view_fails_closed_on_unsafe_governance(unsafe):
    source = replace(_monitoring_view(), **unsafe)
    with pytest.raises(ValueError):
        build_forward_monitoring_operator_view(source)
