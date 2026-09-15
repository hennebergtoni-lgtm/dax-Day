from __future__ import annotations

import ast
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from daxlab.domain.market import Candle, InstrumentId
from daxlab.domain.strategy import StrategyAction, TradeDirection
from daxlab.runtime.candidate_admission import AdmissionStatus
from daxlab.runtime.candidate_config import Cand001Config
from daxlab.runtime.candidate_pipeline import Cand001PipelineState, process_cand001_candle
from daxlab.runtime.decision import FinalAction
from daxlab.strategies import StrategyPlugin
from daxlab.strategies.cand001 import (
    Cand001StrategyBinding,
    Cand001StrategyPlugin,
    adapt_cand001_runtime_candle,
)


INSTRUMENT = InstrumentId("DAX.CFD")
BINDING = Cand001StrategyBinding(instrument_id=INSTRUMENT, timeframe="M5")


def bar(
    minute: int,
    *,
    open_price: float,
    high_price: float,
    low_price: float,
    close_price: float,
) -> Candle:
    # 07:xx UTC == 09:xx Europe/Berlin on 2026-09-11 (CEST).
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


def sequence() -> tuple[Candle, ...]:
    return (
        bar(0, open_price=100, high_price=102, low_price=99, close_price=101),
        bar(5, open_price=101, high_price=103, low_price=98, close_price=102),
        bar(10, open_price=102, high_price=102.5, low_price=98.5, close_price=101),
        bar(15, open_price=102, high_price=105, low_price=101, close_price=104),
        bar(20, open_price=100, high_price=101, low_price=95, close_price=97),
    )


def test_adapter_is_strategy_plugin_and_reuses_existing_product_identity() -> None:
    plugin = Cand001StrategyPlugin(binding=BINDING)
    config = Cand001Config()

    assert isinstance(plugin, StrategyPlugin)
    assert plugin.strategy_id == config.candidate_id
    assert plugin.strategy_version == config.ruleset_version
    assert plugin.strategy_fingerprint == config.product_identity().fingerprint()


def test_canonical_candle_translation_is_explicit_and_lossless_for_strategy_fields() -> None:
    canonical = sequence()[0]
    runtime = adapt_cand001_runtime_candle(canonical, binding=BINDING)

    assert runtime.symbol == "DE40"
    assert runtime.timeframe == "5m"
    assert runtime.event_time == canonical.event_time
    assert runtime.close_time == canonical.close_time
    assert runtime.open == canonical.open
    assert runtime.high == canonical.high
    assert runtime.low == canonical.low
    assert runtime.close == canonical.close
    assert runtime.volume == canonical.volume
    assert runtime.source == canonical.source
    assert runtime.received_at == canonical.received_at
    assert runtime.is_closed is canonical.is_closed
    assert runtime.quality_state.value == canonical.quality_state.value


def test_plugin_matches_direct_cand001_pipeline_state_and_trade_geometry() -> None:
    plugin = Cand001StrategyPlugin(binding=BINDING)
    direct_state = Cand001PipelineState()
    plugin_state = plugin.initial_state()
    plugin_transitions = []
    direct_results = []

    for canonical in sequence():
        runtime = adapt_cand001_runtime_candle(canonical, binding=BINDING)
        direct = process_cand001_candle(
            direct_state,
            runtime,
            observed_at=canonical.received_at,
        )
        transition = plugin.on_candle(plugin_state, canonical)

        assert transition.state == direct.state
        direct_state = direct.state
        plugin_state = transition.state
        direct_results.append(direct)
        plugin_transitions.append(transition)

    # Opening-range bars stay no-trade in both paths.
    assert all(
        transition.decision.action is StrategyAction.NO_TRADE
        for transition in plugin_transitions[:3]
    )

    direct_breakout = direct_results[3]
    canonical_breakout = plugin_transitions[3].decision
    assert direct_breakout.decision.final_action is FinalAction.TRADE
    assert direct_breakout.admission.status is AdmissionStatus.ALLOWED
    assert direct_breakout.admission.admitted_plan is not None
    assert canonical_breakout.action is StrategyAction.TRADE_PLAN
    assert canonical_breakout.trade_plan is not None
    assert canonical_breakout.trade_plan.direction is TradeDirection.LONG
    assert canonical_breakout.trade_plan.entry_price == direct_breakout.admission.admitted_plan.entry_price
    assert canonical_breakout.trade_plan.stop_price == direct_breakout.admission.admitted_plan.stop_price
    assert canonical_breakout.trade_plan.target_price == direct_breakout.admission.admitted_plan.target_price
    assert (
        canonical_breakout.trade_plan.entry_price,
        canonical_breakout.trade_plan.stop_price,
        canonical_breakout.trade_plan.target_price,
    ) == (104, 98, 113)

    # The later short breakout is still visible to the old pipeline but admission blocks it.
    direct_second = direct_results[4]
    canonical_second = plugin_transitions[4].decision
    assert direct_second.admission.status is AdmissionStatus.SESSION_LIMIT
    assert direct_second.decision.final_action is FinalAction.NO_TRADE
    assert direct_second.decision.blockers == ("SESSION_TRADE_LIMIT",)
    assert canonical_second.action is StrategyAction.NO_TRADE
    assert canonical_second.trade_plan is None
    assert "ADMISSION:SESSION_LIMIT" in canonical_second.reason_codes
    assert "BLOCKER:SESSION_TRADE_LIMIT" in canonical_second.reason_codes
    assert plugin_state.admission.trades_admitted == 1


def test_adapter_replay_is_deterministic() -> None:
    plugin = Cand001StrategyPlugin(binding=BINDING)

    def run_once():
        state = plugin.initial_state()
        transitions = []
        for canonical in sequence():
            transition = plugin.on_candle(state, canonical)
            state = transition.state
            transitions.append(transition)
        return tuple(transitions)

    assert run_once() == run_once()
    assert tuple(item.decision.decision_id for item in run_once()) == tuple(
        item.decision.decision_id for item in run_once()
    )


def test_adapter_fails_closed_on_unbound_instrument_or_timeframe() -> None:
    canonical = sequence()[0]

    wrong_instrument = Candle(
        instrument_id=InstrumentId("OTHER"),
        timeframe=canonical.timeframe,
        event_time=canonical.event_time,
        close_time=canonical.close_time,
        open=canonical.open,
        high=canonical.high,
        low=canonical.low,
        close=canonical.close,
        volume=canonical.volume,
        source=canonical.source,
        received_at=canonical.received_at,
        is_closed=canonical.is_closed,
        quality_state=canonical.quality_state,
    )
    with pytest.raises(ValueError, match="instrument"):
        adapt_cand001_runtime_candle(wrong_instrument, binding=BINDING)

    wrong_timeframe = Candle(
        instrument_id=canonical.instrument_id,
        timeframe="M1",
        event_time=canonical.event_time,
        close_time=canonical.close_time,
        open=canonical.open,
        high=canonical.high,
        low=canonical.low,
        close=canonical.close,
        volume=canonical.volume,
        source=canonical.source,
        received_at=canonical.received_at,
        is_closed=canonical.is_closed,
        quality_state=canonical.quality_state,
    )
    with pytest.raises(ValueError, match="timeframe"):
        adapt_cand001_runtime_candle(wrong_timeframe, binding=BINDING)


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def test_adapter_adds_no_broker_paper_mt5_or_order_submission_dependency() -> None:
    repo = Path(__file__).resolve().parents[1]
    adapter = repo / "src/daxlab/strategies/cand001/adapter.py"
    imported = _imported_modules(adapter)
    source = adapter.read_text(encoding="utf-8").lower()

    forbidden_prefixes = (
        "MetaTrader5",
        "daxlab.runtime.mt5",
        "daxlab.runtime.broker",
        "daxlab.runtime.paper",
    )
    assert not any(
        module == prefix or module.startswith(f"{prefix}.")
        for module in imported
        for prefix in forbidden_prefixes
    )
    assert "order_send" not in source
    assert "metatrader5" not in source
