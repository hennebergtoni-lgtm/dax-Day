import json
from pathlib import Path

import pytest

from daxlab.runtime.single_instance import SingleInstanceLock


def test_second_writer_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "dax.lock"
    first = SingleInstanceLock(path=path, identity="DAX")
    second = SingleInstanceLock(path=path, identity="DAX")
    first.acquire()
    try:
        assert first.held
        with pytest.raises(RuntimeError, match="already held"):
            second.acquire()
    finally:
        first.release()
    assert path.exists()
    assert not first.held


def test_release_allows_immediate_reacquire(tmp_path: Path) -> None:
    path = tmp_path / "dax.lock"
    first = SingleInstanceLock(path=path, identity="DAX")
    second = SingleInstanceLock(path=path, identity="DAX")
    first.acquire()
    first.release()
    second.acquire()
    try:
        assert second.held
    finally:
        second.release()


def test_stale_lock_file_does_not_block_restart(tmp_path: Path) -> None:
    path = tmp_path / "dax.lock"
    path.write_text(json.dumps({"identity": "DAX", "pid": 999999}), encoding="utf-8")
    lock = SingleInstanceLock(path=path, identity="DAX")
    lock.acquire()
    try:
        assert lock.held
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["identity"] == "DAX"
        assert isinstance(payload["pid"], int)
        assert payload["pid"] != 999999
    finally:
        lock.release()


def test_context_manager_releases_os_lock_but_keeps_metadata(tmp_path: Path) -> None:
    path = tmp_path / "dax.lock"
    lock = SingleInstanceLock(path=path, identity="DAX")
    with lock:
        assert path.exists()
        assert lock.held
    assert path.exists()
    assert not lock.held


def test_same_object_cannot_acquire_twice(tmp_path: Path) -> None:
    lock = SingleInstanceLock(path=tmp_path / "dax.lock", identity="DAX")
    lock.acquire()
    try:
        with pytest.raises(RuntimeError, match="already held by this object"):
            lock.acquire()
    finally:
        lock.release()


def test_empty_identity_is_rejected(tmp_path: Path) -> None:
    lock = SingleInstanceLock(path=tmp_path / "dax.lock", identity="  ")
    with pytest.raises(ValueError, match="identity must be non-empty"):
        lock.acquire()
