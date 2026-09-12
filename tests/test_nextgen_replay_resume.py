from __future__ import annotations

import ast
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path

import pytest

from daxlab.adapters.file_state_store import AtomicFileStateStore
from daxlab.domain.market import Candle, InstrumentId
from daxlab.domain.strategy import StrategyDecision, TradeDirection, TradePlan
from daxlab.engine.replay import fingerprint_decision_ids, replay_candles
from daxlab.engine.resume import interrupt_replay_candles, resume_replay_candles
from daxlab.state.replay_checkpoint import (
    CheckpointCompatibilityError,
    build_product_checkpoint,
    load_checkpoint,
    save_checkpoint,
)
from daxlab.strategies.contracts import StrategyTransition


UTC = timezone.utc
INSTRUMENT = InstrumentId("DAX.CFD")
CONFIG_FINGERPRINT = sha256(b"resume-config").hexdigest()
SOURCE_COMMIT = "1" * 40


@dataclass(frozen=True, slots=True)
class SyntheticState:
    count: int
    close_sum: float


class SyntheticStateCodec:
    codec_id = "synthetic-state-json-v1"

    def encode(self, state: SyntheticState) -> bytes:
        return json.dumps(
            {"close_sum": state.close_sum, "count": state.count},
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

    def decode(self, payload: bytes) -> SyntheticState:
        value = json.loads(payload.decode("utf-8"))
        return SyntheticState(count=int(value["count"]), close_sum=float(value["close_sum"]))


class NonCanonicalCodec(SyntheticStateCodec):
    def encode(self, state: SyntheticState) -> bytes:
        return json.dumps(
            {"close_sum": state.close_sum, "count": state.count},
            sort_keys=True,
            indent=2,
        ).encode("utf-8")


class SyntheticResumeStrategy:
    strategy_id = "SYNTHETIC-RESUME"
    strategy_version = "1"
    strategy_fingerprint = sha256(b"synthetic-resume-strategy-v1").hexdigest()

    def __init__(self) -> None:
        self.observed_close_times: list[datetime] = []

    def initial_state(self) -> SyntheticState:
        return SyntheticState(count=0, close_sum=0.0)

    def on_candle(
        self,
        state: SyntheticState,
        candle: Candle,
    ) -> StrategyTransition[SyntheticState]:
        self.observed_close_times.append(candle.close_time)
        next_state = SyntheticState(
            count=state.count + 1,
            close_sum=state.close_sum + candle.close,
        )
        if next_state.count % 2 == 0:
            decision = StrategyDecision.trade(
                strategy_id=self.strategy_id,
                strategy_version=self.strategy_version,
                strategy_fingerprint=self.strategy_fingerprint,
                event_time=candle.close_time,
                instrument_id=candle.instrument_id,
                reason_codes=("EVEN_EVENT",),
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
                reason_codes=("ODD_EVENT",),
            )
        return StrategyTransition(state=next_state, decision=decision)


def candles() -> tuple[Candle, ...]:
    values: list[Candle] = []
    for index, close in enumerate((100.0, 101.0, 102.0, 103.0, 104.0)):
        event_time = datetime(2026, 9, 10, 8, 0, tzinfo=UTC) + timedelta(minutes=5 * index)
        close_time = event_time + timedelta(minutes=5)
        values.append(
            Candle(
                instrument_id=INSTRUMENT,
                timeframe="M5",
                event_time=event_time,
                close_time=close_time,
                open=close - 0.5,
                high=close + 1.0,
                low=close - 1.0,
                close=close,
                volume=None,
                source="RESUME_FIXTURE",
                received_at=close_time + timedelta(seconds=1),
                is_closed=True,
            )
        )
    return tuple(values)


@pytest.mark.parametrize("split", [0, 1, 2, 4, 5])
def test_interrupted_resume_matches_uninterrupted_replay_exactly(
    split: int,
    tmp_path: Path,
) -> None:
    stream = candles()
    baseline_strategy = SyntheticResumeStrategy()
    baseline = replay_candles(baseline_strategy, stream)
    codec = SyntheticStateCodec()

    interrupted_strategy = SyntheticResumeStrategy()
    interrupted = interrupt_replay_candles(
        interrupted_strategy,
        stream,
        stop_after=split,
        codec=codec,
        config_fingerprint=CONFIG_FINGERPRINT,
        source_commit=SOURCE_COMMIT,
    )
    store = AtomicFileStateStore(tmp_path / f"state-{split}")
    save_checkpoint(store, "replay", interrupted.checkpoint)
    restored = load_checkpoint(store, "replay")
    assert restored is not None

    resumed_strategy = SyntheticResumeStrategy()
    resumed = resume_replay_candles(
        resumed_strategy,
        stream,
        checkpoint=restored,
        codec=codec,
        config_fingerprint=CONFIG_FINGERPRINT,
        source_commit=SOURCE_COMMIT,
    )

    prefix_ids = tuple(item.decision_id for item in interrupted.decisions)
    suffix_ids = tuple(item.decision_id for item in resumed.decisions)
    baseline_ids = tuple(item.decision_id for item in baseline.decisions)

    assert interrupted.manifest == baseline.manifest
    assert prefix_ids == baseline_ids[:split]
    assert suffix_ids == baseline_ids[split:]
    assert prefix_ids + suffix_ids == baseline_ids
    assert fingerprint_decision_ids(prefix_ids + suffix_ids) == baseline.decision_ids_fingerprint
    assert resumed.final_state == baseline.final_state
    assert codec.encode(resumed.final_state) == codec.encode(baseline.final_state)
    assert resumed.resumed_from_event_count == split
    assert resumed.execution_capability == "NONE"
    assert resumed.order_execution_enabled is False
    assert interrupted.execution_capability == "NONE"
    assert interrupted.order_execution_enabled is False


def test_resume_processes_suffix_only_and_is_idempotent() -> None:
    stream = candles()
    codec = SyntheticStateCodec()
    interrupted = interrupt_replay_candles(
        SyntheticResumeStrategy(),
        stream,
        stop_after=2,
        codec=codec,
        config_fingerprint=CONFIG_FINGERPRINT,
        source_commit=SOURCE_COMMIT,
    )

    first_strategy = SyntheticResumeStrategy()
    first = resume_replay_candles(
        first_strategy,
        stream,
        checkpoint=interrupted.checkpoint,
        codec=codec,
        config_fingerprint=CONFIG_FINGERPRINT,
        source_commit=SOURCE_COMMIT,
    )
    second_strategy = SyntheticResumeStrategy()
    second = resume_replay_candles(
        second_strategy,
        stream,
        checkpoint=interrupted.checkpoint,
        codec=codec,
        config_fingerprint=CONFIG_FINGERPRINT,
        source_commit=SOURCE_COMMIT,
    )

    expected_suffix_times = [item.close_time for item in stream[2:]]
    assert first_strategy.observed_close_times == expected_suffix_times
    assert second_strategy.observed_close_times == expected_suffix_times
    assert first == second
    assert len(first.decisions) == 3


def test_resume_rejects_full_stream_drift_before_processing_suffix() -> None:
    stream = candles()
    codec = SyntheticStateCodec()
    interrupted = interrupt_replay_candles(
        SyntheticResumeStrategy(),
        stream,
        stop_after=2,
        codec=codec,
        config_fingerprint=CONFIG_FINGERPRINT,
        source_commit=SOURCE_COMMIT,
    )
    drifted = list(stream)
    original = drifted[-1]
    drifted[-1] = Candle(
        instrument_id=original.instrument_id,
        timeframe=original.timeframe,
        event_time=original.event_time,
        close_time=original.close_time,
        open=original.open,
        high=original.high + 1.0,
        low=original.low,
        close=original.close,
        volume=original.volume,
        source=original.source,
        received_at=original.received_at,
        is_closed=original.is_closed,
        quality_state=original.quality_state,
    )
    strategy = SyntheticResumeStrategy()

    with pytest.raises(CheckpointCompatibilityError, match="run_fingerprint"):
        resume_replay_candles(
            strategy,
            tuple(drifted),
            checkpoint=interrupted.checkpoint,
            codec=codec,
            config_fingerprint=CONFIG_FINGERPRINT,
            source_commit=SOURCE_COMMIT,
        )
    assert strategy.observed_close_times == []


def test_resume_rejects_config_source_and_codec_drift_before_processing() -> None:
    stream = candles()
    codec = SyntheticStateCodec()
    interrupted = interrupt_replay_candles(
        SyntheticResumeStrategy(),
        stream,
        stop_after=2,
        codec=codec,
        config_fingerprint=CONFIG_FINGERPRINT,
        source_commit=SOURCE_COMMIT,
    )

    for kwargs, expected in (
        ({"config_fingerprint": sha256(b"other-config").hexdigest()}, "config_fingerprint"),
        ({"source_commit": "2" * 40}, "source_commit"),
    ):
        strategy = SyntheticResumeStrategy()
        values = {
            "config_fingerprint": CONFIG_FINGERPRINT,
            "source_commit": SOURCE_COMMIT,
        }
        values.update(kwargs)
        with pytest.raises(CheckpointCompatibilityError, match=expected):
            resume_replay_candles(
                strategy,
                stream,
                checkpoint=interrupted.checkpoint,
                codec=codec,
                **values,
            )
        assert strategy.observed_close_times == []

    class OtherCodec(SyntheticStateCodec):
        codec_id = "other-codec-v1"

    strategy = SyntheticResumeStrategy()
    with pytest.raises(CheckpointCompatibilityError, match="state_codec_id"):
        resume_replay_candles(
            strategy,
            stream,
            checkpoint=interrupted.checkpoint,
            codec=OtherCodec(),
            config_fingerprint=CONFIG_FINGERPRINT,
            source_commit=SOURCE_COMMIT,
        )
    assert strategy.observed_close_times == []


def test_resume_rejects_noncanonical_codec_round_trip() -> None:
    stream = candles()
    canonical = SyntheticStateCodec()
    interrupted = interrupt_replay_candles(
        SyntheticResumeStrategy(),
        stream,
        stop_after=2,
        codec=canonical,
        config_fingerprint=CONFIG_FINGERPRINT,
        source_commit=SOURCE_COMMIT,
    )

    with pytest.raises(CheckpointCompatibilityError, match="not codec-canonical"):
        resume_replay_candles(
            SyntheticResumeStrategy(),
            stream,
            checkpoint=interrupted.checkpoint,
            codec=NonCanonicalCodec(),
            config_fingerprint=CONFIG_FINGERPRINT,
            source_commit=SOURCE_COMMIT,
        )


def test_resume_rejects_validly_rebuilt_checkpoint_with_wrong_position_anchor() -> None:
    stream = candles()
    codec = SyntheticStateCodec()
    interrupted = interrupt_replay_candles(
        SyntheticResumeStrategy(),
        stream,
        stop_after=2,
        codec=codec,
        config_fingerprint=CONFIG_FINGERPRINT,
        source_commit=SOURCE_COMMIT,
    )
    item = interrupted.checkpoint
    wrong_anchor = build_product_checkpoint(
        engine_version=item.engine_version,
        run_fingerprint=item.run_fingerprint,
        strategy_id=item.strategy_id,
        strategy_version=item.strategy_version,
        strategy_fingerprint=item.strategy_fingerprint,
        config_fingerprint=item.config_fingerprint,
        source_commit=item.source_commit,
        instrument_id=item.instrument_id,
        timeframe=item.timeframe,
        total_event_count=item.total_event_count,
        input_fingerprint=item.input_fingerprint,
        processed_event_count=item.processed_event_count,
        last_event_time=stream[0].close_time,
        last_decision_id=item.last_decision_id,
        decision_ids_fingerprint=item.decision_ids_fingerprint,
        state_codec_id=item.state_codec_id,
        strategy_state=item.strategy_state_bytes,
    )

    with pytest.raises(CheckpointCompatibilityError, match="last_event_time"):
        resume_replay_candles(
            SyntheticResumeStrategy(),
            stream,
            checkpoint=wrong_anchor,
            codec=codec,
            config_fingerprint=CONFIG_FINGERPRINT,
            source_commit=SOURCE_COMMIT,
        )


def test_resume_module_has_no_runtime_adapter_mt5_or_execution_dependency() -> None:
    repo = Path(__file__).resolve().parents[1]
    module = repo / "src/daxlab/engine/resume.py"
    tree = ast.parse(module.read_text(encoding="utf-8"))
    imported: set[str] = set()
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
        elif isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)

    forbidden_imports = (
        "daxlab.runtime",
        "daxlab.adapters",
        "daxlab.domain.execution",
        "daxlab.strategies.cand001",
        "MetaTrader5",
    )
    assert not any(
        name == prefix or name.startswith(prefix + ".")
        for name in imported
        for prefix in forbidden_imports
    )
    assert "order_send" not in names
    assert "accept_intent" not in names
