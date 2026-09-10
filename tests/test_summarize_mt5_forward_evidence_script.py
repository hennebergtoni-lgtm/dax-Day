from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
import sys

from daxlab.runtime.mt5_heartbeat_history import archive_heartbeat_snapshot


def _heartbeat(at: datetime, *, status: str = "GREEN", blockers=None, processed: int | None = 1):
    return {
        "schema_version": "DAXLAB_MT5_SHADOW_HEARTBEAT_V1",
        "observed_at_utc": at.isoformat(),
        "status": status,
        "blockers": list(blockers or []),
        "processed_total": processed,
        "new_decisions": 1 if status == "GREEN" else 0,
        "duplicates_suppressed": 0,
        "execution_capability": "NONE",
        "order_execution_enabled": False,
    }


def _run(state_dir: Path, output: Path | None = None):
    command = [
        sys.executable,
        "scripts/summarize_mt5_forward_evidence.py",
        "--state-dir",
        str(state_dir),
    ]
    if output is not None:
        command += ["--output", str(output)]
    return subprocess.run(command, check=True, capture_output=True, text=True)


def test_empty_history_reports_no_evidence(tmp_path) -> None:
    result = _run(tmp_path)
    payload = json.loads(result.stdout)
    assert payload["status"] == "NO_EVIDENCE"
    assert payload["heartbeat_count"] == 0
    assert payload["execution_capability"] == "NONE"
    assert payload["order_execution_enabled"] is False


def test_history_is_summarized_and_optional_output_written(tmp_path) -> None:
    history = tmp_path / "heartbeat_history"
    base = datetime(2026, 9, 10, 8, 0, tzinfo=timezone.utc)
    archive_heartbeat_snapshot(history, _heartbeat(base))
    archive_heartbeat_snapshot(
        history,
        _heartbeat(
            base + timedelta(minutes=1),
            status="BLOCKED",
            blockers=["HISTORICAL_BAR_MUTATION"],
            processed=None,
        ),
    )
    output = tmp_path / "summary.json"
    result = _run(tmp_path, output)
    payload = json.loads(result.stdout)
    persisted = json.loads(output.read_text(encoding="utf-8"))
    assert payload == persisted
    assert payload["status"] == "BLOCKED_PRESENT"
    assert payload["heartbeat_count"] == 2
    assert payload["blocker_counts"] == [["HISTORICAL_BAR_MUTATION", 1]]


def test_script_contains_no_order_api() -> None:
    text = Path("scripts/summarize_mt5_forward_evidence.py").read_text(encoding="utf-8")
    for forbidden in ("order_send", "order_check", "positions_get", "history_deals_get"):
        assert forbidden not in text
    assert "load_heartbeat_history" in text
    assert "summarize_forward_evidence" in text
