import pytest

from daxlab.research.forward_shadow_performance import (
    ALLOWED,
    BLOCKED,
    COMPLETE,
    NO_SIGNALS_OBSERVED,
    ShadowSignalObservation,
    build_forward_shadow_performance_report,
)


def test_mixed_window_reports_activity_cash_and_block_reasons():
    report = build_forward_shadow_performance_report(
        "2026-W37",
        (
            ShadowSignalObservation("s1", ALLOWED, r_result=1.0),
            ShadowSignalObservation("s2", BLOCKED, block_reason="ATR_FILTER"),
            ShadowSignalObservation("s3", ALLOWED, r_result=-1.0),
            ShadowSignalObservation("s4", BLOCKED, block_reason="ATR_FILTER"),
            ShadowSignalObservation("s5", ALLOWED, r_result=2.0),
        ),
        starting_balance_eur=1000.0,
        fixed_risk_eur=20.0,
    )
    assert report.status == COMPLETE
    assert report.generated_signals == 5
    assert report.allowed_shadow_trades == 3
    assert report.blocked_signals == 2
    assert report.signal_to_trade_conversion == pytest.approx(0.6)
    assert dict(report.block_reason_counts) == {"ATR_FILTER": 2}
    assert report.net_r == 2.0
    assert report.cash_ledger.final_balance_eur == 1040.0
    assert report.cash_ledger.cash_pnl_eur == 40.0
    assert report.winning_trades == 2
    assert report.losing_trades == 1


def test_zero_signal_window_is_explicit_not_fake_zero_conversion():
    report = build_forward_shadow_performance_report(
        "quiet-window", (), starting_balance_eur=1000.0, fixed_risk_eur=20.0
    )
    assert report.status == NO_SIGNALS_OBSERVED
    assert report.generated_signals == 0
    assert report.signal_to_trade_conversion is None
    assert report.cash_ledger.final_balance_eur == 1000.0


def test_all_signals_blocked_is_visible():
    report = build_forward_shadow_performance_report(
        "blocked-window",
        (
            ShadowSignalObservation("s1", BLOCKED, block_reason="A"),
            ShadowSignalObservation("s2", BLOCKED, block_reason="B"),
        ),
        starting_balance_eur=1000.0,
        fixed_risk_eur=20.0,
    )
    assert report.generated_signals == 2
    assert report.allowed_shadow_trades == 0
    assert report.signal_to_trade_conversion == 0.0
    assert report.cash_ledger.cash_pnl_eur == 0.0


def test_invalid_observation_contracts_fail_closed():
    with pytest.raises(ValueError):
        build_forward_shadow_performance_report(
            "w", (ShadowSignalObservation("s1", ALLOWED),),
            starting_balance_eur=1000.0, fixed_risk_eur=20.0,
        )
    with pytest.raises(ValueError):
        build_forward_shadow_performance_report(
            "w", (ShadowSignalObservation("s1", BLOCKED, r_result=1.0, block_reason="X"),),
            starting_balance_eur=1000.0, fixed_risk_eur=20.0,
        )
    with pytest.raises(ValueError):
        build_forward_shadow_performance_report(
            "w", (ShadowSignalObservation("s1", "UNKNOWN"),),
            starting_balance_eur=1000.0, fixed_risk_eur=20.0,
        )


def test_duplicate_signal_ids_fail_closed():
    with pytest.raises(ValueError):
        build_forward_shadow_performance_report(
            "w",
            (
                ShadowSignalObservation("s1", BLOCKED, block_reason="X"),
                ShadowSignalObservation("s1", BLOCKED, block_reason="Y"),
            ),
            starting_balance_eur=1000.0,
            fixed_risk_eur=20.0,
        )


def test_safety_flags_are_hard_exposed():
    report = build_forward_shadow_performance_report(
        "w", (), starting_balance_eur=1000.0, fixed_risk_eur=20.0
    )
    payload = report.to_payload()
    assert payload["simulated_only"] is True
    assert payload["broker_balance"] is False
    assert payload["execution_capability"] == "NONE"
    assert payload["order_execution_enabled"] is False
