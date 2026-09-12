"""Generic deterministic strategy transition boundary.

Implementations own only strategy state and strategy rules. They must not own broker
connectivity, persistence backends, host scheduling, risk-authorized sizing or orders.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Protocol, TypeVar, runtime_checkable

from daxlab.domain.market import Candle
from daxlab.domain.strategy import StrategyDecision


StateT = TypeVar("StateT")


@dataclass(frozen=True, slots=True)
class StrategyTransition(Generic[StateT]):
    """Pure result of applying one canonical candle to strategy-owned state."""

    state: StateT
    decision: StrategyDecision


@runtime_checkable
class StrategyPlugin(Protocol[StateT]):
    """Minimal strategy interface shared by deterministic replay and forward modes."""

    @property
    def strategy_id(self) -> str: ...

    @property
    def strategy_version(self) -> str: ...

    @property
    def strategy_fingerprint(self) -> str: ...

    def initial_state(self) -> StateT: ...

    def on_candle(self, state: StateT, candle: Candle) -> StrategyTransition[StateT]: ...
