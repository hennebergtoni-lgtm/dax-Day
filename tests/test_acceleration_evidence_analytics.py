from __future__ import annotations

import pytest

from daxlab.research.conformance import (
    EVIDENCE_IDENTITY_DIMENSIONS, compare_full_evidence_identity,
)
from daxlab.research.failure_analysis import observed_execution_costs


def identity():
    return dict.fromkeys(EVIDENCE_IDENTITY_DIMENSIONS, "a" * 64)


def costs():
    return {"side": "BUY", "reference_price": "100.0", "arrival_bid": "101.0",
            "arrival_ask": "102.0", "arrival_at": "2026-09-14T08:00:00Z",
            "request_at": "2026-09-14T08:00:00.100Z",
            "response_at": "2026-09-14T08:00:00.300Z", "requested_quantity": "2",
            "tick_size": "0.5", "source_sha256": "a" * 64,
            "broker_identity_sha256": "b" * 64, "fill_price": "103.0",
            "fill_at": "2026-09-14T08:00:00.200Z", "native_quantity": "2",
            "explicit_cost_cash": "1.00", "cash_per_point_per_unit": "5"}


def test_all_seven_dimensions_require_complete_full_spec_identity():
    result = compare_full_evidence_identity(identity(), identity())
    assert result["status"] == "MATCH"
    assert set(result["dimensions"]) == {"DATA", "CLOCK", "SIGNAL", "EXECUTION", "COST", "BROKER", "LIFECYCLE"}
    assert set(result["dimensions"].values()) == {"MATCH"}
    assert result["execution_capability"] == "NONE"


@pytest.mark.parametrize("field", list(EVIDENCE_IDENTITY_DIMENSIONS))
def test_each_drift_is_reported_in_its_actual_dimension(field):
    observed = identity()
    observed[field] = "b" * 64
    result = compare_full_evidence_identity(identity(), observed)
    assert result["dimensions"][EVIDENCE_IDENTITY_DIMENSIONS[field]] == "MISMATCH"
    assert result["field_states"][field] == "MISMATCH"
    assert result["status"] == "MISMATCH"


@pytest.mark.parametrize("field", list(EVIDENCE_IDENTITY_DIMENSIONS))
def test_missing_components_are_unknown_not_match(field):
    observed = identity()
    del observed[field]
    assert compare_full_evidence_identity(identity(), observed)["status"] == "UNKNOWN"


@pytest.mark.parametrize("value", ["short", "F" * 64, False, {}, []])
def test_identity_cannot_smuggle_invalid_nested_pins(value):
    observed = identity()
    observed["broker_context"] = value
    with pytest.raises(ValueError):
        compare_full_evidence_identity(identity(), observed)


def test_identity_unknown_fields_reject_and_hash_changes_with_semantics():
    with pytest.raises(ValueError):
        compare_full_evidence_identity({"password": "secret"}, identity())
    observed = identity()
    before = compare_full_evidence_identity(identity(), observed)
    observed["cost"] = "b" * 64
    after = compare_full_evidence_identity(identity(), observed)
    assert before["identity_sha256"] != after["identity_sha256"]
    assert before["source_pins"]["observed"]["cost"] == "a" * 64


def test_tca_hand_computed_buy_native_quantity_and_no_internal_latency_claim():
    result = observed_execution_costs(costs())
    assert result["metrics"] == {"arrival_spread_points": "1.0",
        "reference_shortfall_points": "3.0", "arrival_slippage_points": "1.0",
        "arrival_slippage_cash": "10.0"}
    assert result["client_request_response_ms"] == pytest.approx(200)
    assert result["arrival_to_request_ms"] == pytest.approx(100)
    assert result["explicit_cost_cash"] == "1.00"
    assert all(result["price_grid_observations"].values())
    assert result["broker_internal_latency"] == "UNKNOWN"
    assert result["cumulative_quantity"] == "NOT_PROVEN"
    assert result["final_outcome"] == "UNRESOLVED"


def test_sell_sign_and_price_improvement_are_not_clamped():
    evidence = {**costs(), "side": "SELL", "fill_price": "102.5"}
    result = observed_execution_costs(evidence)
    assert result["metrics"]["reference_shortfall_points"] == "-2.5"
    assert result["metrics"]["arrival_slippage_points"] == "-1.5"
    assert result["metrics"]["arrival_slippage_cash"] == "-15.0"


def test_fill_absence_is_unresolved_and_missing_economics_is_not_zero():
    evidence = costs()
    for field in ("fill_price", "fill_at", "native_quantity", "cash_per_point_per_unit", "explicit_cost_cash"):
        del evidence[field]
    result = observed_execution_costs(evidence)
    assert result["metrics"]["arrival_slippage_cash"] is None
    assert result["explicit_cost_cash"] is None
    assert result["single_fill_vs_requested"] == "UNKNOWN"
    assert result["final_outcome"] == "UNRESOLVED"


def test_below_requested_is_single_fill_observation_not_final_partial_status():
    result = observed_execution_costs({**costs(), "native_quantity": "0.25"})
    assert result["single_fill_vs_requested"] == "BELOW_REQUEST"
    assert result["native_quantity"] == "0.25"
    assert result["cumulative_quantity"] == "NOT_PROVEN"
    assert result["final_outcome"] == "UNRESOLVED"


def test_native_grid_uses_tick_size_not_decimal_digits():
    result = observed_execution_costs({**costs(), "fill_price": "103.25", "tick_size": "0.5"})
    assert result["price_grid_observations"]["fill_price"] is False
    assert result["metrics"]["arrival_slippage_points"] == "1.25"


@pytest.mark.parametrize("change", [
    {"reference_price": "NaN"}, {"native_quantity": True}, {"native_quantity": "0"},
    {"tick_size": "0"}, {"arrival_bid": "103"}, {"arrival_ask": "0"},
    {"explicit_cost_cash": "-1"}, {"cash_per_point_per_unit": "1e3"},
    {"source_sha256": "missing"}, {"broker_identity_sha256": None},
    {"request_at": "2026-09-14T08:00:00"}, {"fill_at": None},
    {"fill_at": "2026-09-14T07:59:59Z"},
    {"response_at": "2026-09-14T07:59:59Z"},
    {"arrival_at": "2026-09-14T08:00:01Z"},
])
def test_tca_invalid_precision_clock_or_incomplete_fill_rejects(change):
    with pytest.raises(ValueError):
        observed_execution_costs({**costs(), **change})


def test_tca_closed_schema_prevents_nested_credential_passthrough():
    with pytest.raises(ValueError) as error:
        observed_execution_costs({**costs(), "credentials": {"password": "SECRET"}})
    assert "SECRET" not in str(error.value)


def test_decimal_product_preserves_more_than_default_28_digits():
    evidence = {**costs(), "native_quantity": "123456789012345678901234567890",
                "cash_per_point_per_unit": "10000000000"}
    result = observed_execution_costs(evidence)
    assert result["metrics"]["arrival_slippage_cash"] == "1234567890123456789012345678900000000000.0"
    assert result["single_fill_vs_requested"] == "ABOVE_REQUEST"


def test_equivalent_offset_clock_normalizes_to_utc():
    result = observed_execution_costs({**costs(), "fill_at": "2026-09-14T10:00:00.200+02:00"})
    assert result["fill_observed_at"] == "2026-09-14T08:00:00.200000+00:00"
