from __future__ import annotations

import ast
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path

import pytest

from daxlab.adapters.file_state_store import AtomicFileStateStore
from daxlab.domain.market import Candle, InstrumentId
from daxlab.domain.strategy import StrategyDecision
from daxlab.engine.replay import ENGINE_VERSION, replay_candles
from daxlab.state.replay_checkpoint import (
    CheckpointCompatibilityError,
    assert_checkpoint_compatible,
    build_product_checkpoint,
    checkpoint_from_bytes,
    checkpoint_to_bytes,
    load_checkpoint,
    save_checkpoint,
)
from daxlab.strategies.contracts import StrategyTransition


UTC = timezone.utc
INSTRUMENT = InstrumentId("DAX.CFD")
CONFIG_FINGERPRINT = sha256(b"checkpoint-config").hexdigest()
SOURCE_COMMIT = "1" * 40
STATE_CODEC_ID = "synthetic-json-v1"


class SyntheticStateStrategy:
    strategy_id = "SYNTHETIC-CHECKPOINT"
    strategy_version = "1"
    strategy_fingerprint = sha256(b"synthetic-checkpoint-strategy").hexdigest()

    def initial_state(self) -> int:
        return 0

    def on_candle(self, state: int, candle: Candle) -> StrategyTransition[int]:
        decision = StrategyDecision.no_trade(
            strategy_id=self.strategy_id,
            strategy_version=self.strategy_version,
            strategy_fingerprint=self.strategy_fingerprint,
            event_time=candle.close_time,
            instrument_id=candle.instrument_id,
            reason_codes=("CHECKPOINT_FIXTURE",),
        )
        return StrategyTransition(state=state + 1, decision=decision)


class MemoryStore:
    def __init__(self) -> None:
        self.values: dict[str, bytes] = {}

    def load(self, key: str) -> bytes | None:
        return self.values.get(key)

    def save(self, key: str, payload: bytes) -> None:
        self.values[key] = payload


def candles() -> tuple[Candle, ...]:
    values: list[Candle] = []
    for minute, close in ((0, 100.0), (5, 101.0), (10, 102.0)):
        event_time = datetime(2026, 9, 10, 8, minute, tzinfo=UTC)
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
                source="CHECKPOINT_FIXTURE",
                received_at=close_time + timedelta(seconds=1),
                is_closed=True,
            )
        )
    return tuple(values)


def checkpoint():
    result = replay_candles(SyntheticStateStrategy(), candles())
    manifest = result.manifest
    strategy_state = json.dumps(
        {"processed": result.final_state},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return build_product_checkpoint(
        engine_version=manifest.engine_version,
        run_fingerprint=manifest.run_fingerprint,
        strategy_id=manifest.strategy_id,
        strategy_version=manifest.strategy_version,
        strategy_fingerprint=manifest.strategy_fingerprint,
        config_fingerprint=CONFIG_FINGERPRINT,
        source_commit=SOURCE_COMMIT,
        instrument_id=manifest.instrument_id.value,
        timeframe=manifest.timeframe,
        total_event_count=manifest.candle_count,
        input_fingerprint=manifest.input_fingerprint,
        processed_event_count=manifest.candle_count,
        last_event_time=result.last_close_time,
        last_decision_id=result.decisions[-1].decision_id,
        decision_ids_fingerprint=result.decision_ids_fingerprint,
        state_codec_id=STATE_CODEC_ID,
        strategy_state=strategy_state,
    )


def compatibility_kwargs() -> dict[str, object]:
    item = checkpoint()
    return {
        "engine_version": item.engine_version,
        "run_fingerprint": item.run_fingerprint,
        "strategy_id": item.strategy_id,
        "strategy_version": item.strategy_version,
        "strategy_fingerprint": item.strategy_fingerprint,
        "config_fingerprint": item.config_fingerprint,
        "source_commit": item.source_commit,
        "instrument_id": item.instrument_id,
        "timeframe": item.timeframe,
        "total_event_count": item.total_event_count,
        "input_fingerprint": item.input_fingerprint,
        "state_codec_id": item.state_codec_id,
    }


def test_checkpoint_binds_real_replay_identity_and_opaque_state_bytes() -> None:
    item = checkpoint()

    assert item.engine_version == ENGINE_VERSION
    assert item.strategy_id == SyntheticStateStrategy.strategy_id
    assert item.instrument_id == "DAX.CFD"
    assert item.timeframe == "M5"
    assert item.total_event_count == 3
    assert item.processed_event_count == 3
    assert item.last_event_time == datetime(2026, 9, 10, 8, 15, tzinfo=UTC)
    assert item.strategy_state_bytes == b'{"processed":3}'
    assert len(item.strategy_state_sha256) == 64
    assert len(item.checkpoint_fingerprint) == 64
    assert item.execution_capability == "NONE"
    assert item.order_execution_enabled is False


def test_checkpoint_serialization_and_state_store_round_trip_are_deterministic(tmp_path: Path) -> None:
    first = checkpoint()
    second = checkpoint()

    assert first == second
    assert checkpoint_to_bytes(first) == checkpoint_to_bytes(second)

    memory = MemoryStore()
    assert load_checkpoint(memory, "run-state") is None
    save_checkpoint(memory, "run-state", first)
    assert load_checkpoint(memory, "run-state") == first

    file_store = AtomicFileStateStore(tmp_path / "state")
    save_checkpoint(file_store, "run-state", first)
    assert load_checkpoint(file_store, "run-state") == first


def test_persisted_payload_fails_closed_on_state_or_metadata_tampering() -> None:
    item = checkpoint()
    encoded = checkpoint_to_bytes(item)
    payload = json.loads(encoded)

    payload["strategy_state_b64"] = "dGFtcGVyZWQ="
    tampered_state = (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode()
    with pytest.raises(ValueError, match="strategy state sha256 mismatch"):
        checkpoint_from_bytes(tampered_state)

    payload = json.loads(encoded)
    payload["processed_event_count"] = 2
    tampered_metadata = (
        json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode()
    with pytest.raises(ValueError, match="checkpoint fingerprint mismatch"):
        checkpoint_from_bytes(tampered_metadata)

    payload = json.loads(encoded)
    payload["unexpected"] = True
    unexpected = (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode()
    with pytest.raises(ValueError, match="field set mismatch"):
        checkpoint_from_bytes(unexpected)


def test_resume_compatibility_rejects_every_material_identity_drift() -> None:
    item = checkpoint()
    expected = compatibility_kwargs()
    assert_checkpoint_compatible(item, **expected)  # type: ignore[arg-type]

    drifts: tuple[tuple[str, object], ...] = (
        ("engine_version", "OTHER_ENGINE"),
        ("run_fingerprint", sha256(b"run").hexdigest()),
        ("strategy_id", "OTHER"),
        ("strategy_version", "2"),
        ("strategy_fingerprint", sha256(b"strategy").hexdigest()),
        ("config_fingerprint", sha256(b"config").hexdigest()),
        ("source_commit", "2" * 40),
        ("instrument_id", "OTHER.INSTRUMENT"),
        ("timeframe", "M15"),
        ("total_event_count", 4),
        ("input_fingerprint", sha256(b"input").hexdigest()),
        ("state_codec_id", "other-codec-v1"),
    )
    for field_name, value in drifts:
        changed = dict(expected)
        changed[field_name] = value
        with pytest.raises(CheckpointCompatibilityError, match=field_name):
            assert_checkpoint_compatible(item, **changed)  # type: ignore[arg-type]


def test_checkpoint_progress_and_time_invariants_fail_closed() -> None:
    item = checkpoint()
    common = {
        "engine_version": item.engine_version,
        "run_fingerprint": item.run_fingerprint,
        "strategy_id": item.strategy_id,
        "strategy_version": item.strategy_version,
        "strategy_fingerprint": item.strategy_fingerprint,
        "config_fingerprint": item.config_fingerprint,
        "source_commit": item.source_commit,
        "instrument_id": item.instrument_id,
        "timeframe": item.timeframe,
        "total_event_count": item.total_event_count,
        "input_fingerprint": item.input_fingerprint,
        "decision_ids_fingerprint": item.decision_ids_fingerprint,
        "state_codec_id": item.state_codec_id,
        "strategy_state": item.strategy_state_bytes,
    }

    with pytest.raises(ValueError, match="timezone-aware"):
        build_product_checkpoint(
            **common,
            processed_event_count=1,
            last_event_time=datetime(2026, 9, 10, 8, 5),
            last_decision_id=item.last_decision_id,
        )
    with pytest.raises(ValueError, match="outside run bounds"):
        build_product_checkpoint(
            **common,
            processed_event_count=4,
            last_event_time=item.last_event_time,
            last_decision_id=item.last_decision_id,
        )
    with pytest.raises(ValueError, match="zero-progress"):
        build_product_checkpoint(
            **common,
            processed_event_count=0,
            last_event_time=item.last_event_time,
            last_decision_id=item.last_decision_id,
        )
    with pytest.raises(ValueError, match="requires last-event"):
        build_product_checkpoint(
            **common,
            processed_event_count=1,
            last_event_time=None,
            last_decision_id=None,
        )


def test_zero_progress_checkpoint_is_valid_when_event_identity_is_absent() -> None:
    item = checkpoint()
    zero = build_product_checkpoint(
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
        processed_event_count=0,
        last_event_time=None,
        last_decision_id=None,
        decision_ids_fingerprint=sha256(b"zero-decisions").hexdigest(),
        state_codec_id=item.state_codec_id,
        strategy_state=b"",
    )

    assert zero.processed_event_count == 0
    assert zero.last_event_time is None
    assert zero.last_decision_id is None
    assert zero.strategy_state_bytes == b""


def test_checkpoint_object_rejects_safety_or_state_tampering() -> None:
    item = checkpoint()

    with pytest.raises(ValueError, match="cannot authorize execution"):
        replace(item, order_execution_enabled=True)
    with pytest.raises(ValueError, match="strategy state sha256 mismatch"):
        replace(item, strategy_state_b64="dGFtcGVyZWQ=")
    with pytest.raises(ValueError, match="checkpoint fingerprint mismatch"):
        replace(item, decision_ids_fingerprint=sha256(b"other-decisions").hexdigest())


def test_checkpoint_module_has_no_engine_runtime_candidate_mt5_or_execution_dependency() -> None:
    repo = Path(__file__).resolve().parents[1]
    module = repo / "src/daxlab/state/replay_checkpoint.py"
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
        "daxlab.engine",
        "daxlab.runtime",
        "daxlab.adapters",
        "daxlab.strategies.cand001",
        "daxlab.domain.execution",
        "MetaTrader5",
    )
    assert not any(
        name == prefix or name.startswith(prefix + ".")
        for name in imported
        for prefix in forbidden_imports
    )
    assert "order_send" not in names
    assert "accept_intent" not in names
