from __future__ import annotations

from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path

import pytest

_EXPORTER_PATH = Path(__file__).resolve().parents[1] / "scripts" / "export_mt5_shadow_telemetry.py"
_SPEC = importlib.util.spec_from_file_location("export_mt5_shadow_telemetry", _EXPORTER_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("failed to load MT5 SHADOW telemetry exporter for tests")
telemetry = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(telemetry)


class _Bar:
    open_time = datetime(2026, 9, 11, 8, 0, tzinfo=timezone.utc)
    open = 18500.0
    high = 18510.0
    low = 18495.0
    close = 18505.0


def _heartbeat() -> dict[str, object]:
    return {
        "schema_version": "DAXLAB_MT5_SHADOW_HEARTBEAT_V1",
        "observed_at_utc": "2026-09-11T08:05:01+00:00",
        "status": "GREEN",
        "blockers": [],
        "symbol": "DE40",
        "bundle_sha256": "a" * 64,
        "closed_m5_bars": 40,
        "latest_closed_bar_age_seconds": 1.0,
        "single_instance_lock_held": True,
        "processed_total": 300,
        "new_decisions": 1,
        "duplicates_suppressed": 0,
        "evidence_state": "MT5_READONLY_EVIDENCE",
        "cross_cycle_status": "GREEN",
        "cross_cycle_overlapping_bars": 39,
        "cross_cycle_identical_overlaps": 39,
        "cross_cycle_mutated_overlaps": 0,
        "history_archive_status": "OK",
        "execution_capability": "NONE",
        "order_execution_enabled": False,
    }


def _decision() -> dict[str, object]:
    return {
        "decision_id": "b" * 64,
        "observed_at": "2026-09-11T08:05:00+00:00",
        "symbol": "DE40",
        "closed_bar_fingerprint": "c" * 64,
        "action": "NO_ORDER",
        "reason_codes": ["OBSERVATION_ONLY_NO_ORDER"],
        "reference_experiment_id": "V112_REFERENCE_V1",
        "reference_engine_sha256": "d" * 64,
        "execution_capability": "NONE",
        "order_execution_enabled": False,
    }


def test_heartbeat_contract_accepts_no_order_payload() -> None:
    telemetry._validate_heartbeat(_heartbeat())


def test_heartbeat_contract_rejects_execution_enablement() -> None:
    payload = _heartbeat()
    payload["order_execution_enabled"] = True
    with pytest.raises(ValueError, match="order execution"):
        telemetry._validate_heartbeat(payload)


def test_heartbeat_contract_rejects_credentials_recursively() -> None:
    payload = _heartbeat()
    payload["metadata"] = {"token": "forbidden"}
    with pytest.raises(ValueError, match="forbidden telemetry field"):
        telemetry._validate_heartbeat(payload)


def test_decision_contract_accepts_no_order_payload() -> None:
    telemetry._validate_decision(_decision())


def test_decision_contract_rejects_execution_enablement() -> None:
    payload = _decision()
    payload["order_execution_enabled"] = True
    with pytest.raises(ValueError, match="order execution"):
        telemetry._validate_decision(payload)


def test_decision_contract_rejects_credentials_recursively() -> None:
    payload = _decision()
    payload["metadata"] = {"api_key": "forbidden"}
    with pytest.raises(ValueError, match="forbidden telemetry field"):
        telemetry._validate_decision(payload)


def test_decision_outbox_filename_must_match_id(tmp_path: Path) -> None:
    outbox = tmp_path / "decision_outbox"
    outbox.mkdir()
    payload = _decision()
    (outbox / ("e" * 64 + ".json")).write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="filename does not match"):
        telemetry._load_decision_outbox(tmp_path)


def test_decision_outbox_loads_valid_payload(tmp_path: Path) -> None:
    outbox = tmp_path / "decision_outbox"
    outbox.mkdir()
    payload = _decision()
    path = outbox / f"{payload['decision_id']}.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    items = telemetry._load_decision_outbox(tmp_path)
    assert items == [(path, payload)]


def test_bar_fingerprint_is_deterministic_sha256() -> None:
    first = telemetry._bar_fingerprint(_Bar())
    second = telemetry._bar_fingerprint(_Bar())
    assert first == second
    assert len(first) == 64
    int(first, 16)


def test_exporter_unlinks_decisions_only_after_transaction_block() -> None:
    source = Path(telemetry.__file__).read_text(encoding="utf-8")
    transaction_index = source.index("with conn.transaction():")
    unlink_index = source.index("path.unlink()")
    assert transaction_index < unlink_index
    assert "on conflict (decision_id) do nothing" in source


def test_exporter_has_no_metatrader5_import_and_idempotent_decision_sql() -> None:
    source = Path(telemetry.__file__).read_text(encoding="utf-8")
    assert "import MetaTrader5" not in source
    assert "from MetaTrader5" not in source
    assert "on conflict (decision_id) do nothing" in source
    assert "path.unlink()" in source
