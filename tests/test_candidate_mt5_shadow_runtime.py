from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from daxlab.runtime.candidate_config import Cand001Config
from daxlab.runtime.candidate_mt5_shadow_runtime import run_cand001_mt5_shadow
from daxlab.runtime.candidate_shadow_orchestrator import Cand001ShadowState
from daxlab.runtime.candidate_sizing import Cand001SimulationSizingPolicy
from daxlab.runtime.contracts import RuntimeMode
from daxlab.runtime.manifests import RunManifest
from daxlab.runtime.mt5_feed_payload import ClosedM5Feed
from daxlab.runtime.mt5_host_contract import Mt5HostObservation
from daxlab.runtime.mt5_readonly import BrokerSymbol, Mt5Bar
from daxlab.runtime.mt5_windows_bundle import WindowsMt5Bundle
from daxlab.runtime.prospective_gate import ProspectiveAuthorization


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


def _bundle() -> WindowsMt5Bundle:
    bars = _bars()
    observed = bars[-1].open_time + timedelta(minutes=5, seconds=1)
    latest_close = bars[-1].open_time + timedelta(minutes=5)
    feed = ClosedM5Feed(
        observed_at=observed,
        requested_start_pos=1,
        bars=bars,
        latest_closed_fingerprint="f" * 64,
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
        fingerprint="1" * 64,
        blockers=(),
    )


def _authorization() -> ProspectiveAuthorization:
    return ProspectiveAuthorization(
        gate_id="STEP_91_USER_AUTHORIZATION",
        shadow_authorized=True,
        paper_authorized=False,
        live_authorized=False,
    )


def _manifest(config: Cand001Config, sizing: Cand001SimulationSizingPolicy) -> RunManifest:
    return RunManifest.build(
        dataset_fingerprint="d" * 64,
        engine_fingerprint="e" * 64,
        config={"candidate": config, "sizing": sizing},
        mode=RuntimeMode.SHADOW,
    )


def test_green_existing_mt5_gate_allows_candidate_shadow_processing() -> None:
    config = Cand001Config()
    sizing = Cand001SimulationSizingPolicy()
    result = run_cand001_mt5_shadow(
        Cand001ShadowState(),
        _bundle(),
        authorization=_authorization(),
        single_instance_lock_held=True,
        run_manifest=_manifest(config, sizing),
        config=config,
        sizing=sizing,
    )

    assert result.gate.allowed is True
    assert result.host_status.status == "GREEN"
    assert result.candidate_feed_result is not None
    assert result.candidate_feed_result.processed_bar_count == 6
    assert result.candidate_feed_result.latest_step is not None
    assert result.candidate_feed_result.latest_step.outcome_to_publish is not None
    snapshot = result.candidate_feed_result.latest_step.operator_snapshot.as_dict()
    assert snapshot["runtime"]["health_source"] == "MT5_SHADOW_HOST"
    assert snapshot["safety"]["execution_capability"] == "NONE"
    assert snapshot["safety"]["order_execution_enabled"] is False
    assert result.execution_capability == "NONE"
    assert result.order_execution_enabled is False


def test_existing_mt5_gate_blocks_candidate_when_single_instance_lock_missing() -> None:
    config = Cand001Config()
    sizing = Cand001SimulationSizingPolicy()
    initial = Cand001ShadowState()
    result = run_cand001_mt5_shadow(
        initial,
        _bundle(),
        authorization=_authorization(),
        single_instance_lock_held=False,
        run_manifest=_manifest(config, sizing),
        config=config,
        sizing=sizing,
    )

    assert result.gate.allowed is False
    assert "SINGLE_INSTANCE_LOCK_NOT_HELD" in result.gate.blockers
    assert result.candidate_feed_result is None
    assert result.state == initial
