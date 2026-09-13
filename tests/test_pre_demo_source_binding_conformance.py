"""Composition fixtures are software evidence, never current broker evidence."""
from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path
import ast

import pytest

from daxlab.domain.risk import evaluate_fixed_cash_risk
from daxlab.domain.risk_policy import build_risk_request_from_policy
from daxlab.runtime.nextgen_broker_economics import bind_verified_windows_broker_economics_to_risk_inputs
from daxlab.runtime.nextgen_loss_exposure_provenance import (
    assert_loss_exposure_provenance_compatible,
    loss_exposure_provenance_from_bytes,
    loss_exposure_provenance_to_bytes,
)
from daxlab.runtime.readiness import ReadinessSnapshot, RunKind, evaluate_run_readiness
import test_nextgen_execution_protection_binding as protection
from test_nextgen_broker_economics_observation import arguments
from test_nextgen_loss_exposure_provenance import evidence
from test_mt5_windows_bundle import _seal


def economics():
    args = arguments()
    payload = args["bundle_payload"]
    payload.pop("sha256")
    old_time = datetime.fromisoformat(payload["host_probe"]["observed_at"])
    delta = protection.EVALUATED_AT - old_time
    for field in ("host_probe", "closed_m5_feed"):
        payload[field]["observed_at"] = protection.EVALUATED_AT.isoformat()
    for bar in payload["closed_m5_feed"]["bars"]:
        bar["open_time"] = (datetime.fromisoformat(bar["open_time"]) + delta).isoformat()
    # Match the existing valid Risk V1 fixture's economics exactly.
    payload["host_probe"]["symbols"][0]["volume_max"] = 10.0
    args["bundle_payload"] = _seal(payload)
    args["expected_bundle_fingerprint"] = args["bundle_payload"]["sha256"]
    args["evaluated_at"] = protection.EVALUATED_AT
    return bind_verified_windows_broker_economics_to_risk_inputs(**args)


def source_loss():
    policy, observation, admission = protection._loss_chain()
    checkpoint = protection._checkpoint(policy, observation)
    _, _, template = evidence()
    day = protection.EVALUATED_AT.replace(hour=0, minute=0)
    provenance = replace(
        template, checkpoint=checkpoint,
        daily_period_start=day, daily_period_end=day + timedelta(days=1),
        weekly_period_start=day - timedelta(days=5), weekly_period_end=day + timedelta(days=2),
    )
    restored = loss_exposure_provenance_from_bytes(loss_exposure_provenance_to_bytes(provenance))
    assert_loss_exposure_provenance_compatible(
        restored, checkpoint=checkpoint, policy=policy,
        account_context=restored.account_context,
        expected_source_fingerprint=restored.source_fingerprint,
        evaluated_at=protection.EVALUATED_AT, max_age_seconds=60,
    )
    return policy, observation, admission, restored


def test_reviewed_source_bindings_preserve_existing_risk_and_protection_fingerprints():
    binding = economics()
    policy, original_request, original_decision = protection._risk_chain()
    request = build_risk_request_from_policy(
        policy=policy, strategy_decision_id=original_request.strategy_decision_id,
        trade_plan=original_request.trade_plan, instrument=binding.risk_binding.risk_inputs,
    )
    decision = evaluate_fixed_cash_risk(request)
    assert request == original_request
    assert decision == original_decision
    loss_policy, observation, admission, _ = source_loss()
    verdict = protection._evaluate(
        risk=(policy, request, decision), loss=(loss_policy, observation, admission),
    )
    assert verdict == protection._evaluate()
    assert verdict.fingerprint == protection._evaluate().fingerprint
    assert verdict.allow_evidence
    assert verdict.execution_capability == "NONE"
    assert verdict.order_execution_enabled is False
    snapshot = ReadinessSnapshot(False, False, False, False, False, False, False)
    readiness = evaluate_run_readiness(RunKind.PAPER, snapshot)
    assert not readiness.allowed
    assert "PAPER_USER_AUTHORIZATION_REQUIRED" in readiness.blockers
    assert "BROKER_ORDER_LIFECYCLE_UNVERIFIED" in readiness.blockers
    assert "BROKER_ECONOMICS_UNVERIFIED" in readiness.blockers


def test_source_provenance_cannot_override_loss_limit():
    policy, observation, admission, _ = source_loss()
    # Explicit fixture limit reached, not a promoted product policy.
    verdict = protection._evaluate(loss=protection._loss_chain(open_positions=1))
    assert admission.allowed
    assert not verdict.allow_evidence
    assert policy.currency == observation.currency


def test_stale_provenance_aborts_composition_before_protection():
    policy, _, _, provenance = source_loss()
    with pytest.raises(ValueError, match="stale"):
        assert_loss_exposure_provenance_compatible(
            provenance, checkpoint=provenance.checkpoint, policy=policy,
            account_context=provenance.account_context,
            expected_source_fingerprint=provenance.source_fingerprint,
            evaluated_at=protection.EVALUATED_AT + timedelta(minutes=2), max_age_seconds=60,
        )


def test_new_provenance_adapters_have_no_submission_or_storage_calls():
    root = Path(__file__).resolve().parents[1]
    for path in ["src/daxlab/runtime/nextgen_broker_economics.py", "src/daxlab/runtime/nextgen_loss_exposure_provenance.py"]:
        tree = ast.parse((root / path).read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id if isinstance(node.func, ast.Name) else ""
                assert name not in {"save", "order_send", "order_check", "place_order", "submit_order", "cancel_order", "modify_order"}
