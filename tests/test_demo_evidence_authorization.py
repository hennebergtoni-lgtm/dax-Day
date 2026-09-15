from datetime import datetime, timedelta, timezone

import pytest

from daxlab.runtime.demo_evidence_authorization import (
    DEMO_EVIDENCE_AUTHORIZATION_SCHEMA,
    DemoAccountMode,
    DemoEvidenceAction,
    DemoEvidenceAuthorization,
    DemoEvidenceAuthorizationStatus,
    DemoEvidenceObservedContext,
    evaluate_demo_evidence_authorization,
)
from daxlab.runtime.prospective_gate import ProspectiveAuthorization


NOW = datetime(2026, 9, 14, 8, 0, tzinfo=timezone.utc)


def _authorization(**overrides):
    values = {
        "schema_version": DEMO_EVIDENCE_AUTHORIZATION_SCHEMA,
        "authorization_id": "monday-demo-evidence-001",
        "account_id": "demo-account-001",
        "server": "Broker-Demo",
        "symbol": "DE40",
        "valid_from": NOW - timedelta(minutes=5),
        "expires_at": NOW + timedelta(minutes=30),
        "allowed_actions": (
            DemoEvidenceAction.SUBMIT_EVIDENCE_ORDER,
            DemoEvidenceAction.QUERY_EVIDENCE_ORDER,
            DemoEvidenceAction.CANCEL_EVIDENCE_ORDER,
        ),
        "max_submissions": 1,
    }
    values.update(overrides)
    return DemoEvidenceAuthorization(**values)


def _observed(**overrides):
    values = {
        "account_id": "demo-account-001",
        "server": "Broker-Demo",
        "symbol": "DE40",
        "account_mode": DemoAccountMode.DEMO,
        "trade_allowed": True,
    }
    values.update(overrides)
    return DemoEvidenceObservedContext(**values)


def _evaluate(*, authorization=None, observed=None, action=None, at=None, attempts=0):
    return evaluate_demo_evidence_authorization(
        authorization=_authorization() if authorization is None else authorization,
        observed=_observed() if observed is None else observed,
        requested_action=action or DemoEvidenceAction.SUBMIT_EVIDENCE_ORDER,
        evaluated_at=at or NOW,
        submissions_already_attempted=attempts,
    )


def test_exact_demo_scope_can_be_valid_but_never_grants_execution():
    verdict = _evaluate()
    assert verdict.status is DemoEvidenceAuthorizationStatus.SCOPE_VALID
    assert verdict.scope_valid is True
    assert verdict.blockers == ()
    assert verdict.execution_capability == "NONE"
    assert verdict.order_execution_enabled is False


@pytest.mark.parametrize(
    ("mode", "blocker"),
    [
        (DemoAccountMode.REAL, "ACCOUNT_MODE_REAL_BLOCKED"),
        (DemoAccountMode.CONTEST, "ACCOUNT_MODE_CONTEST_BLOCKED"),
        (DemoAccountMode.UNKNOWN, "ACCOUNT_MODE_UNKNOWN_BLOCKED"),
    ],
)
def test_non_demo_account_modes_fail_closed_even_when_trade_allowed(mode, blocker):
    verdict = _evaluate(observed=_observed(account_mode=mode, trade_allowed=True))
    assert verdict.scope_valid is False
    assert blocker in verdict.blockers


def test_trade_allowed_true_is_not_demo_proof_and_false_blocks_even_demo():
    real = _evaluate(observed=_observed(account_mode=DemoAccountMode.REAL, trade_allowed=True))
    assert "ACCOUNT_MODE_REAL_BLOCKED" in real.blockers

    disabled = _evaluate(observed=_observed(account_mode=DemoAccountMode.DEMO, trade_allowed=False))
    assert "ACCOUNT_TRADE_NOT_ALLOWED" in disabled.blockers


@pytest.mark.parametrize(
    ("overrides", "blocker"),
    [
        ({"account_id": "other"}, "ACCOUNT_ID_MISMATCH"),
        ({"server": "Other-Demo"}, "SERVER_MISMATCH"),
        ({"symbol": "GER40"}, "SYMBOL_MISMATCH"),
    ],
)
def test_account_server_symbol_cross_wiring_is_blocked(overrides, blocker):
    verdict = _evaluate(observed=_observed(**overrides))
    assert verdict.scope_valid is False
    assert blocker in verdict.blockers


def test_not_yet_valid_and_expired_authorization_are_blocked():
    early = _evaluate(at=_authorization().valid_from - timedelta(seconds=1))
    assert "AUTHORIZATION_NOT_YET_VALID" in early.blockers

    expired = _evaluate(at=_authorization().expires_at)
    assert "AUTHORIZATION_EXPIRED" in expired.blockers


def test_action_scope_and_submission_limit_are_fail_closed():
    authorization = _authorization(
        allowed_actions=(DemoEvidenceAction.QUERY_EVIDENCE_ORDER,),
    )
    out_of_scope = _evaluate(authorization=authorization)
    assert "ACTION_OUT_OF_SCOPE" in out_of_scope.blockers

    exhausted = _evaluate(attempts=1)
    assert "SUBMISSION_LIMIT_REACHED" in exhausted.blockers


def test_final_paper_authorization_type_cannot_be_reused_as_demo_evidence_grant():
    paper_authorization = ProspectiveAuthorization(
        gate_id="STEP_91_USER_AUTHORIZATION",
        shadow_authorized=True,
        paper_authorized=True,
        live_authorized=False,
    )
    verdict = _evaluate(authorization=paper_authorization)
    assert verdict.scope_valid is False
    assert verdict.blockers == ("DEMO_EVIDENCE_AUTHORIZATION_TYPE_INVALID",)


def test_fingerprint_changes_when_scope_is_rehashed_with_different_binding():
    original = _authorization()
    cross_wired = _authorization(server="Other-Demo")
    assert original.fingerprint != cross_wired.fingerprint


def test_authorization_cannot_claim_execution_capability():
    with pytest.raises(ValueError, match="cannot grant execution"):
        _authorization(execution_capability="PAPER")

    with pytest.raises(ValueError, match="cannot grant execution"):
        _authorization(order_execution_enabled=True)


def test_authorization_requires_time_bounded_nonempty_unique_scope():
    with pytest.raises(ValueError, match="expires_at must be after valid_from"):
        _authorization(expires_at=NOW - timedelta(minutes=10))

    with pytest.raises(ValueError, match="allowed_actions must not be empty"):
        _authorization(allowed_actions=())

    with pytest.raises(ValueError, match="must not contain duplicates"):
        _authorization(
            allowed_actions=(
                DemoEvidenceAction.SUBMIT_EVIDENCE_ORDER,
                DemoEvidenceAction.SUBMIT_EVIDENCE_ORDER,
            )
        )

    with pytest.raises(ValueError, match="max_submissions"):
        _authorization(max_submissions=0)


def test_evaluation_requires_aware_time_and_nonnegative_attempt_count():
    with pytest.raises(ValueError, match="evaluated_at must be timezone-aware"):
        _evaluate(at=datetime(2026, 9, 14, 8, 0))

    with pytest.raises(ValueError, match="submissions_already_attempted"):
        _evaluate(attempts=-1)


def test_scope_rejects_untyped_action_and_observed_account_mode():
    with pytest.raises(ValueError, match="DemoEvidenceAction"):
        _authorization(allowed_actions=("SUBMIT_EVIDENCE_ORDER",))

    with pytest.raises(ValueError, match="account_mode must be DemoAccountMode"):
        _observed(account_mode="DEMO")

    with pytest.raises(ValueError, match="trade_allowed must be bool"):
        _observed(trade_allowed=1)
