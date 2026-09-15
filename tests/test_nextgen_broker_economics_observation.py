"""Synthetic adapter conformance only; these tests are not broker evidence."""
from copy import deepcopy
from dataclasses import asdict, replace
from datetime import timedelta
import json

import pytest

from daxlab.domain.market import InstrumentId
from daxlab.runtime.mt5_windows_bundle import parse_windows_mt5_bundle
from daxlab.runtime.nextgen_broker_economics import (
    bind_verified_broker_economics_to_risk_inputs,
    bind_verified_windows_broker_economics_to_risk_inputs,
)
from test_mt5_windows_bundle import _bundle, _seal
from test_nextgen_broker_economics import _symbol


def source():
    payload = _bundle(trade_mode="FULL", demo_context=True)
    payload.pop("sha256")
    payload["host_probe"]["symbols"] = [asdict(_symbol())]
    payload["host_probe"]["broker_timezone"] = "UTC"
    payload["closed_m5_feed"].update(
        broker_timezone="UTC", timestamp_interpretation="EXPLICIT_BROKER_WALL_CLOCK"
    )
    return _seal(payload)


def arguments():
    payload = source()
    bundle = parse_windows_mt5_bundle(payload)
    return dict(
        canonical_instrument_id=InstrumentId("DAX40.CFD"),
        bundle_payload=payload,
        expected_bundle_fingerprint=bundle.fingerprint,
        expected_account_context=bundle.demo_account_context,
        verification_record_fingerprint="e" * 64,  # fixture, no real review
        evaluated_at=bundle.host.observed_at,
        max_age_seconds=30,
    )


def test_exact_source_conversion_preserves_canonical_binding_and_restart():
    args = arguments()
    result = bind_verified_windows_broker_economics_to_risk_inputs(**args)
    assert result.risk_binding == bind_verified_broker_economics_to_risk_inputs(
        canonical_instrument_id=args["canonical_instrument_id"],
        symbol=_symbol(), broker_economics_verified=True,
    )
    args["bundle_payload"] = json.loads(json.dumps(args["bundle_payload"]))
    args["evaluated_at"] += timedelta(seconds=1)
    assert bind_verified_windows_broker_economics_to_risk_inputs(**args) == result
    assert result.fingerprint == bind_verified_windows_broker_economics_to_risk_inputs(
        **args
    ).fingerprint
    assert result.to_dict()["execution_capability"] == "NONE"
    assert result.order_execution_enabled is False
    assert result.observed_at == parse_windows_mt5_bundle(source()).host.observed_at


@pytest.mark.parametrize("field", ["expected_bundle_fingerprint", "verification_record_fingerprint"])
def test_missing_or_invalid_source_review_fingerprint_rejects(field):
    args = arguments()
    args[field] = ""
    with pytest.raises(ValueError):
        bind_verified_windows_broker_economics_to_risk_inputs(**args)


def test_rehashed_source_cross_wiring_rejects():
    args = arguments()
    payload = deepcopy(args["bundle_payload"])
    payload.pop("sha256")
    payload["host_probe"]["symbols"][0]["tick_value_loss"] = 2.0
    args["bundle_payload"] = _seal(payload)
    with pytest.raises(ValueError, match="source bundle cross-wiring"):
        bind_verified_windows_broker_economics_to_risk_inputs(**args)


@pytest.mark.parametrize("change", ["account", "real", "timezone", "host_time", "infinite", "incomplete"])
def test_rehashed_semantic_source_mutations_reject(change):
    args = arguments()
    payload = args["bundle_payload"]
    payload.pop("sha256")
    host = payload["host_probe"]
    if change == "account":
        host["demo_account_context"]["account_fingerprint"] = "f" * 64
    elif change == "real":
        host["demo_account_context"]["account_mode"] = "REAL"
    elif change == "timezone":
        host["broker_timezone"] = "Europe/Berlin"
    elif change == "host_time":
        host["observed_at"] = (args["evaluated_at"] - timedelta(seconds=1)).isoformat()
    elif change == "infinite":
        host["symbols"][0]["contract_size"] = float("inf")
    else:
        host["symbols"][0]["tick_size"] = None
    args["bundle_payload"] = _seal(payload)
    args["expected_bundle_fingerprint"] = args["bundle_payload"]["sha256"]
    with pytest.raises(ValueError):
        bind_verified_windows_broker_economics_to_risk_inputs(**args)


@pytest.mark.parametrize("delta", [-1, 31, 601])
def test_observation_time_future_or_stale_rejects(delta):
    args = arguments()
    args["evaluated_at"] += timedelta(seconds=delta)
    with pytest.raises(ValueError):
        bind_verified_windows_broker_economics_to_risk_inputs(**args)


@pytest.mark.parametrize("limit", [float("nan"), float("inf"), -1, True])
def test_invalid_freshness_limits_reject(limit):
    args = arguments()
    args["max_age_seconds"] = limit
    with pytest.raises(ValueError):
        bind_verified_windows_broker_economics_to_risk_inputs(**args)


def test_non_demo_expected_context_and_missing_context_reject():
    args = arguments()
    payload = args["bundle_payload"]
    payload.pop("sha256")
    del payload["host_probe"]["demo_account_context"]
    args["bundle_payload"] = _seal(payload)
    args["expected_bundle_fingerprint"] = args["bundle_payload"]["sha256"]
    with pytest.raises(ValueError, match="DEMO account context"):
        bind_verified_windows_broker_economics_to_risk_inputs(**args)


def test_observation_provenance_and_safety_are_bound():
    result = bind_verified_windows_broker_economics_to_risk_inputs(**arguments())
    assert replace(result, verification_record_fingerprint="f" * 64).fingerprint != result.fingerprint
    with pytest.raises(ValueError, match="cannot authorize"):
        replace(result, execution_capability="PAPER")


def test_adapter_does_not_promote_readiness():
    from daxlab.runtime.readiness import ReadinessSnapshot
    bind_verified_windows_broker_economics_to_risk_inputs(**arguments())
    snapshot = ReadinessSnapshot(False, False, False, False, False, False, False)
    assert snapshot.broker_economics_verified is False
    assert snapshot.paper_user_authorized is False
