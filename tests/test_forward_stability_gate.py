import pytest

from daxlab.research.forward_shadow_performance import (
    ALLOWED,
    BLOCKED,
    ShadowSignalObservation,
    build_forward_shadow_performance_report,
)
from daxlab.research.forward_shadow_rolling_summary import summarize_forward_shadow_windows
from daxlab.research.forward_stability_gate import (
    BLOCKED as GATE_BLOCKED,
    PASS,
    ForwardStabilityThresholds,
    evaluate_forward_stability_gate,
)


def report(window, r_values=(), blocked=0):
    obs = [
        ShadowSignalObservation(f"{window}-a{i}", ALLOWED, r_result=value)
        for i, value in enumerate(r_values)
    ]
    obs.extend(
        ShadowSignalObservation(f"{window}-b{i}", BLOCKED, block_reason="FILTER")
        for i in range(blocked)
    )
    return build_forward_shadow_performance_report(
        window,
        tuple(obs),
        starting_balance_eur=1000.0,
        fixed_risk_eur=20.0,
    )


def thresholds(**overrides):
    values = {
        "min_windows": 3,
        "min_allowed_trades": 3,
        "min_signal_to_trade_conversion": 0.5,
        "max_consecutive_negative_windows": 1,
        "max_best_window_share_of_positive_cash": 0.8,
    }
    values.update(overrides)
    return ForwardStabilityThresholds(**values)


def stable_summary():
    return summarize_forward_shadow_windows(
        (
            report("W1", (1.0,)),
            report("W2", (-0.5, 1.0)),
            report("W3", (0.5,), blocked=1),
        )
    )


def test_pass_when_all_explicit_thresholds_are_met():
    result = evaluate_forward_stability_gate(stable_summary(), thresholds())
    assert result.status == PASS
    assert result.blockers == ()
    assert result.automatic_promotion is False
    assert result.execution_capability == "NONE"
    assert result.order_execution_enabled is False


@pytest.mark.parametrize(
    ("override", "blocker"),
    [
        ({"min_windows": 4}, "INSUFFICIENT_WINDOWS"),
        ({"min_allowed_trades": 5}, "INSUFFICIENT_ALLOWED_TRADES"),
        ({"min_signal_to_trade_conversion": 0.9}, "SIGNAL_TO_TRADE_CONVERSION_TOO_LOW"),
        ({"max_consecutive_negative_windows": 0}, "NEGATIVE_WINDOW_STREAK_TOO_LONG"),
        ({"max_best_window_share_of_positive_cash": 0.4}, "BEST_WINDOW_CONCENTRATION_TOO_HIGH"),
    ],
)
def test_each_explicit_limit_can_block(override, blocker):
    result = evaluate_forward_stability_gate(stable_summary(), thresholds(**override))
    assert result.status == GATE_BLOCKED
    assert blocker in result.blockers


def test_no_positive_cash_windows_fail_closed():
    summary = summarize_forward_shadow_windows(
        (report("W1", (-1.0,)), report("W2", (-1.0,)), report("W3", (-1.0,)))
    )
    result = evaluate_forward_stability_gate(
        summary,
        thresholds(max_consecutive_negative_windows=3, min_signal_to_trade_conversion=1.0),
    )
    assert result.status == GATE_BLOCKED
    assert "NO_POSITIVE_CASH_WINDOWS" in result.blockers


def test_no_signals_fail_closed():
    summary = summarize_forward_shadow_windows((report("W1"), report("W2"), report("W3")))
    result = evaluate_forward_stability_gate(summary, thresholds(min_allowed_trades=1))
    assert "NO_SIGNAL_TO_TRADE_CONVERSION" in result.blockers
    assert "INSUFFICIENT_ALLOWED_TRADES" in result.blockers


@pytest.mark.parametrize(
    "bad",
    [
        ForwardStabilityThresholds(0, 1, 0.5, 1, 0.8),
        ForwardStabilityThresholds(1, 0, 0.5, 1, 0.8),
        ForwardStabilityThresholds(1, 1, -0.1, 1, 0.8),
        ForwardStabilityThresholds(1, 1, 1.1, 1, 0.8),
        ForwardStabilityThresholds(1, 1, 0.5, -1, 0.8),
        ForwardStabilityThresholds(1, 1, 0.5, 1, 1.1),
    ],
)
def test_invalid_thresholds_fail_closed(bad):
    with pytest.raises(ValueError):
        evaluate_forward_stability_gate(stable_summary(), bad)
