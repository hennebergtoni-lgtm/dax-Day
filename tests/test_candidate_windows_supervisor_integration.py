from __future__ import annotations

from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import sys

from daxlab.runtime.paper_contracts import ExecutionIntent, Side


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "mt5_shadow_supervisor.py"


def _load_supervisor_module():
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location("candidate_mt5_shadow_supervisor_test", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_candidate_intent_outbox_payload_is_json_safe_and_execution_disabled() -> None:
    supervisor = _load_supervisor_module()
    intent = ExecutionIntent.build(
        decision_id="1" * 64,
        run_manifest_fingerprint="2" * 64,
        created_at=datetime(2026, 9, 11, 9, 20, tzinfo=timezone.utc),
        symbol="DE40",
        side=Side.BUY,
        quantity=1.0,
        requested_price=100.0,
        stop_price=90.0,
        target_price=115.0,
    )

    payload = supervisor._intent_payload(intent)

    json.dumps(payload, sort_keys=True)
    assert payload["client_order_id"] == intent.client_order_id
    assert payload["side"] == "BUY"
    assert payload["execution_capability"] == "NONE"
    assert payload["order_execution_enabled"] is False


def test_candidate_runs_only_after_existing_green_gate_and_publication_precedes_checkpoint() -> None:
    source = SCRIPT.read_text(encoding="utf-8")

    legacy_gate = source.index("cycle = process_mt5_shadow_cycle")
    green_guard = source.index('cycle.heartbeat.get("status") == "GREEN"')
    candidate_run = source.index("candidate_cycle = run_cand001_shadow_host_cycle")
    publication = source.index("_persist_candidate_publications(", candidate_run)
    checkpoint = source.index("candidate_checkpoint_path,", publication)

    assert legacy_gate < green_guard < candidate_run < publication < checkpoint
    assert "order_send" not in source
    assert '"execution_capability": "NONE"' in source
    assert '"order_execution_enabled": False' in source
