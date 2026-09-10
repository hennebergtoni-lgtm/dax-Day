from dataclasses import replace

import pytest

from daxlab.research.shadow_cash_ledger import simulate_fixed_risk_cash_ledger
from daxlab.research.shadow_risk_observation import build_shadow_risk_observation


def test_observation_exposes_drawdown_without_threshold_or_action():
    ledger = simulate_fixed_risk_cash_ledger(
        (1.0, -1.0, -0.5, 2.0), starting_balance_eur=1000.0, fixed_risk_eur=50.0
    )
    report = build_shadow_risk_observation(ledger)
    assert report.ledger_sha256 == ledger.ledger_sha256
    assert report.max_drawdown_eur == ledger.max_drawdown_eur
    assert report.max_drawdown_pct_of_peak == ledger.max_drawdown_pct_of_peak
    assert report.descriptive_only is True
    assert report.threshold_defined is False
    assert report.automatic_halt is False
    assert report.automatic_promotion is False
    assert report.execution_capability == "NONE"
    assert report.order_execution_enabled is False


def test_capital_halt_is_observed_but_not_acted_on():
    ledger = simulate_fixed_risk_cash_ledger(
        (-2.0, 1.0), starting_balance_eur=100.0, fixed_risk_eur=50.0
    )
    report = build_shadow_risk_observation(ledger)
    assert report.capital_halt_observed is True
    assert report.automatic_halt is False


def test_observation_is_deterministic():
    ledger = simulate_fixed_risk_cash_ledger(
        (0.5, -0.25), starting_balance_eur=1000.0, fixed_risk_eur=25.0
    )
    assert build_shadow_risk_observation(ledger) == build_shadow_risk_observation(ledger)


@pytest.mark.parametrize(
    "unsafe",
    [
        {"mode": "BROKER"},
    ],
)
def test_noncanonical_mutation_does_not_create_broker_capability(unsafe):
    ledger = simulate_fixed_risk_cash_ledger(
        (1.0,), starting_balance_eur=1000.0, fixed_risk_eur=25.0
    )
    mutated = replace(ledger, **unsafe)
    report = build_shadow_risk_observation(mutated)
    assert report.execution_capability == "NONE"
    assert report.order_execution_enabled is False
