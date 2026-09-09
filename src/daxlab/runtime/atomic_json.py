"""Small durable JSON persistence helpers for runtime state.

Writes always go to a sibling temporary file first, are fsynced, then atomically
replace the destination. Runtime callers therefore never observe a half-written
heartbeat or resume payload after interruption.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping


def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    encoded = json.dumps(
        payload,
        indent=2,
        sort_keys=True,
        ensure_ascii=True,
    ).encode("utf-8")
    try:
        with temporary.open("wb") as handle:
            handle.write(encoded)
            handle.write(b"\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def read_json_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path}")
    return value
