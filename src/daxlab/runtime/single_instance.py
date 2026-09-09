"""Crash-safe single-instance lock for adapter/runtime writers.

The lock file is persistent metadata; exclusivity comes from an operating-system
file lock, not from file existence. This avoids stale lock files blocking restart
after a crash or reboot.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class SingleInstanceLock:
    path: Path
    identity: str
    _fd: int | None = None

    @property
    def held(self) -> bool:
        return self._fd is not None

    def acquire(self) -> None:
        if self._fd is not None:
            raise RuntimeError("single-instance lock is already held by this object")
        if not self.identity.strip():
            raise ValueError("single-instance identity must be non-empty")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(self.path, os.O_CREAT | os.O_RDWR, 0o600)
        try:
            _prepare_lock_byte(fd)
            _lock_nonblocking(fd)
        except OSError as exc:
            os.close(fd)
            raise RuntimeError(f"single-instance lock already held: {self.path}") from exc
        try:
            payload = json.dumps(
                {"identity": self.identity, "pid": os.getpid()},
                sort_keys=True,
            ).encode("utf-8")
            os.ftruncate(fd, 0)
            os.lseek(fd, 0, os.SEEK_SET)
            os.write(fd, payload)
            os.fsync(fd)
        except Exception:
            _unlock(fd)
            os.close(fd)
            raise
        self._fd = fd

    def release(self) -> None:
        if self._fd is None:
            return
        fd = self._fd
        self._fd = None
        try:
            _unlock(fd)
        finally:
            os.close(fd)

    def __enter__(self) -> "SingleInstanceLock":
        self.acquire()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.release()


def _prepare_lock_byte(fd: int) -> None:
    """Ensure Windows can lock byte zero; harmless for an existing metadata file."""
    if os.fstat(fd).st_size == 0:
        os.write(fd, b"\0")
        os.fsync(fd)
    os.lseek(fd, 0, os.SEEK_SET)


def _lock_nonblocking(fd: int) -> None:
    if os.name == "nt":  # pragma: no cover - exercised on the real Windows host
        import msvcrt

        msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        return
    import fcntl

    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)


def _unlock(fd: int) -> None:
    os.lseek(fd, 0, os.SEEK_SET)
    if os.name == "nt":  # pragma: no cover - exercised on the real Windows host
        import msvcrt

        msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        return
    import fcntl

    fcntl.flock(fd, fcntl.LOCK_UN)
