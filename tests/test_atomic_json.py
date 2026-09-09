import json
from pathlib import Path

import pytest

from daxlab.runtime.atomic_json import atomic_write_json, read_json_object


def test_atomic_write_round_trip_and_no_temp_left(tmp_path: Path) -> None:
    path = tmp_path / "state" / "heartbeat.json"
    atomic_write_json(path, {"status": "GREEN", "order_execution_enabled": False})
    assert read_json_object(path) == {
        "order_execution_enabled": False,
        "status": "GREEN",
    }
    assert not path.with_name(f".{path.name}.tmp").exists()


def test_atomic_write_replaces_existing_object(tmp_path: Path) -> None:
    path = tmp_path / "resume.json"
    atomic_write_json(path, {"generation": 1})
    atomic_write_json(path, {"generation": 2})
    assert json.loads(path.read_text(encoding="utf-8")) == {"generation": 2}


def test_read_json_object_rejects_non_object(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="JSON object required"):
        read_json_object(path)
