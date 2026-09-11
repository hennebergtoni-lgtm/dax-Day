from __future__ import annotations

import copy

import pytest

from daxlab.runtime.candidate_operator_telemetry import validate_candidate_operator_snapshot


def _payload() -> dict[str, object]:
    return {
        "schema_version": "DAX_BOT_OPERATOR_SNAPSHOT_V3",
        "generated_at": "2026-09-11T17:00:00+00:00",
        "core_version": "DAX-BOT-1.0-alpha",
        "candidate_id": "CAND-001",
        "config_fingerprint": "a" * 64,
        "strategy": {"regime": "OPEN", "structure": "OR15", "setup": "BREAKOUT"},
        "signal": {"direction": "LONG", "reason": "CONFIRMED_BREAKOUT_CLOSE"},
        "admission": {"status": "ALLOWED"},
        "decision": {
            "action": "TRADE",
            "decision_id": "b" * 64,
            "blockers": [],
            "risk_result": "ALLOWED",
        },
        "trade_plan": {
            "entry": 18600.0,
            "stop": 18580.0,
            "target": 18630.0,
            "reward_risk": 1.5,
        },
        "runtime": {
            "last_bar_id": "c" * 64,
            "last_bar_close_time": "2026-09-11T16:55:00+00:00",
            "freshness_seconds": 300.0,
            "health_state": "GREEN",
            "health_source": "MT5_SHADOW",
            "events": [],
            "recovery_state": "NONE",
            "reconciliation_state": "CLEAN",
        },
        "virtual_position": {
            "lifecycle_id": None,
            "origin_decision_id": None,
            "status": None,
            "side": None,
            "filled_at": None,
            "filled_price": None,
            "closed_at": None,
            "exit_price": None,
            "exit_reason": None,
        },
        "outcome": {
            "outcome_id": None,
            "gross_r": None,
            "cost_r": None,
            "net_r": None,
        },
        "safety": {
            "execution_capability": "NONE",
            "order_execution_enabled": False,
        },
        "snapshot_fingerprint": "d" * 64,
    }


def test_valid_candidate_operator_snapshot_is_accepted() -> None:
    validate_candidate_operator_snapshot(_payload())


def test_candidate_operator_snapshot_rejects_execution_capability() -> None:
    payload = copy.deepcopy(_payload())
    payload["safety"]["execution_capability"] = "BROKER"  # type: ignore[index]
    with pytest.raises(ValueError, match="execution capability"):
        validate_candidate_operator_snapshot(payload)


def test_candidate_operator_snapshot_rejects_incomplete_runtime_bar_context() -> None:
    payload = copy.deepcopy(_payload())
    payload["runtime"]["last_bar_close_time"] = None  # type: ignore[index]
    with pytest.raises(ValueError, match="last_bar_close_time"):
        validate_candidate_operator_snapshot(payload)


def test_candidate_operator_snapshot_rejects_credentials_anywhere() -> None:
    payload = copy.deepcopy(_payload())
    payload["runtime"]["token"] = "secret"  # type: ignore[index]
    with pytest.raises(ValueError, match="forbidden Candidate telemetry field"):
        validate_candidate_operator_snapshot(payload)
