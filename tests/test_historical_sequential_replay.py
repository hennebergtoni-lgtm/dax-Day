from datetime import datetime, timedelta, timezone

import pytest

from daxlab.runtime.historical_sequential_replay import (
    HistoricalReplayBinding,
    VERIFIED_DATASET_ID,
    VERIFIED_DATASET_SHA256,
    run_historical_sequential_replay,
)
from daxlab.runtime.mt5_readonly import Mt5Bar
from daxlab.runtime.shadow_observation import V112_ENGINE_SHA256, V112_EXPERIMENT_ID


def _bars(count: int = 4) -> tuple[Mt5Bar, ...]:
    start = datetime(2019, 1, 2, 9, 0, tzinfo=timezone.utc)
    return tuple(
        Mt5Bar(
            open_time=start + timedelta(minutes=5 * index),
            open=100.0 + index,
            high=101.0 + index,
            low=99.0 + index,
            close=100.5 + index,
        )
        for index in range(count)
    )


def test_replay_feeds_closed_m5_prefix_sequentially() -> None:
    result = run_historical_sequential_replay(_bars())
    assert result.schema_version == "DAXLAB_HISTORICAL_SEQUENTIAL_REPLAY_V1"
    assert result.evidence_state == "HISTORICAL_REPLAY_ONLY_NOT_BROKER_EVIDENCE"
    assert [record.sequence for record in result.records] == [0, 1, 2, 3]
    assert [record.visible_bar_count for record in result.records] == [1, 2, 3, 4]
    assert all(record.decision.action == "NO_ORDER" for record in result.records)
    assert result.execution_capability == "NONE"
    assert result.order_execution_enabled is False


def test_replay_is_bound_to_verified_dataset_and_v112_reference() -> None:
    result = run_historical_sequential_replay(_bars())
    assert result.dataset_id == VERIFIED_DATASET_ID
    assert result.dataset_sha256 == VERIFIED_DATASET_SHA256
    assert result.reference_experiment_id == V112_EXPERIMENT_ID
    assert result.reference_engine_sha256 == V112_ENGINE_SHA256


def test_replay_is_deterministic_for_same_closed_bars() -> None:
    first = run_historical_sequential_replay(_bars())
    second = run_historical_sequential_replay(_bars())
    assert first == second
    assert len(first.replay_fingerprint) == 64


def test_replay_rejects_out_of_order_or_duplicate_bar_time() -> None:
    bars = _bars(2)
    with pytest.raises(ValueError, match="strictly chronological"):
        run_historical_sequential_replay((bars[1], bars[0]))
    with pytest.raises(ValueError, match="strictly chronological"):
        run_historical_sequential_replay((bars[0], bars[0]))


def test_replay_rejects_non_m5_contract() -> None:
    with pytest.raises(ValueError, match="requires M5"):
        run_historical_sequential_replay(_bars(), timeframe_minutes=1)


def test_replay_requires_timezone_aware_bars() -> None:
    bar = Mt5Bar(datetime(2019, 1, 2, 9, 0), 100.0, 101.0, 99.0, 100.5)
    with pytest.raises(ValueError, match="timezone-aware"):
        run_historical_sequential_replay((bar,))


def test_replay_binding_rejects_wrong_dataset_identity() -> None:
    with pytest.raises(ValueError, match="dataset ID mismatch"):
        HistoricalReplayBinding(dataset_id="other_dataset")
    with pytest.raises(ValueError, match="dataset fingerprint mismatch"):
        HistoricalReplayBinding(dataset_sha256="0" * 64)


def test_replay_binding_rejects_wrong_v112_reference() -> None:
    with pytest.raises(ValueError, match="V11.2 experiment mismatch"):
        HistoricalReplayBinding(reference_experiment_id="V12")
    with pytest.raises(ValueError, match="V11.2 engine fingerprint mismatch"):
        HistoricalReplayBinding(reference_engine_sha256="0" * 64)


def test_replay_revalidates_binding_at_run_boundary() -> None:
    valid = HistoricalReplayBinding()
    forged = object.__new__(HistoricalReplayBinding)
    object.__setattr__(forged, "dataset_id", valid.dataset_id)
    object.__setattr__(forged, "dataset_sha256", "0" * 64)
    object.__setattr__(forged, "reference_experiment_id", valid.reference_experiment_id)
    object.__setattr__(forged, "reference_engine_sha256", valid.reference_engine_sha256)
    with pytest.raises(ValueError, match="dataset fingerprint mismatch"):
        run_historical_sequential_replay(_bars(), binding=forged)
