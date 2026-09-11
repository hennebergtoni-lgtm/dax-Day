from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from daxlab.runtime.candidate_config import Cand001Config
from daxlab.runtime.candidate_shadow_host_cycle import run_cand001_shadow_host_cycle
from daxlab.runtime.candidate_sizing import Cand001SimulationSizingPolicy
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
