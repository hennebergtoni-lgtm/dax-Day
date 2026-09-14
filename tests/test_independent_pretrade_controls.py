from __future__ import annotations

from dataclasses import replace

import pytest

from daxlab.runtime.broker_execution_protection import (
    evaluate_execution_protection, evaluate_independent_pretrade_controls,
)


def protection(**changes):
    args = dict(client_order_id="a" * 64, host_health_green=True,
                broker_account_trade_allowed=True, feed_age_seconds=1,
                max_feed_age_seconds=10, observed_spread_points=0.2,
                max_spread_points=0.5, reconciliation_inventory_complete=True,
                reconciliations=(), duplicate_client_order_id=False, sizing_allowed=True,
                sizing_evidence_fingerprint="b" * 64, loss_cap_allowed=True,
                risk_policy_fingerprint="c" * 64, session_admission_allowed=True)
    return evaluate_execution_protection(**{**args, **changes})


def policy():
    return {"account_identity_sha256": "a" * 64, "instrument_identity_sha256": "b" * 64,
            "min_quantity": "0.25", "max_quantity": "2", "quantity_increment": "0.25",
            "tick_size": "0.5", "max_notional_cash": "1000",
            "max_price_deviation_points": "1", "max_quote_age_seconds": 2, "max_attempts": 1}


def observation():
    return {"source_sha256": "c" * 64, "account_identity_sha256": "a" * 64,
            "instrument_identity_sha256": "b" * 64, "environment": "DEMO",
            "quantity": "0.5", "request_price": "100.5", "reference_price": "100",
            "cash_per_point_per_unit": "5", "quote_age_seconds": 1,
            "attempts_used": 0, "duplicate": False, "inventory_clear": True,
            "session_allowed": True, "reservation_unknown": False, "emergency_latched": False}


def evaluate(**changes):
    return evaluate_independent_pretrade_controls(policy=policy(),
                                                  observation={**observation(), **changes},
                                                  protection=protection())


def test_independent_ptc_hand_notional_and_none_false_cannot_unlock_strategy():
    result = evaluate()
    assert result["status"] == "ALLOW_EVIDENCE"
    assert result["notional_cash_proxy"] == "251.25"
    assert result["execution_capability"] == "NONE"
    assert result["order_execution_enabled"] is False
    assert result["runtime_integration"] == "BOUNDED_TRANSPORT_NOT_YET_VERIFIED"
    assert result["fingerprint"] == evaluate()["fingerprint"]


@pytest.mark.parametrize("changes,blocker", [
    ({"environment": "LIVE"}, "PTC_HARD_LIVE_OR_UNKNOWN_ENVIRONMENT_BLOCK"),
    ({"environment": None}, "PTC_HARD_LIVE_OR_UNKNOWN_ENVIRONMENT_BLOCK"),
    ({"account_identity_sha256": "d" * 64}, "PTC_ACCOUNT_VETO"),
    ({"instrument_identity_sha256": "d" * 64}, "PTC_INSTRUMENT_VETO"),
    ({"quantity": "0.1"}, "PTC_QUANTITY_BOUND_VETO"),
    ({"quantity": "3"}, "PTC_QUANTITY_BOUND_VETO"),
    ({"quantity": "0.3"}, "PTC_NATIVE_QUANTITY_GRID_VETO"),
    ({"request_price": "100.25"}, "PTC_NATIVE_PRICE_GRID_VETO"),
    ({"request_price": "101.5"}, "PTC_PRICE_COLLAR_VETO"),
    ({"cash_per_point_per_unit": "100"}, "PTC_NOTIONAL_BOUND_VETO"),
    ({"quote_age_seconds": 3}, "PTC_STALE_PRICE_VETO"),
    ({"attempts_used": 1}, "PTC_ATTEMPT_BOUND_VETO"),
    ({"duplicate": True}, "PTC_DUPLICATE_VETO"),
    ({"inventory_clear": False}, "PTC_INVENTORY_VETO"),
    ({"session_allowed": False}, "PTC_SESSION_VETO"),
    ({"reservation_unknown": True}, "PTC_UNKNOWN_RESERVATION_QUERY_REQUIRED"),
    ({"emergency_latched": True}, "PTC_EMERGENCY_AUTHORITY_LATCHED"),
])
def test_each_ptc_veto_is_independent_of_green_strategy_risk(changes, blocker):
    result = evaluate(**changes)
    assert result["status"] == "BLOCKED"
    assert blocker in result["blockers"]
    assert result["execution_capability"] == "NONE"


@pytest.mark.parametrize("field", ["duplicate", "inventory_clear", "session_allowed", "reservation_unknown", "emergency_latched"])
@pytest.mark.parametrize("value", [None, 0, 1, "true"])
def test_missing_or_truthy_nonboolean_control_cannot_open_gate(field, value):
    with pytest.raises(ValueError):
        evaluate(**{field: value})


@pytest.mark.parametrize("change", [
    {"quantity": "NaN"}, {"quantity": True}, {"quote_age_seconds": float("nan")},
    {"attempts_used": True}, {"source_sha256": "missing"},
    {"quantity": "0"}, {"request_price": "1e3"},
])
def test_invalid_native_or_unpinned_evidence_rejects(change):
    with pytest.raises(ValueError):
        evaluate(**change)


def test_existing_protection_block_cannot_be_overridden_by_ptc():
    result = evaluate_independent_pretrade_controls(
        policy=policy(), observation=observation(), protection=protection(loss_cap_allowed=False),
    )
    assert "PTC_EXISTING_PROTECTION_BLOCKED" in result["blockers"]


def test_closed_schemas_veto_unknown_credential_nesting():
    with pytest.raises(ValueError) as error:
        evaluate_independent_pretrade_controls(
            policy={**policy(), "credentials": {"password": "SECRET"}},
            observation=observation(), protection=protection(),
        )
    assert "SECRET" not in str(error.value)


def test_policy_boundaries_are_inclusive_but_attempt_limit_is_exclusive():
    result = evaluate(quantity="2", request_price="101", quote_age_seconds=2,
                      cash_per_point_per_unit="1")
    assert result["status"] == "ALLOW_EVIDENCE"
    assert evaluate(attempts_used=1)["status"] == "BLOCKED"


@pytest.mark.parametrize("field", [
    "host_health_green", "broker_account_trade_allowed", "reconciliation_inventory_complete",
    "duplicate_client_order_id", "sizing_allowed", "loss_cap_allowed", "session_admission_allowed",
])
@pytest.mark.parametrize("value", [None, 0, 1, "false"])
def test_existing_protection_rejects_nonboolean_normalized_safety_gates(field, value):
    with pytest.raises(ValueError, match="must be boolean"):
        protection(**{field: value})


@pytest.mark.parametrize("value", [None, 0, "false", True])
def test_persisted_protection_requires_literal_false_execution(value):
    with pytest.raises(ValueError, match="cannot authorize execution"):
        replace(protection(), order_execution_enabled=value)


@pytest.mark.parametrize("value", ["1", True, 10**1000])
def test_native_ptc_age_type_and_overflow_fail_closed(value):
    with pytest.raises(ValueError):
        evaluate(quote_age_seconds=value)
