"""Opaque strategy-state serialization boundary for deterministic restart/resume."""
from __future__ import annotations

from typing import Protocol, TypeVar, runtime_checkable


StateT = TypeVar("StateT")


@runtime_checkable
class StrategyStateCodec(Protocol[StateT]):
    """Caller-owned deterministic codec for strategy state only."""

    @property
    def codec_id(self) -> str: ...

    def encode(self, state: StateT) -> bytes: ...

    def decode(self, payload: bytes) -> StateT: ...
