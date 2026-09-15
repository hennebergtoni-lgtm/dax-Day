from __future__ import annotations

from datetime import datetime, timezone
import importlib.util
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "read_candidate_operator_runtime.py"
_SPEC = importlib.util.spec_from_file_location("read_candidate_operator_runtime", _SCRIPT)
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)


class _Result:
    def __init__(self, row):
        self._row = row

    def fetchone(self):
        return self._row


class _Connection:
    def __init__(self, row):
        self._row = row

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql):
        assert sql == "select payload from cand001_operator_current limit 1"
        return _Result(self._row)


def _payload() -> dict[str, object]:
    return {
        "schema_version": "DAX_BOT_OPERATOR_SNAPSHOT_V3",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "core_version": "DAX-BOT-1.0-alpha",
        "candidate_id": "CAND-001",
        "config_fingerprint": "a" * 64,
        "strategy": {"regime": "OPEN", "structure": "OR15", "setup": "BREAKOUT"},
        "signal": {"direction": "NONE", "reason": "NO_BREAKOUT"},
        "admission": {"status": "NO_SIGNAL"},
        "decision": {
            "action": "NO_TRADE",
            "decision_id": "b" * 64,
            "blockers": [],
            "risk_result": "NO_SIGNAL",
        },
        "trade_plan": {"entry": None, "stop": None, "target": None, "reward_risk": None},
        "runtime": {
            "last_bar_id": None,
            "last_bar_close_time": None,
            "freshness_seconds": None,
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
        "outcome": {"outcome_id": None, "gross_r": None, "cost_r": None, "net_r": None},
        "safety": {"execution_capability": "NONE", "order_execution_enabled": False},
        "snapshot_fingerprint": "d" * 64,
    }


def test_reader_returns_safe_no_data(monkeypatch) -> None:
    monkeypatch.setattr(_MODULE.psycopg, "connect", lambda *args, **kwargs: _Connection(None))
    result = _MODULE.read_current("postgresql://credential-not-emitted")
    assert result["state"] == "NO_DATA"
    assert result["execution_capability"] == "NONE"
    assert result["order_execution_enabled"] is False
    assert "credential" not in str(result)


def test_reader_validates_and_returns_current_snapshot(monkeypatch) -> None:
    payload = _payload()
    monkeypatch.setattr(
        _MODULE.psycopg,
        "connect",
        lambda *args, **kwargs: _Connection((payload,)),
    )
    result = _MODULE.read_current("postgresql://credential-not-emitted")
    assert result["source"] == "cand001_operator_current"
    assert result["snapshot_fingerprint"] == "d" * 64
    assert result["execution_capability"] == "NONE"


def test_reader_rejects_non_object_payload(monkeypatch) -> None:
    monkeypatch.setattr(
        _MODULE.psycopg,
        "connect",
        lambda *args, **kwargs: _Connection(("bad",)),
    )
    with pytest.raises(RuntimeError, match="not a JSON object"):
        _MODULE.read_current("postgresql://credential-not-emitted")
