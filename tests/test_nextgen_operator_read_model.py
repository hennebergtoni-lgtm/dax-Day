from __future__ import annotations

import ast
from dataclasses import replace
from datetime import datetime, timezone
import json
from pathlib import Path

import pytest

from daxlab.adapters.cand001_operator import candidate_current_to_product_operator_view
from daxlab.operator.read_model import canonical_operator_view_json
from daxlab.runtime.candidate_operator_query import build_candidate_operator_current


UTC = timezone.utc


def payload() -> dict[str, object]:
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
            "blockers": ["RISK_PROFILE_RESEARCH_ONLY"],
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
            "health_source": "MT5_SHADOW_HOST",
            "events": ["RESTART_CATCHUP"],
            "recovery_state": "RESUME_ANCHOR_RECONCILED",
            "reconciliation_state": "IN_SYNC",
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


def current_view(data: dict[str, object] | None = None):
    return build_candidate_operator_current(
        data or payload(),
        queried_at=datetime(2026, 9, 11, 17, 5, tzinfo=UTC),
    )


def test_candidate_current_maps_to_generic_view_without_losing_operator_freshness() -> None:
    current = current_view()
    view = candidate_current_to_product_operator_view(current)

    assert view.source == "cand001_operator_current"
    assert view.product_version == "DAX-BOT-1.0-alpha"
    assert view.strategy_id == "CAND-001"
    assert view.config_fingerprint == "a" * 64
    assert view.source_snapshot_fingerprint == "d" * 64
    assert view.decision_id == "b" * 64
    assert view.decision_action == "TRADE"
    assert view.decision_blockers == ("RISK_PROFILE_RESEARCH_ONLY",)
    assert view.risk_state == "ALLOWED"
    assert view.last_market_event_id == "c" * 64
    assert view.last_market_event_time == datetime(2026, 9, 11, 16, 55, tzinfo=UTC)
    assert view.current_market_event_age_seconds == current.current_bar_age_seconds == 600.0
    assert view.health_state == "GREEN"
    assert view.health_source == "MT5_SHADOW_HOST"
    assert view.runtime_events == ("RESTART_CATCHUP",)
    assert view.recovery_state == "RESUME_ANCHOR_RECONCILED"
    assert view.reconciliation_state == "IN_SYNC"
    assert view.execution_capability == "NONE"
    assert view.order_execution_enabled is False


def test_adapter_is_deterministic_and_generic_json_is_stable() -> None:
    first = candidate_current_to_product_operator_view(current_view())
    second = candidate_current_to_product_operator_view(current_view())

    assert first == second
    assert len(first.view_fingerprint) == 64

    text = canonical_operator_view_json(first)
    decoded = json.loads(text)
    assert text == json.dumps(decoded, sort_keys=True, indent=2, ensure_ascii=True) + "\n"
    assert decoded["safety"] == {
        "execution_capability": "NONE",
        "order_execution_enabled": False,
    }
    assert "strategy" not in decoded
    assert "signal" not in decoded
    assert "trade_plan" not in decoded
    assert "virtual_position" not in decoded


def test_generic_view_supports_no_market_event_context() -> None:
    data = payload()
    runtime = dict(data["runtime"])  # type: ignore[arg-type]
    runtime["last_bar_id"] = None
    runtime["last_bar_close_time"] = None
    runtime["freshness_seconds"] = None
    data["runtime"] = runtime

    current = current_view(data)
    view = candidate_current_to_product_operator_view(current)

    assert current.current_bar_age_seconds is None
    assert view.last_market_event_id is None
    assert view.last_market_event_time is None
    assert view.current_market_event_age_seconds is None


def test_adapter_fails_closed_on_candidate_payload_safety_or_identity_drift() -> None:
    current = current_view()
    current.payload["safety"]["order_execution_enabled"] = True  # type: ignore[index]
    with pytest.raises(ValueError, match="order execution must be disabled"):
        candidate_current_to_product_operator_view(current)

    current = current_view()
    current.payload["snapshot_fingerprint"] = "e" * 64
    with pytest.raises(ValueError, match="snapshot fingerprint drift"):
        candidate_current_to_product_operator_view(current)


def test_generic_view_fails_closed_on_incomplete_health_or_fingerprint_tampering() -> None:
    current = current_view()
    current.payload["runtime"]["health_source"] = None  # type: ignore[index]
    with pytest.raises(ValueError, match="health_state and health_source must be paired"):
        candidate_current_to_product_operator_view(current)

    view = candidate_current_to_product_operator_view(current_view())
    with pytest.raises(ValueError, match="cannot authorize execution"):
        replace(view, order_execution_enabled=True)
    with pytest.raises(ValueError, match="fingerprint mismatch"):
        replace(view, risk_state="BLOCKED")


def test_generic_operator_core_has_no_candidate_runtime_mt5_or_execution_dependency() -> None:
    repo = Path(__file__).resolve().parents[1]
    module = repo / "src/daxlab/operator/read_model.py"
    tree = ast.parse(module.read_text(encoding="utf-8"))
    imported: set[str] = set()
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
        elif isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)

    forbidden_imports = (
        "daxlab.runtime",
        "daxlab.adapters",
        "daxlab.strategies.cand001",
        "daxlab.domain.execution",
        "MetaTrader5",
    )
    assert not any(
        name == prefix or name.startswith(prefix + ".")
        for name in imported
        for prefix in forbidden_imports
    )
    assert "order_send" not in names
    assert "accept_intent" not in names


def test_candidate_operator_adapter_has_no_mt5_or_execution_dependency() -> None:
    repo = Path(__file__).resolve().parents[1]
    module = repo / "src/daxlab/adapters/cand001_operator.py"
    tree = ast.parse(module.read_text(encoding="utf-8"))
    imported: set[str] = set()
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
        elif isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)

    forbidden_imports = (
        "MetaTrader5",
        "daxlab.runtime.mt5",
        "daxlab.domain.execution",
        "daxlab.runtime.broker",
    )
    assert not any(
        name == prefix or name.startswith(prefix + ".")
        for name in imported
        for prefix in forbidden_imports
    )
    assert "order_send" not in names
    assert "accept_intent" not in names
