from __future__ import annotations

import ast
from dataclasses import dataclass, fields
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path

import pytest

from daxlab.domain.market import Candle, InstrumentId
from daxlab.domain.strategy import (
    StrategyAction,
    StrategyDecision,
    TradeDirection,
    TradePlan,
)
from daxlab.strategies import StrategyPlugin, StrategyTransition


@dataclass(frozen=True, slots=True)
class DemoState:
    seen: int = 0


class DemoStrategy:
    @property
    def strategy_id(self) -> str:
        return "SYNTHETIC-CONFORMANCE"

    @property
    def strategy_version(self) -> str:
        return "1"

    @property
    def strategy_fingerprint(self) -> str:
        return sha256(b"synthetic-conformance-v1").hexdigest()

    def initial_state(self) -> DemoState:
        return DemoState()

    def on_candle(self, state: DemoState, candle: Candle) -> StrategyTransition[DemoState]:
        next_state = DemoState(seen=state.seen + 1)
        if state.seen == 0:
            decision = StrategyDecision.no_trade(
                strategy_id=self.strategy_id,
                strategy_version=self.strategy_version,
                strategy_fingerprint=self.strategy_fingerprint,
                event_time=candle.close_time,
                instrument_id=candle.instrument_id,
                reason_codes=("WARMUP",),
            )
        else:
            decision = StrategyDecision.trade(
                strategy_id=self.strategy_id,
                strategy_version=self.strategy_version,
                strategy_fingerprint=self.strategy_fingerprint,
                event_time=candle.close_time,
                instrument_id=candle.instrument_id,
                reason_codes=("SYNTHETIC_SIGNAL",),
                trade_plan=TradePlan(
                    instrument_id=candle.instrument_id,
                    direction=TradeDirection.LONG,
                    entry_price=candle.close,
                    stop_price=candle.close - 10.0,
                    target_price=candle.close + 20.0,
                ),
            )
        return StrategyTransition(state=next_state, decision=decision)


def _candle(minute: int, close: float = 20_000.0) -> Candle:
    start = datetime(2026, 9, 10, 8, minute, tzinfo=timezone.utc)
    return Candle(
        instrument_id=InstrumentId("DAX.CFD"),
        timeframe="M5",
        event_time=start,
        close_time=start + timedelta(minutes=5),
        open=close - 2.0,
        high=close + 3.0,
        low=close - 4.0,
        close=close,
        volume=None,
        source="SYNTHETIC_TEST",
        received_at=start + timedelta(minutes=5, seconds=1),
        is_closed=True,
    )


def test_strategy_plugin_is_runtime_conformant_and_deterministic() -> None:
    plugin = DemoStrategy()
    candle = _candle(0)

    assert isinstance(plugin, StrategyPlugin)

    first = plugin.on_candle(plugin.initial_state(), candle)
    second = plugin.on_candle(plugin.initial_state(), candle)

    assert first == second
    assert first.state == DemoState(seen=1)
    assert first.decision.action is StrategyAction.NO_TRADE
    assert first.decision.trade_plan is None
    assert len(first.decision.decision_id) == 64


def test_same_sequence_produces_same_state_and_decisions() -> None:
    plugin = DemoStrategy()
    candles = (_candle(0), _candle(5, close=20_010.0))

    def run_once() -> tuple[DemoState, tuple[StrategyDecision, ...]]:
        state = plugin.initial_state()
        decisions: list[StrategyDecision] = []
        for candle in candles:
            transition = plugin.on_candle(state, candle)
            state = transition.state
            decisions.append(transition.decision)
        return state, tuple(decisions)

    left = run_once()
    right = run_once()

    assert left == right
    assert left[0] == DemoState(seen=2)
    assert left[1][1].action is StrategyAction.TRADE_PLAN
    assert left[1][1].trade_plan is not None
    assert left[1][1].trade_plan.direction is TradeDirection.LONG


def test_strategy_output_stops_before_risk_sizing_and_execution() -> None:
    plan_field_names = {field.name for field in fields(TradePlan)}
    decision_field_names = {field.name for field in fields(StrategyDecision)}

    forbidden = {
        "quantity",
        "size",
        "lots",
        "account_id",
        "broker",
        "broker_symbol",
        "client_order_id",
        "order_id",
    }
    assert plan_field_names.isdisjoint(forbidden)
    assert decision_field_names.isdisjoint(forbidden)


def test_trade_plan_enforces_directional_price_invariants() -> None:
    instrument = InstrumentId("DAX.CFD")

    with pytest.raises(ValueError, match="LONG plan"):
        TradePlan(
            instrument_id=instrument,
            direction=TradeDirection.LONG,
            entry_price=100.0,
            stop_price=101.0,
            target_price=110.0,
        )

    with pytest.raises(ValueError, match="SHORT plan"):
        TradePlan(
            instrument_id=instrument,
            direction=TradeDirection.SHORT,
            entry_price=100.0,
            stop_price=90.0,
            target_price=80.0,
        )


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def test_strategy_foundation_has_no_runtime_broker_legacy_or_candidate_dependency() -> None:
    repo = Path(__file__).resolve().parents[1]
    owners = (
        repo / "src/daxlab/domain/strategy.py",
        repo / "src/daxlab/strategies/contracts.py",
        repo / "src/daxlab/strategies/__init__.py",
    )
    imported = set().union(*(_imported_modules(path) for path in owners))

    forbidden_prefixes = (
        "MetaTrader5",
        "daxlab.runtime",
        "daxlab.data.legacy_dataset",
        "daxlab.legacy",
    )
    assert not any(
        module == prefix or module.startswith(f"{prefix}.")
        for module in imported
        for prefix in forbidden_prefixes
    )
    assert not any("candidate" in module.lower() for module in imported)
