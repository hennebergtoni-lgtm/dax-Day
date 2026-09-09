from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from daxlab.reference.recovered_engine import load_exact_candidate_engine
from daxlab.runtime.contracts import Candle, DataQualityState, RuntimeMode
from daxlab.runtime.manifests import RunManifest
from daxlab.runtime.mt5_readonly import Mt5Bar
from daxlab.runtime.shadow_soak import bar_fingerprint, run_shadow_soak
from daxlab.runtime.v112_bridge import run_replay_days, v112_results_fingerprint

BERLIN = ZoneInfo("Europe/Berlin")


def to_candle(bar: Mt5Bar) -> Candle:
    return Candle(
        symbol="DAX",
        timeframe="5m",
        event_time=bar.open_time,
        close_time=bar.open_time + timedelta(minutes=5),
        open=bar.open,
        high=bar.high,
        low=bar.low,
        close=bar.close,
        volume=None,
        source="synthetic-soak",
        received_at=bar.open_time + timedelta(minutes=5, seconds=1),
        is_closed=True,
        quality_state=DataQualityState.OK,
    )


def session(day: datetime) -> tuple[Mt5Bar, ...]:
    start = day.replace(hour=9, minute=0, second=0, microsecond=0)
    return tuple(
        Mt5Bar(
            open_time=start + timedelta(minutes=5 * index),
            open=16000.0 + index * 0.1,
            high=16001.0 + index * 0.1,
            low=15999.0 + index * 0.1,
            close=16000.5 + index * 0.1,
        )
        for index in range(103)
    )


def test_synthetic_bars_convert_to_safe_runtime_candles() -> None:
    source = session(datetime(2026, 1, 5, tzinfo=BERLIN))
    candles = tuple(to_candle(bar) for bar in source)
    assert len(candles) == 103
    assert all(candle.safe_for_decision for candle in candles)
    assert candles[0].event_time.astimezone(BERLIN).strftime("%H:%M") == "09:00"
    assert candles[-1].event_time.astimezone(BERLIN).strftime("%H:%M") == "17:30"


def test_winter_and_summer_berlin_session_offsets() -> None:
    winter = session(datetime(2026, 1, 5, tzinfo=BERLIN))[0]
    summer = session(datetime(2026, 6, 5, tzinfo=BERLIN))[0]
    assert winter.open_time.utcoffset() == timedelta(hours=1)
    assert summer.open_time.utcoffset() == timedelta(hours=2)


def test_dst_boundary_soak_remains_deterministic() -> None:
    before = session(datetime(2026, 3, 27, tzinfo=BERLIN))[-3:]
    after = session(datetime(2026, 3, 30, tzinfo=BERLIN))[:3]
    first = run_shadow_soak(before + after)
    second = run_shadow_soak(before + after)
    assert first == second
    assert first.processed == 6
    assert all(item.action == "NO_ORDER" for item in first.decisions)


def test_v112_fixture_replay_fingerprint_repeats() -> None:
    engine = load_exact_candidate_engine()
    params = next(iter(engine.grid()))
    source = (
        session(datetime(2026, 1, 5, tzinfo=BERLIN))
        + session(datetime(2026, 1, 6, tzinfo=BERLIN))
        + session(datetime(2026, 1, 7, tzinfo=BERLIN))
    )
    candles = tuple(to_candle(bar) for bar in source)
    first = run_replay_days(engine, candles, params)
    second = run_replay_days(engine, candles, params)
    assert first == second
    assert v112_results_fingerprint(first) == v112_results_fingerprint(second)


def test_shadow_run_manifest_is_deterministic() -> None:
    source = session(datetime(2026, 1, 5, tzinfo=BERLIN))
    dataset_identity = bar_fingerprint(source[-1])
    first = RunManifest.build(
        dataset_fingerprint=dataset_identity,
        engine_fingerprint="b3d62e0cad72420d36ade523857d024d4a334298be51a8313069e36614bda888",
        config={"surface": "SYNTHETIC_ONLY_NOT_BROKER_EVIDENCE"},
        mode=RuntimeMode.SHADOW,
    )
    second = RunManifest.build(
        dataset_fingerprint=dataset_identity,
        engine_fingerprint="b3d62e0cad72420d36ade523857d024d4a334298be51a8313069e36614bda888",
        config={"surface": "SYNTHETIC_ONLY_NOT_BROKER_EVIDENCE"},
        mode=RuntimeMode.SHADOW,
    )
    assert first == second
    assert len(first.manifest_fingerprint) == 64
