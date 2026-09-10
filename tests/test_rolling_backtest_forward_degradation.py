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


def test_fixed_width_series_preserves_temporal_order_and_metrics():
    reports = (
        shadow_report("W1", (1.0, -0.5), blocked=1),
        shadow_report("W2", (0.5,)),
        shadow_report("W3", (-1.0,)),
        shadow_report("W4", (1.5,)),
    )

    result = build_rolling_backtest_forward_degradation_series(
        v11_2_active_reference(), reports, rolling_width=2
    )

    assert result.historical_reference_id == "V112_REFERENCE_V1"
    assert result.rolling_width == 2
    assert result.source_window_count == 4
    assert result.source_window_id_order == ("W1", "W2", "W3", "W4")
    assert len(result.points) == 3

    first, second, third = result.points
    assert first.window_ids == ("W1", "W2")
    assert first.start_index == 0
    assert first.end_index == 1
    assert first.degradation.forward_windows == 2
    assert first.degradation.forward_trades_per_window == pytest.approx(3 / 2)
    assert first.degradation.forward_r_per_trade == pytest.approx(1.0 / 3)
    assert first.degradation.forward_signal_to_trade_conversion == pytest.approx(3 / 4)

    assert second.window_ids == ("W2", "W3")
    assert second.degradation.forward_r_per_trade == pytest.approx(-0.25)
    assert third.window_ids == ("W3", "W4")
    assert third.degradation.forward_r_per_trade == pytest.approx(0.25)

    assert result.descriptive_only is True
    assert result.composite_score is None
    assert result.automatic_promotion is False
    assert result.execution_capability == "NONE"
    assert result.order_execution_enabled is False


def test_width_one_exposes_each_window_without_inventing_score():
    reports = (
        shadow_report("W1", (1.0,)),
        shadow_report("W2", (-1.0,)),
    )
    result = build_rolling_backtest_forward_degradation_series(
        v11_2_active_reference(), reports, rolling_width=1
    )
    assert [point.window_ids for point in result.points] == [("W1",), ("W2",)]
    assert all(point.composite_score is None for point in result.points)
    assert all(point.automatic_promotion is False for point in result.points)


def test_zero_trade_window_is_represented_without_fake_r_per_trade():
    reports = (
        shadow_report("W1", (), blocked=2),
        shadow_report("W2", (), blocked=1),
    )
    result = build_rolling_backtest_forward_degradation_series(
        v11_2_active_reference(), reports, rolling_width=2
    )
    point = result.points[0]
    assert point.degradation.forward_trades_per_window == 0.0
    assert point.degradation.forward_r_per_trade is None
    assert point.degradation.r_per_trade_delta is None
    assert point.degradation.forward_signal_to_trade_conversion == 0.0


def test_hashes_are_deterministic_and_order_sensitive():
    reports = (
        shadow_report("W1", (1.0,)),
        shadow_report("W2", (-0.5,)),
        shadow_report("W3", (0.25,)),
    )
    first = build_rolling_backtest_forward_degradation_series(
        v11_2_active_reference(), reports, rolling_width=2
    )
    second = build_rolling_backtest_forward_degradation_series(
        v11_2_active_reference(), reports, rolling_width=2
    )
    reversed_result = build_rolling_backtest_forward_degradation_series(
        v11_2_active_reference(), tuple(reversed(reports)), rolling_width=2
    )

    assert first.series_sha256 == second.series_sha256
    assert [p.point_sha256 for p in first.points] == [p.point_sha256 for p in second.points]
    assert first.series_sha256 != reversed_result.series_sha256
    assert len(first.series_sha256) == 64


@pytest.mark.parametrize("width", [0, -1, 4])
def test_invalid_rolling_width_fails_closed(width):
    reports = (
        shadow_report("W1", (1.0,)),
        shadow_report("W2", (-1.0,)),
        shadow_report("W3", (0.5,)),
    )
    with pytest.raises(ValueError):
        build_rolling_backtest_forward_degradation_series(
            v11_2_active_reference(), reports, rolling_width=width
        )


def test_empty_input_fails_closed():
    with pytest.raises(ValueError, match="at least one"):
        build_rolling_backtest_forward_degradation_series(
            v11_2_active_reference(), (), rolling_width=1
        )


def test_execution_capable_or_broker_backed_window_fails_closed():
    safe = shadow_report("W1", (1.0,))
    unsafe = safe.__class__(
        **{**safe.__dict__, "execution_capability": "ORDER", "order_execution_enabled": True}
    )
    with pytest.raises(ValueError, match="NO_ORDER"):
        build_rolling_backtest_forward_degradation_series(
            v11_2_active_reference(), (unsafe,), rolling_width=1
        )

    broker_backed = safe.__class__(
        **{**safe.__dict__, "simulated_only": False, "broker_balance": True}
    )
    with pytest.raises(ValueError, match="SHADOW simulation"):
        build_rolling_backtest_forward_degradation_series(
            v11_2_active_reference(), (broker_backed,), rolling_width=1
        )
