import math

import pytest

from daxlab.research.backtest_forward_degradation import (
    HistoricalOOSReference,
    build_backtest_forward_degradation_report,
)
from daxlab.research.forward_shadow_performance import (
    ALLOWED,
    BLOCKED,
    ShadowSignalObservation,
    build_forward_shadow_performance_report,
)
from daxlab.research.forward_shadow_rolling_summary import summarize_forward_shadow_windows


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


def historical_reference():
    return HistoricalOOSReference(
        reference_id="V11.2_NORMAL_OOS_2014_2019",
        windows=81,
        trades=856,
        net_r=-31.309210619787684,
        positive_windows=37,
        negative_windows=44,
    )


def test_report_uses_verified_v11_2_reference_and_normalized_forward_metrics():
    summary = summarize_forward_shadow_windows(
        (
            shadow_report("W1", (1.0, -0.5), blocked=1),
            shadow_report("W2", (0.5,)),
            shadow_report("W3", (-1.0,)),
        )
    )

    result = build_backtest_forward_degradation_report(historical_reference(), summary)

    assert result.historical_windows == 81
    assert result.forward_windows == 3
    assert result.historical_trades_per_window == pytest.approx(856 / 81)
    assert result.forward_trades_per_window == pytest.approx(4 / 3)
    assert result.trade_activity_ratio == pytest.approx((4 / 3) / (856 / 81))
    assert result.historical_r_per_trade == pytest.approx(-31.309210619787684 / 856)
    assert result.forward_r_per_trade == pytest.approx(0.0)
    assert result.r_per_trade_delta == pytest.approx(0.0 - (-31.309210619787684 / 856))
    assert result.historical_positive_window_rate == pytest.approx(37 / 81)
    assert result.forward_positive_window_rate == pytest.approx(2 / 3)
    assert result.historical_negative_window_rate == pytest.approx(44 / 81)
    assert result.forward_negative_window_rate == pytest.approx(1 / 3)
    assert result.forward_signal_to_trade_conversion == pytest.approx(4 / 5)
    assert result.forward_total_cash_pnl_eur == pytest.approx(0.0)
    assert result.descriptive_only is True
    assert result.composite_score is None
    assert result.automatic_promotion is False
    assert result.execution_capability == "NONE"
    assert result.order_execution_enabled is False


def test_zero_forward_trades_is_described_without_inventing_per_trade_result():
    summary = summarize_forward_shadow_windows(
        (
            shadow_report("W1", (), blocked=1),
            shadow_report("W2", (), blocked=2),
        )
    )

    result = build_backtest_forward_degradation_report(historical_reference(), summary)

    assert result.forward_trades_per_window == 0.0
    assert result.trade_activity_ratio == 0.0
    assert result.forward_r_per_trade is None
    assert result.r_per_trade_delta is None
    assert result.forward_signal_to_trade_conversion == 0.0


def test_report_hash_is_deterministic_for_same_inputs():
    summary = summarize_forward_shadow_windows((shadow_report("W1", (1.0,)),))
    first = build_backtest_forward_degradation_report(historical_reference(), summary)
    second = build_backtest_forward_degradation_report(historical_reference(), summary)
    assert first.report_sha256 == second.report_sha256
    assert len(first.report_sha256) == 64


@pytest.mark.parametrize(
    "bad_reference",
    [
        HistoricalOOSReference("", 81, 856, -31.0, 37, 44),
        HistoricalOOSReference("x", 0, 856, -31.0, 0, 0),
        HistoricalOOSReference("x", 81, 0, -31.0, 37, 44),
        HistoricalOOSReference("x", 81, 856, math.inf, 37, 44),
        HistoricalOOSReference("x", 81, 856, -31.0, -1, 82),
        HistoricalOOSReference("x", 81, 856, -31.0, 37, 43),
    ],
)
def test_invalid_historical_reference_fails_closed(bad_reference):
    summary = summarize_forward_shadow_windows((shadow_report("W1", (1.0,)),))
    with pytest.raises(ValueError):
        build_backtest_forward_degradation_report(bad_reference, summary)


def test_non_shadow_or_execution_capable_forward_input_fails_closed():
    summary = summarize_forward_shadow_windows((shadow_report("W1", (1.0,)),))

    unsafe = summary.__class__(
        **{
            **summary.__dict__,
            "execution_capability": "ORDER",
            "order_execution_enabled": True,
        }
    )
    with pytest.raises(ValueError, match="NO_ORDER"):
        build_backtest_forward_degradation_report(historical_reference(), unsafe)

    broker_backed = summary.__class__(
        **{
            **summary.__dict__,
            "simulated_only": False,
            "broker_balance": True,
        }
    )
    with pytest.raises(ValueError, match="SHADOW simulation evidence"):
        build_backtest_forward_degradation_report(historical_reference(), broker_backed)
