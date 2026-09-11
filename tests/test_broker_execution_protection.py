from __future__ import annotations

from pathlib import Path

import pytest

from daxlab.runtime.broker_execution_protection import (
    ExecutionProtectionStatus,
    evaluate_execution_protection,
)
from daxlab.runtime.broker_reconciliation import reconcile_broker_order


CLIENT_ID = "a" * 64
SIZING_FP = "b" * 64
RISK_FP = "c" * 64


def _safe(**changes):
    values = {
        "client_order_id": CLIENT_ID,
        "host_health_green": True,
        "broker_account_trade_allowed": True,
        "feed_age_seconds": 1.0,
        "max_feed_age_seconds": 10.0,
        "observed_spread_points": 0.2,
        "max_spread_points": 0.5,
        "reconciliation_inventory_complete": True,
        "reconciliations": (),
        "duplicate_client_order_id": False,
        "sizing_allowed": True,
        "sizing_evidence_fingerprint": SIZING_FP,
        "loss_cap_allowed": True,
        "risk_policy_fingerprint": RISK_FP,
        "session_admission_allowed": True,
    }
    values.update(changes)
    return evaluate_execution_protection(**values)


def test_complete_empty_inventory_can_allow_evidence_but_never_execution() -> None:
    verdict = _safe()
    assert verdict.status is ExecutionProtectionStatus.ALLOW_EVIDENCE
    assert verdict.allow_evidence is True
    assert verdict.blockers == ()
    assert verdict.reconciliation_fingerprints == ()
    assert verdict.execution_capability == "NONE"
    assert verdict.order_execution_enabled is False


@pytest.mark.parametrize(
    ("change", "blocker"),
    [
        ({"host_health_green": False}, "HOST_HEALTH_NOT_GREEN"),
        (
            {"broker_account_trade_allowed": False},
            "BROKER_ACCOUNT_TRADING_NOT_ALLOWED",
        ),
        ({"feed_age_seconds": 11.0}, "STALE_FEED"),
        ({"observed_spread_points": None}, "SPREAD_UNAVAILABLE"),
        ({"observed_spread_points": 0.51}, "EXTREME_SPREAD"),
        (
            {"reconciliation_inventory_complete": False},
            "RECONCILIATION_INVENTORY_INCOMPLETE",
        ),
        ({"duplicate_client_order_id": True}, "DUPLICATE_CLIENT_ORDER_ID"),
        ({"sizing_evidence_fingerprint": None}, "SIZING_EVIDENCE_MISSING"),
        ({"sizing_allowed": False}, "SIZING_BLOCKED"),
        ({"risk_policy_fingerprint": None}, "RISK_POLICY_EVIDENCE_MISSING"),
        ({"loss_cap_allowed": False}, "LOSS_CAP_BLOCKED"),
        ({"session_admission_allowed": False}, "SESSION_ADMISSION_BLOCKED"),
    ],
)
def test_each_hard_protection_input_fails_closed(change, blocker) -> None:
    verdict = _safe(**change)
    assert verdict.status is ExecutionProtectionStatus.BLOCKED
    assert verdict.allow_evidence is False
    assert blocker in verdict.blockers
    assert verdict.execution_capability == "NONE"
    assert verdict.order_execution_enabled is False


def test_blocked_reconciliation_forces_protection_block() -> None:
    blocked_reconciliation = reconcile_broker_order(local=None, venue=None)
    verdict = _safe(reconciliations=(blocked_reconciliation,))
    assert "BROKER_RECONCILIATION_BLOCKED" in verdict.blockers
    assert verdict.reconciliation_fingerprints == (blocked_reconciliation.fingerprint,)


def test_spread_exactly_at_limit_is_not_extreme() -> None:
    verdict = _safe(observed_spread_points=0.5, max_spread_points=0.5)
    assert verdict.allow_evidence is True


def test_protection_fingerprint_is_deterministic() -> None:
    assert _safe().fingerprint == _safe().fingerprint


def test_invalid_sha_evidence_is_rejected() -> None:
    with pytest.raises(ValueError, match="sizing_evidence_fingerprint"):
        _safe(sizing_evidence_fingerprint="not-a-sha")


def test_protection_owner_contains_no_order_submission_api() -> None:
    root = Path(__file__).resolve().parents[1]
    source = (
        root / "src/daxlab/runtime/broker_execution_protection.py"
    ).read_text(encoding="utf-8")
    assert "order_send(" not in source
    assert "import MetaTrader5" not in source
