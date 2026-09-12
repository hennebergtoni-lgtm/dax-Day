from __future__ import annotations

import ast
from dataclasses import dataclass, fields
from datetime import datetime, timedelta, timezone
from pathlib import Path

from daxlab.domain.market import Candle, InstrumentId
from daxlab.domain.strategy import (
    StrategyAction,
    StrategyDecision,
    TradeDirection,
    TradePlan,
)
from daxlab.strategies.contracts import StrategyPlugin, StrategyTransition


UTC = timezone.utc
STRATEGY_FINGERPRINT = "a" * 64


@dataclass(frozen=True, slots=True)
class CounterState:
    candles_seen: int = 0


class SyntheticStrategy:
    @property
    def strategy_id(self) -> str:
        return "SYNTHETIC_CONFORMANCE"

    @property
    def strategy_version(self) -> str:
        return "1.0"

    @property
    def strategy_fingerprint(self) -> str:
        return STRATEGY_FINGERPRINT

    def initial_state(self) -> CounterState:
        return CounterState()

    def on_candle(
        self,
        state: CounterState,
        candle: Candle,
    ) -> StrategyTransition[CounterState]:
        next_state = CounterState(candles_seen=state.candles_seen + 1)
        if candle.close <= candle.open:
            decision = StrategyDecision.no_trade(
                strategy_id=self.strategy_id,
                strategy_version=self.strategy_version,
                strategy_fingerprint=self.strategy_fingerprint,
                event_time=candle.close_time,
                instrument_id=candle.instrument_id,
                reason_codes=("NO_LONG_TRIGGER",),
            )
        else:
            decision = StrategyDecision.trade(
                strategy_id=self.strategy_id,
                strategy_version=self.strategy_version,
                strategy_fingerprint=self.strategy_fingerprint,
                event_time=candle.close_time,
                instrument_id=candle.instrument_id,
                reason_codes=("SYNTHETIC_LONG_TRIGGER",),
                trade_plan=TradePlan(
                    instrument_id=candle.instrument_id,
                    direction=TradeDirection.LONG,
                    entry_price=candle.close,
                    stop_price=candle.close - 10.0,
                    target_price=candle.close + 20.0,
                ),
            )
        return StrategyTransition(state=next_state, decision=decision)


def _candle(*, bullish: bool = True) -> Candle:
    event_time = datetime(2026, 9, 11, 8, 0, tzinfo=UTC)
    open_price = 25_000.0
    close_price = 25_010.0 if bullish else 24_990.0
    return Candle(
        instrument_id=InstrumentId("DAX.CFD"),
        timeframe="5m",
        event_time=event_time,
        close_time=event_time + timedelta(minutes=5),
        open=open_price,
        high=25_015.0,
        low=24_985.0,
        close=close_price,
        volume=None,
        source="SYNTHETIC_TEST",
        received_at=event_time + timedelta(minutes=5, seconds=1),
        is_closed=True,
    )


def test_strategy_plugin_is_deterministic_for_same_state_and_candle() -> None:
    plugin = SyntheticStrategy()
    state = plugin.initial_state()
    candle = _candle()

    first = plugin.on_candle(state, candle)
    second = plugin.on_candle(state, candle)

    assert isinstance(plugin, StrategyPlugin)
    assert first == second
    assert first.state == CounterState(candles_seen=1)
    assert first.decision.action is StrategyAction.TRADE_PLAN
    assert first.decision.decision_id == second.decision.decision_id
    assert first.decision.trade_plan is not None
    assert first.decision.trade_plan.direction is TradeDirection.LONG


def test_no_trade_decision_is_deterministic_and_plan_free() -> None:
    plugin = SyntheticStrategy()
    state = plugin.initial_state()
    candle = _candle(bullish=False)

    transition = plugin.on_candle(state, candle)

    assert transition.decision.action is StrategyAction.NO_TRADE
    assert transition.decision.trade_plan is None
    assert transition.decision.reason_codes == ("NO_LONG_TRIGGER",)


def test_trade_plan_stops_before_risk_sizing_and_execution() -> None:
    assert {field.name for field in fields(TradePlan)} == {
        "instrument_id",
        "direction",
        "entry_price",
        "stop_price",
        "target_price",
    }


def test_strategy_contracts_have_no_runtime_broker_legacy_or_candidate_imports() -> None:
    root = Path(__file__).resolve().parents[1]
    sources = (
        root / "src/daxlab/domain/strategy.py",
        root / "src/daxlab/strategies/contracts.py",
    )
    imported_modules: set[str] = set()
    for path in sources:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module)

    forbidden_prefixes = (
        "MetaTrader5",
        "daxlab.runtime",
        "daxlab.data.legacy_dataset",
        "daxlab.research",
    )
    assert not any(
        module.startswith(forbidden_prefixes) or ".candidate" in module
        for module in imported_modules
    )
