"""Bounded atomic heartbeat history for MT5 read-only SHADOW."""
from __future__ import annotations

from datetime import datetime, timedelta
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping

from daxlab.runtime.atomic_json import atomic_write_json

_ALLOWED_STATUSES = frozenset({"GREEN", "BLOCKED", "ERROR", "STOPPED"})
_FORBIDDEN_KEYS = frozenset({"login", "password", "token", "secret", "email", "phone", "account_id"})


def archive_heartbeat_snapshot(
    history_dir: Path,
    heartbeat: Mapping[str, Any],
    *,
    max_entries: int = 2000,
) -> Path:
    if type(max_entries) is not int or max_entries < 1:
        raise ValueError("max_entries must be positive integer")
    _validate_heartbeat(heartbeat)
    history_dir.mkdir(parents=True, exist_ok=True)
    filename = _filename(heartbeat)
    destination = history_dir / filename
    atomic_write_json(destination, heartbeat)
    _prune(history_dir, max_entries=max_entries)
    return destination


def load_heartbeat_history(history_dir: Path) -> tuple[dict[str, Any], ...]:
    if not history_dir.exists():
        return ()
    payloads: list[dict[str, Any]] = []
    for path in sorted(history_dir.glob("heartbeat_*.json")):
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError(f"heartbeat history entry must be object: {path}")
        _validate_heartbeat(value)
        payloads.append(value)
    return tuple(payloads)


def _filename(heartbeat: Mapping[str, Any]) -> str:
    observed = _observed_at(heartbeat)
    stamp = observed.strftime("%Y%m%dT%H%M%S%fZ")
    canonical = json.dumps(heartbeat, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    digest = sha256(canonical.encode("utf-8")).hexdigest()[:16]
    return f"heartbeat_{stamp}_{digest}.json"


def _observed_at(heartbeat: Mapping[str, Any]) -> datetime:
    value = heartbeat.get("observed_at_utc")
    if not isinstance(value, str):
        raise ValueError("heartbeat observed_at_utc must be ISO string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("heartbeat observed_at_utc invalid") from exc
    if parsed.tzinfo is None:
        raise ValueError("heartbeat observed_at_utc must be timezone-aware")
    if parsed.utcoffset() != timedelta(0):
        raise ValueError("heartbeat observed_at_utc must be UTC")
    return parsed


def _validate_heartbeat(heartbeat: Mapping[str, Any]) -> None:
    _assert_credential_free(heartbeat)
    if heartbeat.get("status") not in _ALLOWED_STATUSES:
        raise ValueError("unsupported heartbeat status")
    if heartbeat.get("execution_capability") != "NONE":
        raise ValueError("heartbeat execution_capability must be NONE")
    if heartbeat.get("order_execution_enabled") is not False:
        raise ValueError("heartbeat order_execution_enabled must be false")
    _observed_at(heartbeat)


def _prune(history_dir: Path, *, max_entries: int) -> None:
    entries = sorted(history_dir.glob("heartbeat_*.json"))
    excess = len(entries) - max_entries
    for path in entries[: max(0, excess)]:
        path.unlink()


def _assert_credential_free(payload: Mapping[str, Any]) -> None:
    def walk(value: Any) -> None:
        if isinstance(value, Mapping):
            for key, item in value.items():
                if str(key).lower() in _FORBIDDEN_KEYS:
                    raise ValueError(f"forbidden heartbeat history key: {key}")
                walk(item)
        elif isinstance(value, (list, tuple)):
            for item in value:
                walk(item)

    walk(payload)
