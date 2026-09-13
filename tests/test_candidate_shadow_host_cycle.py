from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timedelta
import json
from unittest.mock import Mock
from zoneinfo import ZoneInfo

import pytest

from daxlab.runtime.candidate_config import Cand001Config
from daxlab.runtime.candidate_shadow_host_cycle import run_cand001_shadow_host_cycle
from daxlab.runtime.candidate_shadow_checkpoint import (
    candidate_shadow_checkpoint_payload,
    parse_candidate_shadow_checkpoint_payload,
)
from daxlab.runtime.candidate_mt5_feed import mt5_bar_to_candidate_candle
from daxlab.runtime.candidate_sizing import Cand001SimulationSizingPolicy
from daxlab.runtime.candidate_virtual_lifecycle import advance_cand001_virtual_lifecycle
from daxlab.runtime.decision import stable_fingerprint
from daxlab.runtime.mt5_feed_payload import ClosedM5Feed
from daxlab.runtime.mt5_host_contract import Mt5HostObservation
from daxlab.runtime.mt5_readonly import BrokerSymbol, Mt5Bar
from daxlab.runtime.mt5_windows_bundle import WindowsMt5Bundle


BERLIN = ZoneInfo("Europe/Berlin")


def _bars() -> tuple[Mt5Bar, ...]:
    values = (
        (9, 0, 100.0, 102.0, 99.0, 101.0),
        (9, 5, 101.0, 103.0, 100.0, 102.0),
        (9, 10, 102.0, 103.0, 98.0, 101.0),
        (9, 15, 101.0, 105.0, 100.0, 104.0),
        (9, 20, 104.0, 108.0, 101.0, 106.0),
        (9, 25, 106.0, 114.0, 103.0, 113.0),
    )
    return tuple(
        Mt5Bar(
            open_time=datetime(2026, 9, 11, hour, minute, tzinfo=BERLIN),
            open=open_,
            high=high,
            low=low,
            close=close,
        )
        for hour, minute, open_, high, low, close in values
    )


def _bundle(bars: tuple[Mt5Bar, ...], *, marker: str) -> WindowsMt5Bundle:
    observed = bars[-1].open_time + timedelta(minutes=5, seconds=1)
    latest_close = bars[-1].open_time + timedelta(minutes=5)
    feed = ClosedM5Feed(
        observed_at=observed,
        requested_start_pos=1,
        bars=bars,
        latest_closed_fingerprint=marker * 64,
        age_seconds=(observed - latest_close).total_seconds(),
        fresh=True,
        discontinuities=(),
        broker_timezone="Europe/Berlin",
        timestamp_interpretation="EXPLICIT_BROKER_WALL_CLOCK",
    )
    host = Mt5HostObservation(
        observed_at=observed,
        terminal_connected=True,
        account_connected=True,
        account_trade_allowed=True,
        order_execution_enabled=False,
        engine_loop_healthy=True,
        clock_ok=True,
        symbols=(
            BrokerSymbol(
                name="DE40",
                digits=2,
                point=0.01,
                trade_mode="DISABLED",
                contract_size=1.0,
            ),
        ),
    )
    return WindowsMt5Bundle(
        host=host,
        feed=feed,
        symbol_resolution_state="CONFIGURED_EXACT_DATA_ONLY",
        fingerprint=marker * 64,
        blockers=(),
    )


def test_host_cycle_manifest_is_stable_and_checkpoint_resumes_open_trade() -> None:
    bars = _bars()
    config = Cand001Config()
    sizing = Cand001SimulationSizingPolicy()

    first = run_cand001_shadow_host_cycle(
        _bundle(bars[:5], marker="1"),
        single_instance_lock_held=True,
        config=config,
        sizing=sizing,
    )
    assert first.runtime.state.active_trade is not None
    assert len(first.intents_to_publish) == 1
    assert not first.outcomes_to_publish

    resumed = run_cand001_shadow_host_cycle(
        _bundle(bars, marker="2"),
        single_instance_lock_held=True,
        checkpoint_payload=first.checkpoint_payload,
        config=config,
        sizing=sizing,
    )

    assert resumed.manifest.manifest_fingerprint == first.manifest.manifest_fingerprint
    assert resumed.runtime.candidate_feed_result is not None
    assert resumed.runtime.candidate_feed_result.overlap_filtered_bar_count == 5
    assert resumed.runtime.candidate_feed_result.processed_bar_count == 1
    assert resumed.runtime.state.active_trade is None
    assert not resumed.intents_to_publish
    assert len(resumed.outcomes_to_publish) == 1
    assert resumed.latest_operator_snapshot is not None
    assert resumed.latest_operator_snapshot.outcome_id == resumed.outcomes_to_publish[0].outcome_id
    assert resumed.execution_capability == "NONE"
    assert resumed.order_execution_enabled is False


def _rehash(payload):
    payload.pop("payload_fingerprint")
    payload["payload_fingerprint"] = stable_fingerprint(payload)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
@pytest.mark.parametrize("fields", [("or_high",), ("or_low",), ("or_high", "or_low")])
def test_complete_checkpoint_rejects_non_finite_or_and_never_runs_strategy(value, fields, monkeypatch):
    bars = _bars()
    first = run_cand001_shadow_host_cycle(_bundle(bars[:3], marker="1"), single_instance_lock_held=True)
    payload = deepcopy(first.checkpoint_payload)
    pipeline = payload["pipeline_state"]
    pipeline["state"]["signal"].update(dict.fromkeys(fields, value))
    _rehash(pipeline)
    _rehash(payload)
    wire_payload = json.loads(json.dumps(payload))

    with pytest.raises(ValueError, match=rf"signal\.{fields[0]} must be finite"):
        parse_candidate_shadow_checkpoint_payload(wire_payload, run_manifest=first.manifest)

    strategy = Mock(side_effect=AssertionError("strategy reached before restore rejection"))
    monkeypatch.setattr("daxlab.runtime.candidate_shadow_host_cycle.run_cand001_mt5_shadow", strategy)
    # Include the next valid breakout candle: rejection must precede any runtime processing.
    with pytest.raises(ValueError, match=rf"signal\.{fields[0]} must be finite"):
        run_cand001_shadow_host_cycle(
            _bundle(bars[:4], marker="2"), single_instance_lock_held=True,
            checkpoint_payload=wire_payload,
        )
    strategy.assert_not_called()


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
@pytest.mark.parametrize("fields", [("or_high",), ("or_low",), ("or_high", "or_low")])
def test_complete_checkpoint_writer_rejects_preexisting_invalid_or(value, fields):
    first = run_cand001_shadow_host_cycle(_bundle(_bars()[:3], marker="1"), single_instance_lock_held=True)
    for field in fields:
        object.__setattr__(first.runtime.state.pipeline.signal, field, value)
    with pytest.raises(ValueError, match=rf"signal\.{fields[0]} must be finite"):
        candidate_shadow_checkpoint_payload(first.runtime.state, run_manifest=first.manifest)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
@pytest.mark.parametrize("field", [
    "quantity", "requested_price", "stop_price", "target_price", "filled_price", "exit_price",
])
def test_complete_checkpoint_rejects_non_finite_lifecycle_fields(value, field, monkeypatch):
    bars = _bars()
    first = run_cand001_shadow_host_cycle(_bundle(bars[:5], marker="1"), single_instance_lock_held=True)
    active = first.runtime.state.active_trade
    assert active is not None
    next_bar = mt5_bar_to_candidate_candle(
        bars[-1], broker_symbol="DE40", observed_at=bars[-1].open_time + timedelta(minutes=5, seconds=1),
    )
    closed = advance_cand001_virtual_lifecycle(active.lifecycle, next_bar)
    state = replace(first.runtime.state, active_trade=replace(active, lifecycle=closed))
    payload = candidate_shadow_checkpoint_payload(state, run_manifest=first.manifest)
    virtual = payload["active_trade"]["virtual_lifecycle"]
    virtual["lifecycle"][field] = value
    _rehash(virtual)
    _rehash(payload["active_trade"])
    _rehash(payload)
    with pytest.raises(ValueError, match=rf"{field} must be finite"):
        parse_candidate_shadow_checkpoint_payload(
            json.loads(json.dumps(payload)), run_manifest=first.manifest,
        )
    strategy = Mock(side_effect=AssertionError("invalid lifecycle reached runtime"))
    monkeypatch.setattr("daxlab.runtime.candidate_shadow_host_cycle.run_cand001_mt5_shadow", strategy)
    with pytest.raises(ValueError, match=rf"{field} must be finite"):
        run_cand001_shadow_host_cycle(
            _bundle(bars, marker="2"), single_instance_lock_held=True, checkpoint_payload=payload,
        )
    strategy.assert_not_called()

    bad_state = replace(state, active_trade=replace(active, lifecycle=replace(closed, **{field: value})))
    with pytest.raises(ValueError, match=rf"{field} must be finite"):
        candidate_shadow_checkpoint_payload(bad_state, run_manifest=first.manifest)


@pytest.mark.parametrize(("count", "prior_fingerprint"), [
    (3, "edb7642dcad7ef3d0e85eee63555b12b147959436d1f6cddaecf0ecd1e84c217"),
    (4, "05df854dac529729df982d41ed36b413130aeb9b997d660b7025069fdd134f67"),
    (5, "8eceffb2c312920c3f61ab64a54a605b4b8b919de0d0ebbcefcd39c084192ef4"),
    (6, "12cf28bf4ac7500be342ffed7c8dcc5fdec6453f1130908db44127bff4e2c94c"),
])
def test_valid_checkpoint_preserves_prior_fingerprint_and_restart_parity(count, prior_fingerprint):
    # Captured at 643e6741da601cce708fa301a90664e4a5137149: OR, pending, open, completed.
    bars = _bars()
    first = run_cand001_shadow_host_cycle(_bundle(bars[:count], marker="1"), single_instance_lock_held=True)
    assert first.checkpoint_payload["payload_fingerprint"] == prior_fingerprint
    checkpoint = json.loads(json.dumps(first.checkpoint_payload, allow_nan=False))
    restored = parse_candidate_shadow_checkpoint_payload(checkpoint, run_manifest=first.manifest)
    assert restored == first.runtime.state
    assert candidate_shadow_checkpoint_payload(restored, run_manifest=first.manifest) == checkpoint

    resumed = run_cand001_shadow_host_cycle(
        _bundle(bars, marker="2"), single_instance_lock_held=True, checkpoint_payload=checkpoint,
    )
    uninterrupted = run_cand001_shadow_host_cycle(_bundle(bars, marker="2"), single_instance_lock_held=True)
    assert resumed.runtime.state == uninterrupted.runtime.state
    assert resumed.checkpoint_payload == uninterrupted.checkpoint_payload
    assert first.intents_to_publish + resumed.intents_to_publish == uninterrupted.intents_to_publish
    assert first.outcomes_to_publish + resumed.outcomes_to_publish == uninterrupted.outcomes_to_publish
    assert resumed.execution_capability == "NONE"
    assert resumed.order_execution_enabled is False
