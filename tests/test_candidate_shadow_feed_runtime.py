from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from daxlab.runtime.atomic_json import atomic_write_json, read_json_object
from daxlab.runtime.candidate_active_trade_state import (
    candidate_active_trade_payload,
    parse_candidate_active_trade_payload,
)
from daxlab.runtime.candidate_config import Cand001Config
from daxlab.runtime.candidate_publication_state import (
    candidate_publication_state_payload,
    parse_candidate_publication_state_payload,
)
from daxlab.runtime.candidate_shadow_feed_runtime import run_cand001_shadow_from_mt5_feed
from daxlab.runtime.candidate_shadow_orchestrator import Cand001ShadowState
from daxlab.runtime.candidate_sizing import Cand001SimulationSizingPolicy
from daxlab.runtime.candidate_state import candidate_state_payload, parse_candidate_state_payload
from daxlab.runtime.contracts import RuntimeMode
from daxlab.runtime.manifests import RunManifest
from daxlab.runtime.mt5_feed_payload import ClosedM5Feed
from daxlab.runtime.mt5_readonly import Mt5Bar


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


def _feed(bars: tuple[Mt5Bar, ...], *, observed_at: datetime) -> ClosedM5Feed:
    latest_close = bars[-1].open_time + timedelta(minutes=5)
    return ClosedM5Feed(
        observed_at=observed_at,
        requested_start_pos=1,
        bars=bars,
        latest_closed_fingerprint="f" * 64,
        age_seconds=(observed_at - latest_close).total_seconds(),
        fresh=True,
        discontinuities=(),
        broker_timezone="Europe/Berlin",
        timestamp_interpretation="EXPLICIT_BROKER_WALL_CLOCK",
    )


def _manifest(config: Cand001Config, sizing: Cand001SimulationSizingPolicy) -> RunManifest:
    return RunManifest.build(
        dataset_fingerprint="d" * 64,
        engine_fingerprint="e" * 64,
        config={"candidate": config, "sizing": sizing},
        mode=RuntimeMode.SHADOW,
    )


def test_overlapping_mt5_feed_restart_matches_continuous_outcome(tmp_path) -> None:
    bars = _bars()
    config = Cand001Config()
    sizing = Cand001SimulationSizingPolicy()
    manifest = _manifest(config, sizing)

    full_observed = bars[-1].open_time + timedelta(minutes=5, seconds=1)
    continuous = run_cand001_shadow_from_mt5_feed(
        Cand001ShadowState(),
        _feed(bars, observed_at=full_observed),
        broker_symbol="DE40",
        run_manifest=manifest,
        config=config,
        sizing=sizing,
    )
    assert continuous.latest_step is not None
    assert continuous.latest_step.outcome_to_publish is not None

    first_bars = bars[:5]
    first_observed = first_bars[-1].open_time + timedelta(minutes=5, seconds=1)
    first = run_cand001_shadow_from_mt5_feed(
        Cand001ShadowState(),
        _feed(first_bars, observed_at=first_observed),
        broker_symbol="DE40",
        run_manifest=manifest,
        config=config,
        sizing=sizing,
    )
    assert first.state.active_trade is not None

    pipeline_path = tmp_path / "pipeline.json"
    active_path = tmp_path / "active.json"
    publication_path = tmp_path / "publication.json"
    atomic_write_json(pipeline_path, candidate_state_payload(first.state.pipeline, config=config))
    atomic_write_json(active_path, candidate_active_trade_payload(first.state.active_trade))
    atomic_write_json(publication_path, candidate_publication_state_payload(first.state.publication))

    restored = Cand001ShadowState(
        pipeline=parse_candidate_state_payload(read_json_object(pipeline_path), config=config),
        active_trade=parse_candidate_active_trade_payload(read_json_object(active_path)),
        publication=parse_candidate_publication_state_payload(read_json_object(publication_path)),
    )
    resumed = run_cand001_shadow_from_mt5_feed(
        restored,
        _feed(bars, observed_at=full_observed),
        broker_symbol="DE40",
        run_manifest=manifest,
        config=config,
        sizing=sizing,
    )

    assert resumed.overlap_filtered_bar_count == 5
    assert resumed.processed_bar_count == 1
    assert resumed.latest_step is not None
    assert resumed.latest_step.outcome_to_publish is not None
    assert resumed.latest_step.outcome_to_publish.outcome_id == continuous.latest_step.outcome_to_publish.outcome_id
    assert resumed.latest_step.outcome_to_publish.net_r == continuous.latest_step.outcome_to_publish.net_r
    assert resumed.state.publication == continuous.state.publication
    assert resumed.state.active_trade is None
    assert resumed.execution_capability == "NONE"
    assert resumed.order_execution_enabled is False
