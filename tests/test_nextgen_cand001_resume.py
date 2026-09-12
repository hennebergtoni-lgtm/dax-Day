from __future__ import annotations

import ast
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

import pytest

from daxlab.adapters.file_state_store import AtomicFileStateStore
from daxlab.domain.market import Candle, InstrumentId
from daxlab.engine.replay import fingerprint_decision_ids, replay_candles
from daxlab.engine.resume import interrupt_replay_candles, resume_replay_candles
from daxlab.runtime.candidate_pipeline import Cand001PipelineState
from daxlab.strategies.cand001 import (
    CAND001_STATE_CODEC_ID,
    CAND001_STATE_SCHEMA,
    Cand001PipelineStateCodec,
    Cand001StrategyBinding,
    Cand001StrategyPlugin,
)
from daxlab.state.replay_checkpoint import load_checkpoint, save_checkpoint


UTC = timezone.utc
INSTRUMENT = InstrumentId("DAX.CFD")
BINDING = Cand001StrategyBinding(instrument_id=INSTRUMENT, timeframe="M5")
SOURCE_COMMIT = "1" * 40


def bar(
    minute: int,
    *,
    open_price: float,
    high_price: float,
    low_price: float,
    close_price: float,
) -> Candle:
    event = datetime(2026, 9, 11, 7, minute, tzinfo=UTC)
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
        source="CAND001_RESUME_TEST",
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


def plugin() -> Cand001StrategyPlugin:
    return Cand001StrategyPlugin(binding=BINDING)


def config_fingerprint() -> str:
    return plugin().config.product_identity().fingerprint()


def test_initial_state_codec_has_frozen_explicit_schema() -> None:
    codec = Cand001PipelineStateCodec()
    encoded = codec.encode(Cand001PipelineState())

    assert codec.codec_id == CAND001_STATE_CODEC_ID
    assert encoded == (
        b'{"admission":{"session_date":null,"trades_admitted":0},'
        b'"schema_version":"DAXLAB_CAND001_PIPELINE_STATE_V1",'
        b'"signal":{"last_close_time_utc":null,"or_high":null,"or_low":null,'
        b'"or_slots":[],"session_date":null}}'
    )
    assert json.loads(encoded)["schema_version"] == CAND001_STATE_SCHEMA
    assert codec.decode(encoded) == Cand001PipelineState()


@pytest.mark.parametrize("split", [0, 1, 2, 3, 4, 5])
def test_real_cand001_resume_matches_uninterrupted_decisions_and_state(
    split: int,
    tmp_path: Path,
) -> None:
    stream = sequence()
    codec = Cand001PipelineStateCodec()
    baseline = replay_candles(plugin(), stream)
    interrupted = interrupt_replay_candles(
        plugin(),
        stream,
        stop_after=split,
        codec=codec,
        config_fingerprint=config_fingerprint(),
        source_commit=SOURCE_COMMIT,
    )

    store = AtomicFileStateStore(tmp_path / f"cand001-state-{split}")
    save_checkpoint(store, "candidate", interrupted.checkpoint)
    restored = load_checkpoint(store, "candidate")
    assert restored is not None

    resumed = resume_replay_candles(
        plugin(),
        stream,
        checkpoint=restored,
        codec=codec,
        config_fingerprint=config_fingerprint(),
        source_commit=SOURCE_COMMIT,
    )

    baseline_ids = tuple(item.decision_id for item in baseline.decisions)
    prefix_ids = tuple(item.decision_id for item in interrupted.decisions)
    suffix_ids = tuple(item.decision_id for item in resumed.decisions)

    assert interrupted.manifest == baseline.manifest
    assert prefix_ids == baseline_ids[:split]
    assert suffix_ids == baseline_ids[split:]
    assert prefix_ids + suffix_ids == baseline_ids
    assert fingerprint_decision_ids(prefix_ids + suffix_ids) == baseline.decision_ids_fingerprint
    assert resumed.final_state == baseline.final_state
    assert codec.encode(resumed.final_state) == codec.encode(baseline.final_state)
    assert resumed.execution_capability == "NONE"
    assert resumed.order_execution_enabled is False


def test_codec_preserves_opening_range_and_session_admission_state_exactly() -> None:
    stream = sequence()
    codec = Cand001PipelineStateCodec()
    interrupted = interrupt_replay_candles(
        plugin(),
        stream,
        stop_after=4,
        codec=codec,
        config_fingerprint=config_fingerprint(),
        source_commit=SOURCE_COMMIT,
    )
    state = interrupted.state
    restored = codec.decode(codec.encode(state))

    assert restored == state
    assert restored.signal.session_date == "2026-09-11"
    assert restored.signal.or_high == 103.0
    assert restored.signal.or_low == 98.0
    assert restored.signal.or_slots == ("09:00", "09:05", "09:10")
    assert restored.signal.last_close_time == datetime(2026, 9, 11, 7, 20, tzinfo=UTC)
    assert restored.admission.session_date == "2026-09-11"
    assert restored.admission.trades_admitted == 1


def test_codec_rejects_extra_fields_noncanonical_json_and_non_utc_timestamp() -> None:
    codec = Cand001PipelineStateCodec()
    interrupted = interrupt_replay_candles(
        plugin(),
        sequence(),
        stop_after=3,
        codec=codec,
        config_fingerprint=config_fingerprint(),
        source_commit=SOURCE_COMMIT,
    )
    canonical = codec.encode(interrupted.state)
    payload = json.loads(canonical)

    payload["extra"] = True
    with pytest.raises(ValueError, match="root field set mismatch"):
        codec.decode(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode())

    pretty = json.dumps(json.loads(canonical), sort_keys=True, indent=2).encode()
    with pytest.raises(ValueError, match="not canonical"):
        codec.decode(pretty)

    payload = json.loads(canonical)
    payload["signal"]["last_close_time_utc"] = "2026-09-11T09:15:00+02:00"
    shifted = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    with pytest.raises(ValueError, match="explicit UTC"):
        codec.decode(shifted)


def test_codec_rejects_state_invariant_corruption() -> None:
    codec = Cand001PipelineStateCodec()
    interrupted = interrupt_replay_candles(
        plugin(),
        sequence(),
        stop_after=3,
        codec=codec,
        config_fingerprint=config_fingerprint(),
        source_commit=SOURCE_COMMIT,
    )
    payload = json.loads(codec.encode(interrupted.state))

    payload["signal"]["or_slots"] = ["09:05", "09:00"]
    noncanonical_slots = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    with pytest.raises(ValueError, match="opening-range slots"):
        codec.decode(noncanonical_slots)

    payload = json.loads(codec.encode(interrupted.state))
    payload["admission"]["trades_admitted"] = -1
    negative_admission = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    with pytest.raises(ValueError, match="cannot be negative"):
        codec.decode(negative_admission)


def test_codec_surface_has_no_pickle_mt5_broker_or_execution_dependency() -> None:
    repo = Path(__file__).resolve().parents[1]
    module = repo / "src/daxlab/strategies/cand001/state_codec.py"
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

    forbidden = (
        "pickle",
        "cloudpickle",
        "MetaTrader5",
        "daxlab.runtime.mt5",
        "daxlab.runtime.broker",
        "daxlab.runtime.paper",
        "daxlab.domain.execution",
    )
    assert not any(
        name == prefix or name.startswith(prefix + ".")
        for name in imported
        for prefix in forbidden
    )
    assert "order_send" not in names
    assert "accept_intent" not in names
