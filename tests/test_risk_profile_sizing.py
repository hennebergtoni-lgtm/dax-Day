from __future__ import annotations

import pytest

from daxlab.research.risk_profile_sizing import (
    RISK_PROFILE_SIZING_RESEARCH_VERSION,
    RiskProfile,
    RiskProfileBudgetSpec,
    estimate_profile_volume,
)
from daxlab.runtime.mt5_readonly import BrokerSymbol


def _symbol(**overrides) -> BrokerSymbol:
    values = {
        "name": "DE40",
        "digits": 2,
        "point": 0.01,
        "trade_mode": "FULL",
        "contract_size": 1.0,
        "volume_min": 0.1,
        "volume_step": 0.1,
        "volume_max": 100.0,
        "volume_limit": 0.0,
        "tick_size": 0.01,
        "tick_value": 0.01,
        "tick_value_profit": 0.01,
        "tick_value_loss": 0.01,
        "currency_profit": "EUR",
        "currency_margin": "EUR",
        "margin_initial": 0.0,
        "margin_maintenance": 0.0,
    }
    values.update(overrides)
    return BrokerSymbol(**values)


def _spec() -> RiskProfileBudgetSpec:
    return RiskProfileBudgetSpec(
        currency="EUR",
        base_cash_risk=25.0,
        boost_cash_risk=50.0,
        high_cash_risk=75.0,
        hard_cap_cash_risk=100.0,
    )


def test_profile_budget_spec_is_explicit_monotonic_and_versioned() -> None:
    spec = _spec()

    assert spec.policy_version == RISK_PROFILE_SIZING_RESEARCH_VERSION
    assert spec.cash_risk_for(RiskProfile.BASE) == 25.0
    assert spec.cash_risk_for(RiskProfile.BOOST) == 50.0
    assert spec.cash_risk_for(RiskProfile.HIGH) == 75.0
    assert len(spec.fingerprint) == 64


def test_non_monotonic_or_over_cap_profiles_are_rejected() -> None:
    with pytest.raises(ValueError, match="BASE <= BOOST <= HIGH <= hard cap"):
        RiskProfileBudgetSpec(
            currency="EUR",
            base_cash_risk=25.0,
            boost_cash_risk=20.0,
            high_cash_risk=75.0,
            hard_cap_cash_risk=100.0,
        )
    with pytest.raises(ValueError, match="BASE <= BOOST <= HIGH <= hard cap"):
        RiskProfileBudgetSpec(
            currency="EUR",
            base_cash_risk=25.0,
            boost_cash_risk=50.0,
            high_cash_risk=125.0,
            hard_cap_cash_risk=100.0,
        )


def test_profile_bridge_uses_explicit_cash_at_stop_budget_only() -> None:
    spec = _spec()
    result = estimate_profile_volume(
        spec=spec,
        profile=RiskProfile.BOOST,
        symbol=_symbol(),
        stop_distance_price=10.0,
    )

    assert result.profile is RiskProfile.BOOST
    assert result.profile_spec_fingerprint == spec.fingerprint
    assert result.risk_currency == "EUR"
    assert result.requested_cash_risk == 50.0
    assert result.hard_cap_cash_risk == 100.0
    assert result.estimate.risk_budget_cash == 50.0
    assert result.estimate.volume == pytest.approx(5.0)
    assert result.estimate.projected_stop_loss_cash == pytest.approx(50.0)
    assert len(result.fingerprint) == 64
    assert result.execution_capability == "NONE"
    assert result.order_execution_enabled is False


def test_high_profile_still_cannot_exceed_hard_cap() -> None:
    spec = RiskProfileBudgetSpec(
        currency="EUR",
        base_cash_risk=10.0,
        boost_cash_risk=20.0,
        high_cash_risk=30.0,
        hard_cap_cash_risk=30.0,
    )
    result = estimate_profile_volume(
        spec=spec,
        profile=RiskProfile.HIGH,
        symbol=_symbol(),
        stop_distance_price=10.0,
    )

    assert result.requested_cash_risk == 30.0
    assert result.estimate.projected_stop_loss_cash <= 30.0
    assert result.order_execution_enabled is False


def test_currency_mismatch_propagates_as_unavailable_estimate() -> None:
    spec = RiskProfileBudgetSpec(
        currency="USD",
        base_cash_risk=25.0,
        boost_cash_risk=50.0,
        high_cash_risk=75.0,
        hard_cap_cash_risk=100.0,
    )
    result = estimate_profile_volume(
        spec=spec,
        profile=RiskProfile.BASE,
        symbol=_symbol(currency_profit="EUR"),
        stop_distance_price=10.0,
    )

    assert result.estimate.available is False
    assert result.estimate.blockers == ("RISK_CURRENCY_MISMATCH",)
    assert result.execution_capability == "NONE"
    assert result.order_execution_enabled is False


def test_profile_spec_does_not_accept_boolean_or_whitespace_currency() -> None:
    with pytest.raises(ValueError, match="all cash-risk values must be positive"):
        RiskProfileBudgetSpec(
            currency="EUR",
            base_cash_risk=True,
            boost_cash_risk=50.0,
            high_cash_risk=75.0,
            hard_cap_cash_risk=100.0,
        )
    with pytest.raises(ValueError, match="currency cannot contain outer whitespace"):
        RiskProfileBudgetSpec(
            currency=" EUR ",
            base_cash_risk=25.0,
            boost_cash_risk=50.0,
            high_cash_risk=75.0,
            hard_cap_cash_risk=100.0,
        )


def test_profile_and_result_fingerprints_are_deterministic_and_sensitive() -> None:
    spec = _spec()
    same_spec = _spec()
    changed_spec = RiskProfileBudgetSpec(
        currency="EUR",
        base_cash_risk=25.0,
        boost_cash_risk=55.0,
        high_cash_risk=75.0,
        hard_cap_cash_risk=100.0,
    )

    first = estimate_profile_volume(
        spec=spec,
        profile=RiskProfile.BOOST,
        symbol=_symbol(),
        stop_distance_price=10.0,
    )
    repeated = estimate_profile_volume(
        spec=same_spec,
        profile=RiskProfile.BOOST,
        symbol=_symbol(),
        stop_distance_price=10.0,
    )
    changed_profile = estimate_profile_volume(
        spec=spec,
        profile=RiskProfile.HIGH,
        symbol=_symbol(),
        stop_distance_price=10.0,
    )

    assert spec.fingerprint == same_spec.fingerprint
    assert spec.fingerprint != changed_spec.fingerprint
    assert first.fingerprint == repeated.fingerprint
    assert first.fingerprint != changed_profile.fingerprint
