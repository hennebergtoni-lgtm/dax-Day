from pathlib import Path

import pytest

from daxlab.runtime.single_instance import SingleInstanceLock


def test_second_writer_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "dax.lock"
    first = SingleInstanceLock(path=path, identity="DAX")
    second = SingleInstanceLock(path=path, identity="DAX")
    first.acquire()
    try:
        with pytest.raises(RuntimeError, match="already held"):
            second.acquire()
    finally:
        first.release()
    assert not path.exists()


def test_context_manager_releases_lock(tmp_path: Path) -> None:
    path = tmp_path / "dax.lock"
    with SingleInstanceLock(path=path, identity="DAX"):
        assert path.exists()
    assert not path.exists()
