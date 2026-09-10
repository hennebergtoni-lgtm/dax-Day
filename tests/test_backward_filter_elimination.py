from daxlab.research.backward_filter_elimination import evaluate_backward_filter_elimination


def test_removing_harmful_filter_improves_cash_and_survival():
    baseline = (1.0, -1.0, 2.0)
    filters = (
        ("GOOD", (True, False, True)),
        ("HARMFUL", (False, True, True)),
    )
    report = evaluate_backward_filter_elimination(
        baseline, filters, starting_balance_eur=1000.0, fixed_risk_eur=20.0
    )
    harmful = next(item for item in report.removals if item.removed_filter_id == "HARMFUL")
    assert harmful.cash_pnl_delta_reduced_minus_full_eur > 0.0
    assert harmful.additional_surviving_trades > 0


def test_removing_useful_filter_can_hurt_cash():
    baseline = (1.0, -2.0, 1.0)
    filters = (("LOSS_BLOCKER", (True, False, True)),)
    report = evaluate_backward_filter_elimination(
        baseline, filters, starting_balance_eur=1000.0, fixed_risk_eur=20.0
    )
    removal = report.removals[0]
    assert removal.cash_pnl_delta_reduced_minus_full_eur < 0.0
    assert removal.additional_surviving_trades == 1


def test_single_filter_neutral_removal_is_supported():
    baseline = (1.0, -1.0)
    filters = (("PASS_ALL", (True, True)),)
    report = evaluate_backward_filter_elimination(
        baseline, filters, starting_balance_eur=1000.0, fixed_risk_eur=20.0
    )
    removal = report.removals[0]
    assert removal.cash_pnl_delta_reduced_minus_full_eur == 0.0
    assert removal.additional_surviving_trades == 0


def test_filter_order_is_bound_into_report_hash():
    baseline = (1.0, -1.0, 2.0)
    a = ("A", (True, False, True))
    b = ("B", (False, True, True))
    first = evaluate_backward_filter_elimination(
        baseline, (a, b), starting_balance_eur=1000.0, fixed_risk_eur=20.0
    )
    second = evaluate_backward_filter_elimination(
        baseline, (b, a), starting_balance_eur=1000.0, fixed_risk_eur=20.0
    )
    assert first.report_sha256 != second.report_sha256


def test_no_execution_or_auto_removal_is_exposed():
    report = evaluate_backward_filter_elimination(
        (1.0, -1.0), (("A", (True, False)),), starting_balance_eur=1000.0, fixed_risk_eur=20.0
    )
    payload = report.to_payload()
    assert payload["automatic_removal"] is False
    assert payload["research_only"] is True
    assert payload["execution_capability"] == "NONE"
    assert payload["order_execution_enabled"] is False
