"""Portable atomic byte-state adapter for the NextGen ``StateStorePort``.

The adapter owns storage mechanics only.  State schemas, checkpoint semantics,
recovery bundles and broker/runtime lifecycle remain owned by their existing
specialized components.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re
import tempfile


_PORTABLE_KEY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


@dataclass(frozen=True, slots=True)
class AtomicFileStateStore:
    """Persist opaque state bytes beneath one configured root directory."""

    root: Path

    def __post_init__(self) -> None:
        root = Path(self.root)
        if root.exists() and not root.is_dir():
            raise ValueError("state-store root must be a directory")
        object.__setattr__(self, "root", root)

    def load(self, key: str) -> bytes | None:
        """Load exact persisted bytes, returning ``None`` when the key is absent."""

        target = self._path_for_key(key)
        try:
            return target.read_bytes()
        except FileNotFoundError:
            return None

    def save(self, key: str, payload: bytes) -> None:
        """Atomically replace one key with an exact opaque byte payload."""

        if not isinstance(payload, bytes):
            raise TypeError("payload must be bytes")
        target = self._path_for_key(key)
        self.root.mkdir(parents=True, exist_ok=True)

        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{target.name}.",
            suffix=".tmp",
            dir=self.root,
        )
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, target)
        finally:
            if temporary.exists():
                temporary.unlink()

    def _path_for_key(self, key: str) -> Path:
        if not isinstance(key, str):
            raise TypeError("state-store key must be str")
        if key in {".", ".."} or _PORTABLE_KEY.fullmatch(key) is None:
            raise ValueError(
                "state-store key must be 1-128 portable characters: "
                "letters, digits, dot, underscore or hyphen"
            )
        return self.root / f"{key}.bin"
