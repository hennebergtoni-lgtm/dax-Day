from __future__ import annotations

from datetime import datetime, timezone

import pytest

from daxlab.runtime.candidate_operator_query import build_candidate_operator_current


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


def test_current_read_model_recomputes_bar_age_at_query_time() -> None:
    current = build_candidate_operator_current(
        _payload(),
        queried_at=datetime(2026, 9, 11, 17, 5, tzinfo=timezone.utc),
    )
    assert current.current_bar_age_seconds == 600.0
    assert current.payload["runtime"]["freshness_seconds"] == 300.0
    assert current.execution_capability == "NONE"
    assert current.order_execution_enabled is False


def test_current_read_model_rejects_future_bar() -> None:
    with pytest.raises(ValueError, match="future"):
        build_candidate_operator_current(
            _payload(),
            queried_at=datetime(2026, 9, 11, 16, 54, tzinfo=timezone.utc),
        )


def test_current_read_model_requires_timezone_aware_query_time() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        build_candidate_operator_current(
            _payload(),
            queried_at=datetime(2026, 9, 11, 17, 5),
        )
