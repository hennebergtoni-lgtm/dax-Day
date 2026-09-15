from copy import deepcopy
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from daxlab.runtime.atomic_json import atomic_write_json, read_json_object
from daxlab.runtime.candidate_config import Cand001Config
from daxlab.runtime.candidate_shadow_checkpoint import (
    candidate_shadow_checkpoint_payload,
    parse_candidate_shadow_checkpoint_payload,
)
from daxlab.runtime.candidate_shadow_orchestrator import (
    Cand001ShadowState,
    process_cand001_shadow_candle,
)
from daxlab.runtime.candidate_sizing import Cand001SimulationSizingPolicy
from daxlab.runtime.contracts import Candle, RuntimeMode
from daxlab.runtime.decision import stable_fingerprint
from daxlab.runtime.manifests import RunManifest


BERLIN = ZoneInfo("Europe/Berlin")


def _manifest(config: Cand001Config, sizing: Cand001SimulationSizingPolicy, marker: str = "d") -> RunManifest:
    return RunManifest.build(
        dataset_fingerprint=marker * 64,
        engine_fingerprint="e" * 64,
        config={"candidate": config, "sizing": sizing},
        mode=RuntimeMode.SHADOW,
    )


def _candle(minute: int, *, open_: float, high: float, low: float, close: float) -> Candle:
    event = datetime(2026, 9, 11, 9, minute, tzinfo=BERLIN)
    return Candle(
        symbol="DE40",
        timeframe="5m",
        event_time=event,
        close_time=event + timedelta(minutes=5),
        open=open_,
        high=high,
        low=low,
        close=close,
        volume=None,
        source="TEST",
        received_at=event + timedelta(minutes=5, seconds=1),
        is_closed=True,
    )


def _open_state(config: Cand001Config, sizing: Cand001SimulationSizingPolicy, manifest: RunManifest) -> Cand001ShadowState:
    state = Cand001ShadowState()
    bars = (
        _candle(0, open_=100.0, high=102.0, low=99.0, close=101.0),
        _candle(5, open_=101.0, high=103.0, low=100.0, close=102.0),
        _candle(10, open_=102.0, high=103.0, low=98.0, close=101.0),
        _candle(15, open_=101.0, high=105.0, low=100.0, close=104.0),
        _candle(20, open_=104.0, high=108.0, low=101.0, close=106.0),
    )
    for candle in bars:
        state = process_cand001_shadow_candle(
            state,
            candle,
            observed_at=candle.received_at,
            run_manifest=manifest,
            config=config,
            sizing=sizing,
        ).state
    assert state.active_trade is not None
    return state


def test_complete_shadow_checkpoint_roundtrip_is_exact(tmp_path) -> None:
    config = Cand001Config()
    sizing = Cand001SimulationSizingPolicy()
    manifest = _manifest(config, sizing)
    state = _open_state(config, sizing, manifest)
    path = tmp_path / "candidate_shadow_state.json"

    atomic_write_json(
        path,
        candidate_shadow_checkpoint_payload(state, run_manifest=manifest, config=config),
    )
    restored = parse_candidate_shadow_checkpoint_payload(
        read_json_object(path),
        run_manifest=manifest,
        config=config,
    )

    assert restored == state
    assert restored.execution_capability == "NONE"
    assert restored.order_execution_enabled is False


def test_checkpoint_rejects_different_run_manifest() -> None:
    config = Cand001Config()
    sizing = Cand001SimulationSizingPolicy()
    manifest = _manifest(config, sizing)
    state = _open_state(config, sizing, manifest)
    payload = candidate_shadow_checkpoint_payload(state, run_manifest=manifest, config=config)
    different = _manifest(config, sizing, marker="c")

    with pytest.raises(ValueError, match="run-manifest drift"):
        parse_candidate_shadow_checkpoint_payload(
            payload,
            run_manifest=different,
            config=config,
        )


def test_checkpoint_rejects_rehashed_nested_publication_tamper() -> None:
    config = Cand001Config()
    sizing = Cand001SimulationSizingPolicy()
    manifest = _manifest(config, sizing)
    state = _open_state(config, sizing, manifest)
    payload = deepcopy(
        candidate_shadow_checkpoint_payload(state, run_manifest=manifest, config=config)
    )
    payload["publication_state"]["published_intent_ids"] = []
    payload.pop("payload_fingerprint")
    payload["payload_fingerprint"] = stable_fingerprint(payload)

    with pytest.raises(ValueError, match="publication-state payload fingerprint mismatch"):
        parse_candidate_shadow_checkpoint_payload(
            payload,
            run_manifest=manifest,
            config=config,
        )
