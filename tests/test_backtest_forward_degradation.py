import math

import pytest

from daxlab.research.backtest_forward_degradation import (
    V112_ENGINE_SHA256,
    V112_REFERENCE_ID,
    V112_REFERENCE_RESULT_BLOB_SHA,
    V112_REFERENCE_SOURCE,
    V112_SESSION_OHLC_SHA256,
    HistoricalOOSReference,
    build_backtest_forward_degradation_report,
    v11_2_active_reference,
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
    return v11_2_active_reference()


def test_canonical_v11_2_reference_matches_active_repository_reference():
    reference = v11_2_active_reference()

    assert reference.reference_id == V112_REFERENCE_ID == "V112_REFERENCE_V1"
    assert reference.windows == 81
    assert reference.trades == 856
    assert reference.net_r == pytest.approx(-31.309210619787684)
    assert reference.positive_windows == 37
    assert reference.negative_windows == 44
    assert reference.flat_windows == 0
    assert reference.source_path == V112_REFERENCE_SOURCE == "research/V112_REFERENCE_V1/reference_result.json"
    assert reference.source_blob_sha == V112_REFERENCE_RESULT_BLOB_SHA == "397af5ae3d17fc1ad427cf6abbfa72f3c7a8564d"
    assert reference.session_ohlc_sha256 == V112_SESSION_OHLC_SHA256 == (
        "e51bba6cb2befe5e7eb0376318e43b096a3e2ecaae3f556019862975c60286a2"
    )
    assert reference.engine_sha256 == V112_ENGINE_SHA256 == (
        "b3d62e0cad72420d36ade523857d024d4a334298be51a8313069e36614bda888"
    )
    reference.validate()


def test_report_uses_verified_v11_2_reference_and_normalized_forward_metrics():
    summary = summarize_forward_shadow_windows(
        (
            shadow_report("W1", (1.0, -0.5), blocked=1),
            shadow_report("W2", (0.5,)),
            shadow_report("W3", (-1.0,)),
        )
    )

    result = build_backtest_forward_degradation_report(historical_reference(), summary)

    assert result.historical_reference_id == "V112_REFERENCE_V1"
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
    assert result.historical_source_path == V112_REFERENCE_SOURCE
    assert result.historical_source_blob_sha == V112_REFERENCE_RESULT_BLOB_SHA
    assert result.historical_session_ohlc_sha256 == V112_SESSION_OHLC_SHA256
    assert result.historical_engine_sha256 == V112_ENGINE_SHA256
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
