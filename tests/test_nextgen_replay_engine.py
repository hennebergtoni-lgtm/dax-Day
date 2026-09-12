from __future__ import annotations

import ast
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path

import pytest

from daxlab.domain.market import Candle, DataQualityState, InstrumentId
from daxlab.domain.strategy import (
    StrategyAction,
    StrategyDecision,
    TradeDirection,
    TradePlan,
)
from daxlab.engine import ENGINE_VERSION, ReplayInputError, StrategyContractError, replay_candles
from daxlab.strategies import StrategyTransition
from daxlab.strategies.cand001 import Cand001StrategyBinding, Cand001StrategyPlugin


INSTRUMENT = InstrumentId("DAX.CFD")
SYNTHETIC_FINGERPRINT = sha256(b"nextgen-replay-synthetic-v1").hexdigest()


@dataclass(frozen=True, slots=True)
class CounterState:
    seen: int = 0


class SyntheticStrategy:
    @property
    def strategy_id(self) -> str:
        return "SYNTHETIC-REPLAY"

    @property
    def strategy_version(self) -> str:
        return "1"

    @property
    def strategy_fingerprint(self) -> str:
        return SYNTHETIC_FINGERPRINT

    def initial_state(self) -> CounterState:
        return CounterState()

    def on_candle(self, state: CounterState, candle: Candle) -> StrategyTransition[CounterState]:
        next_state = CounterState(state.seen + 1)
        if candle.close > 101.0:
            decision = StrategyDecision.trade(
                strategy_id=self.strategy_id,
                strategy_version=self.strategy_version,
                strategy_fingerprint=self.strategy_fingerprint,
                event_time=candle.close_time,
                instrument_id=candle.instrument_id,
                reason_codes=("ABOVE_THRESHOLD",),
                trade_plan=TradePlan(
                    instrument_id=candle.instrument_id,
                    direction=TradeDirection.LONG,
                    entry_price=candle.close,
                    stop_price=candle.close - 1.0,
                    target_price=candle.close + 2.0,
                ),
            )
        else:
            decision = StrategyDecision.no_trade(
                strategy_id=self.strategy_id,
                strategy_version=self.strategy_version,
                strategy_fingerprint=self.strategy_fingerprint,
                event_time=candle.close_time,
                instrument_id=candle.instrument_id,
                reason_codes=("BELOW_THRESHOLD",),
            )
        return StrategyTransition(state=next_state, decision=decision)


class WrongDecisionTimeStrategy(SyntheticStrategy):
    def on_candle(self, state: CounterState, candle: Candle) -> StrategyTransition[CounterState]:
        return StrategyTransition(
            state=CounterState(state.seen + 1),
            decision=StrategyDecision.no_trade(
                strategy_id=self.strategy_id,
                strategy_version=self.strategy_version,
                strategy_fingerprint=self.strategy_fingerprint,
                event_time=candle.event_time,
                instrument_id=candle.instrument_id,
                reason_codes=("WRONG_TIME",),
            ),
        )


class DriftingIdentityStrategy(SyntheticStrategy):
    def __init__(self) -> None:
        self._reads = 0

    @property
    def strategy_fingerprint(self) -> str:
        self._reads += 1
        suffix = b"manifest" if self._reads == 1 else b"drifted"
        return sha256(b"strategy-" + suffix).hexdigest()


def candle(
    minute: int,
    *,
    close: float = 100.0,
    instrument_id: InstrumentId = INSTRUMENT,
    timeframe: str = "M5",
    received_offset_seconds: int = 1,
    is_closed: bool = True,
    quality_state: DataQualityState = DataQualityState.OK,
) -> Candle:
    event_time = datetime(2026, 9, 10, 8, minute, tzinfo=timezone.utc)
    close_time = event_time + timedelta(minutes=5)
    return Candle(
        instrument_id=instrument_id,
        timeframe=timeframe,
        event_time=event_time,
        close_time=close_time,
        open=close - 0.5,
        high=close + 1.0,
        low=close - 1.0,
        close=close,
        volume=None,
        source="SYNTHETIC_TEST",
        received_at=close_time + timedelta(seconds=received_offset_seconds),
        is_closed=is_closed,
        quality_state=quality_state,
    )


def synthetic_sequence() -> tuple[Candle, ...]:
    return (
        candle(0, close=100.0),
        candle(5, close=101.0),
        candle(10, close=102.0),
    )


def test_replay_is_deterministic_and_has_no_execution_capability() -> None:
    left = replay_candles(SyntheticStrategy(), synthetic_sequence())
    right = replay_candles(SyntheticStrategy(), synthetic_sequence())

    assert left == right
    assert left.manifest.engine_version == ENGINE_VERSION
    assert left.manifest.instrument_id == INSTRUMENT
    assert left.manifest.timeframe == "M5"
    assert left.manifest.candle_count == 3
    assert len(left.manifest.input_fingerprint) == 64
    assert len(left.manifest.run_fingerprint) == 64
    assert len(left.decision_ids_fingerprint) == 64
    assert len(left.result_fingerprint) == 64
    assert left.final_state == CounterState(seen=3)
    assert tuple(item.action for item in left.decisions) == (
        StrategyAction.NO_TRADE,
        StrategyAction.NO_TRADE,
        StrategyAction.TRADE_PLAN,
    )
    assert left.execution_capability == "NONE"
    assert left.order_execution_enabled is False


def test_run_identity_changes_when_observation_input_changes_but_strategy_decisions_need_not() -> None:
    original = synthetic_sequence()
    changed = list(original)
    last = original[-1]
    changed[-1] = Candle(
        instrument_id=last.instrument_id,
        timeframe=last.timeframe,
        event_time=last.event_time,
        close_time=last.close_time,
        open=last.open,
        high=last.high,
        low=last.low,
        close=last.close,
        volume=last.volume,
        source=last.source,
        received_at=last.received_at + timedelta(seconds=1),
        is_closed=last.is_closed,
        quality_state=last.quality_state,
    )

    first = replay_candles(SyntheticStrategy(), original)
    second = replay_candles(SyntheticStrategy(), tuple(changed))

    assert first.manifest.input_fingerprint != second.manifest.input_fingerprint
    assert first.manifest.run_fingerprint != second.manifest.run_fingerprint
    assert tuple(item.decision_id for item in first.decisions) == tuple(
        item.decision_id for item in second.decisions
    )
    assert first.result_fingerprint != second.result_fingerprint


@pytest.mark.parametrize(
    ("candles", "message"),
    [
        ((), "at least one"),
        ((candle(0), candle(0)), "ordered and non-overlapping"),
        ((candle(5), candle(0)), "ordered and non-overlapping"),
        (
            (candle(0), candle(5, instrument_id=InstrumentId("OTHER"))),
            "mix instrument",
        ),
        ((candle(0), candle(5, timeframe="M1")), "mix timeframes"),
        ((candle(0, received_offset_seconds=-1),), "observed before it closed"),
        ((candle(0, is_closed=False),), "not safe for decision"),
        (
            (candle(0, quality_state=DataQualityState.STALE),),
            "not safe for decision",
        ),
    ],
)
def test_replay_fails_closed_on_unsafe_or_noncausal_input(
    candles: tuple[Candle, ...],
    message: str,
) -> None:
    with pytest.raises(ReplayInputError, match=message):
        replay_candles(SyntheticStrategy(), candles)


def test_replay_rejects_strategy_decision_with_wrong_event_time() -> None:
    with pytest.raises(StrategyContractError, match="time"):
        replay_candles(WrongDecisionTimeStrategy(), (candle(0),))


def test_replay_freezes_strategy_identity_at_run_start() -> None:
    with pytest.raises(StrategyContractError, match="fingerprint"):
        replay_candles(DriftingIdentityStrategy(), (candle(0),))


def cand001_sequence() -> tuple[Candle, ...]:
    def cand001_bar(
        minute: int,
        *,
        open_price: float,
        high_price: float,
        low_price: float,
        close_price: float,
    ) -> Candle:
        event = datetime(2026, 9, 11, 7, minute, tzinfo=timezone.utc)
        return Candle(
            instrument_id=INSTRUMENT,
            timeframe="M5",
            event_time=event,
            close_time=event + timedelta(minutes=5),
            open=open_price,
            high=high_price,
            low=low_price,
            close=close_price,
            volume=None,
            source="TEST",
            received_at=event + timedelta(minutes=5, seconds=1),
            is_closed=True,
        )

    return (
        cand001_bar(0, open_price=100, high_price=102, low_price=99, close_price=101),
        cand001_bar(5, open_price=101, high_price=103, low_price=98, close_price=102),
        cand001_bar(10, open_price=102, high_price=102.5, low_price=98.5, close_price=101),
        cand001_bar(15, open_price=102, high_price=105, low_price=101, close_price=104),
        cand001_bar(20, open_price=100, high_price=101, low_price=95, close_price=97),
    )


def test_cand001_adapter_replays_through_generic_engine_without_behavior_change() -> None:
    plugin = Cand001StrategyPlugin(
        binding=Cand001StrategyBinding(instrument_id=INSTRUMENT, timeframe="M5")
    )

    result = replay_candles(plugin, cand001_sequence())
    repeated = replay_candles(
        Cand001StrategyPlugin(
            binding=Cand001StrategyBinding(instrument_id=INSTRUMENT, timeframe="M5")
        ),
        cand001_sequence(),
    )

    assert result == repeated
    assert tuple(item.action for item in result.decisions) == (
        StrategyAction.NO_TRADE,
        StrategyAction.NO_TRADE,
        StrategyAction.NO_TRADE,
        StrategyAction.TRADE_PLAN,
        StrategyAction.NO_TRADE,
    )
    admitted = result.decisions[3].trade_plan
    assert admitted is not None
    assert admitted.direction is TradeDirection.LONG
    assert (admitted.entry_price, admitted.stop_price, admitted.target_price) == (104, 98, 113)
    assert "ADMISSION:SESSION_LIMIT" in result.decisions[4].reason_codes
    assert "BLOCKER:SESSION_TRADE_LIMIT" in result.decisions[4].reason_codes
    assert result.final_state.admission.trades_admitted == 1
    assert result.execution_capability == "NONE"
    assert result.order_execution_enabled is False


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def test_generic_engine_has_no_runtime_data_candidate_broker_or_order_dependency() -> None:
    repo = Path(__file__).resolve().parents[1]
    engine = repo / "src/daxlab/engine/replay.py"
    imported = _imported_modules(engine)
    source = engine.read_text(encoding="utf-8").lower()

    forbidden_prefixes = (
        "MetaTrader5",
        "daxlab.runtime",
        "daxlab.data",
        "daxlab.strategies.cand001",
    )
    assert not any(
        module == prefix or module.startswith(f"{prefix}.")
        for module in imported
        for prefix in forbidden_prefixes
    )
    assert "order_send" not in source
    assert "brokerexecutionport" not in source
