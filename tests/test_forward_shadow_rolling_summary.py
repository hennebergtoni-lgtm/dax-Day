import pytest

from daxlab.research.forward_shadow_performance import (
    ALLOWED,
    BLOCKED,
    ShadowSignalObservation,
    build_forward_shadow_performance_report,
)
from daxlab.research.forward_shadow_rolling_summary import summarize_forward_shadow_windows


def make_report(window, observations):
    return build_forward_shadow_performance_report(
        window,
        observations,
        starting_balance_eur=1000.0,
        fixed_risk_eur=20.0,
    )


def test_rolling_summary_aggregates_activity_and_cash():
    w1 = make_report(
        "W1",
        (
            ShadowSignalObservation("a1", ALLOWED, r_result=2.0),
            ShadowSignalObservation("a2", BLOCKED, block_reason="F"),
        ),
    )
    w2 = make_report(
        "W2",
        (
            ShadowSignalObservation("b1", ALLOWED, r_result=-1.0),
            ShadowSignalObservation("b2", ALLOWED, r_result=0.5),
            ShadowSignalObservation("b3", BLOCKED, block_reason="G"),
        ),
    )
    summary = summarize_forward_shadow_windows((w1, w2))
    assert summary.window_count == 2
    assert summary.positive_cash_windows == 1
    assert summary.negative_cash_windows == 1
    assert summary.total_generated_signals == 5
    assert summary.total_allowed_shadow_trades == 3
    assert summary.total_blocked_signals == 2
    assert summary.aggregate_signal_to_trade_conversion == pytest.approx(3 / 5)
    assert summary.total_net_r == pytest.approx(1.5)
    assert summary.total_cash_pnl_eur == pytest.approx(30.0)
    assert summary.best_window_id == "W1"
    assert summary.best_window_cash_pnl_eur == pytest.approx(40.0)
    assert summary.worst_window_id == "W2"
    assert summary.worst_window_cash_pnl_eur == pytest.approx(-10.0)


def test_single_positive_window_concentration_is_explicit():
    w1 = make_report("W1", (ShadowSignalObservation("a", ALLOWED, r_result=3.0),))
    w2 = make_report("W2", (ShadowSignalObservation("b", ALLOWED, r_result=-1.0),))
    w3 = make_report("W3", (ShadowSignalObservation("c", ALLOWED, r_result=-1.0),))
    summary = summarize_forward_shadow_windows((w1, w2, w3))
    assert summary.best_window_share_of_positive_cash == 1.0


def test_no_signal_windows_do_not_create_fake_conversion():
    w1 = make_report("W1", ())
    w2 = make_report("W2", ())
    summary = summarize_forward_shadow_windows((w1, w2))
    assert summary.no_signal_windows == 2
    assert summary.aggregate_signal_to_trade_conversion is None
    assert summary.total_cash_pnl_eur == 0.0


def test_global_conversion_is_weighted_by_signal_count_not_window_average():
    w1 = make_report("W1", (ShadowSignalObservation("a", ALLOWED, r_result=1.0),))
    w2 = make_report(
        "W2",
        tuple(ShadowSignalObservation(f"b{i}", BLOCKED, block_reason="F") for i in range(9)),
    )
    summary = summarize_forward_shadow_windows((w1, w2))
    assert summary.aggregate_signal_to_trade_conversion == pytest.approx(0.1)


def test_window_order_is_bound_into_hash():
    w1 = make_report("W1", ())
    w2 = make_report("W2", ())
    first = summarize_forward_shadow_windows((w1, w2))
    second = summarize_forward_shadow_windows((w2, w1))
    assert first.summary_sha256 != second.summary_sha256


def test_empty_input_fails_closed():
    with pytest.raises(ValueError):
        summarize_forward_shadow_windows(())


def test_safety_flags_are_preserved():
    summary = summarize_forward_shadow_windows((make_report("W1", ()),))
    payload = summary.to_payload()
    assert payload["simulated_only"] is True
    assert payload["broker_balance"] is False
    assert payload["execution_capability"] == "NONE"
    assert payload["order_execution_enabled"] is False
