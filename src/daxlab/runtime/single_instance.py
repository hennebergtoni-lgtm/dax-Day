"""Fail-closed single-instance lock for future adapter/runtime writers."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class SingleInstanceLock:
    path: Path
    identity: str
    _held: bool = False

    def acquire(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps({"identity": self.identity, "pid": os.getpid()}, sort_keys=True)
        try:
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as exc:
            raise RuntimeError(f"single-instance lock already held: {self.path}") from exc
        try:
            os.write(fd, payload.encode("utf-8"))
        finally:
            os.close(fd)
        self._held = True

    def release(self) -> None:
        if not self._held:
            return
        try:
            self.path.unlink()
        finally:
            self._held = False

    def __enter__(self) -> "SingleInstanceLock":
        self.acquire()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.release()
