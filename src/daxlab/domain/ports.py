"""Minimal external ports for the deterministic NextGen product core.

These Protocols define dependency direction only. They contain no venue client,
credentials, persistence backend or order-submission implementation.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

from daxlab.domain.execution import ExecutionIntent
from daxlab.domain.market import Candle


@runtime_checkable
class ClockPort(Protocol):
    """Provide the environment clock without exposing host-specific APIs."""

    def now(self) -> datetime: ...


@runtime_checkable
class CandleSourcePort(Protocol):
    """Yield one canonical candle at a time for replay or real-time processing."""

    def next_candle(self) -> Candle | None: ...


@runtime_checkable
class StateStorePort(Protocol):
    """Persist opaque deterministic state without binding the core to a backend."""

    def load(self, key: str) -> bytes | None: ...

    def save(self, key: str, payload: bytes) -> None: ...


@runtime_checkable
class ExecutionIntentSinkPort(Protocol):
    """Accept product intent at an external boundary without granting order capability."""

    def accept_intent(self, intent: ExecutionIntent) -> None: ...
