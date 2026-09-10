from datetime import datetime, timedelta, timezone
import json

import pytest

from daxlab.runtime.mt5_heartbeat_history import (
    archive_heartbeat_snapshot,
    load_heartbeat_history,
)


def _heartbeat(at: datetime, *, status: str = "GREEN", **overrides):
    payload = {
        "schema_version": "DAXLAB_MT5_SHADOW_HEARTBEAT_V1",
        "observed_at_utc": at.isoformat(),
        "status": status,
        "blockers": [],
        "processed_total": 1,
        "new_decisions": 1,
        "duplicates_suppressed": 0,
        "execution_capability": "NONE",
        "order_execution_enabled": False,
    }
    payload.update(overrides)
    return payload


def test_archive_and_load_history_in_time_order(tmp_path) -> None:
    base = datetime(2026, 9, 10, 8, 0, tzinfo=timezone.utc)
    archive_heartbeat_snapshot(tmp_path, _heartbeat(base + timedelta(minutes=1)))
    archive_heartbeat_snapshot(tmp_path, _heartbeat(base))
    loaded = load_heartbeat_history(tmp_path)
    assert [item["observed_at_utc"] for item in loaded] == [
        base.isoformat(),
        (base + timedelta(minutes=1)).isoformat(),
    ]


def test_same_snapshot_is_idempotent(tmp_path) -> None:
    at = datetime(2026, 9, 10, 8, 0, tzinfo=timezone.utc)
    heartbeat = _heartbeat(at)
    first = archive_heartbeat_snapshot(tmp_path, heartbeat)
    second = archive_heartbeat_snapshot(tmp_path, heartbeat)
    assert first == second
    assert len(list(tmp_path.glob("heartbeat_*.json"))) == 1


def test_retention_keeps_newest_entries(tmp_path) -> None:
    base = datetime(2026, 9, 10, 8, 0, tzinfo=timezone.utc)
    for minute in range(4):
        archive_heartbeat_snapshot(
            tmp_path,
            _heartbeat(base + timedelta(minutes=minute)),
            max_entries=2,
        )
    loaded = load_heartbeat_history(tmp_path)
    assert len(loaded) == 2
    assert [item["observed_at_utc"] for item in loaded] == [
        (base + timedelta(minutes=2)).isoformat(),
        (base + timedelta(minutes=3)).isoformat(),
    ]


def test_invalid_retention_fails_closed(tmp_path) -> None:
    at = datetime(2026, 9, 10, 8, 0, tzinfo=timezone.utc)
    for value in (0, -1, True):
        with pytest.raises(ValueError, match="max_entries"):
            archive_heartbeat_snapshot(tmp_path, _heartbeat(at), max_entries=value)


def test_credentials_and_execution_capability_are_rejected(tmp_path) -> None:
    at = datetime(2026, 9, 10, 8, 0, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="forbidden heartbeat history key"):
        archive_heartbeat_snapshot(tmp_path, _heartbeat(at, password="never"))
    with pytest.raises(ValueError, match="execution_capability"):
        archive_heartbeat_snapshot(tmp_path, _heartbeat(at, execution_capability="PAPER"))
    with pytest.raises(ValueError, match="order_execution_enabled"):
        archive_heartbeat_snapshot(tmp_path, _heartbeat(at, order_execution_enabled=True))


def test_invalid_status_or_timestamp_is_rejected(tmp_path) -> None:
    at = datetime(2026, 9, 10, 8, 0, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="unsupported heartbeat status"):
        archive_heartbeat_snapshot(tmp_path, _heartbeat(at, status="UNKNOWN"))
    naive = datetime(2026, 9, 10, 8, 0)
    with pytest.raises(ValueError, match="timezone-aware"):
        archive_heartbeat_snapshot(tmp_path, _heartbeat(naive))
    non_utc = at.astimezone(timezone(timedelta(hours=2)))
    with pytest.raises(ValueError, match="must be UTC"):
        archive_heartbeat_snapshot(tmp_path, _heartbeat(non_utc))


def test_history_load_revalidates_entries(tmp_path) -> None:
    at = datetime(2026, 9, 10, 8, 0, tzinfo=timezone.utc)
    path = archive_heartbeat_snapshot(tmp_path, _heartbeat(at))
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["order_execution_enabled"] = True
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="order_execution_enabled"):
        load_heartbeat_history(tmp_path)
