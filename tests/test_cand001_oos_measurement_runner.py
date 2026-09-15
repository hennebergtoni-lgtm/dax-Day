from dataclasses import replace
from datetime import date, datetime, time, timedelta

import pandas as pd
import pytest

from daxlab.research.cand001_oos_measurement_runner import (
    CAND001_OOS_MEASUREMENT_SCHEMA,
    run_cand001_oos_measurements,
    stressed_fill_model,
)
from daxlab.runtime.paper_contracts import (
    GapPolicy,
    PaperFillModelConfig,
    PartialFillPolicy,
    SameBarPolicy,
)


DATASET_SHA = "e51bba6cb2befe5e7eb0376318e43b096a3e2ecaae3f556019862975c60286a2"


def _session(days: int = 70, *, bars_per_day: int = 4) -> pd.DataFrame:
    rows: list[dict[str, float]] = []
    index: list[pd.Timestamp] = []
    start = date(2014, 1, 1)
    for day_index in range(days):
        day = start + timedelta(days=day_index)
        for bar_index in range(bars_per_day):
            stamp = datetime.combine(day, time(9, 0)) + timedelta(minutes=5 * bar_index)
            index.append(pd.Timestamp(stamp, tz="Europe/Berlin"))
            rows.append(
                {
                    "open": 100.0,
                    "high": 100.2,
                    "low": 99.8,
                    "close": 100.0,
                }
            )
    return pd.DataFrame(rows, index=pd.DatetimeIndex(index, name="timestamp"))


def test_cost_stress_changes_only_cost_fields() -> None:
    base = PaperFillModelConfig(
        spread_points=0.20,
        slippage_points=0.10,
        commission_points=0.10,
        latency_ms=375,
        same_bar_policy=SameBarPolicy.CONSERVATIVE_STOP_FIRST,
        gap_policy=GapPolicy.FILL_AT_FIRST_AVAILABLE,
        partial_fill_policy=PartialFillPolicy.DISABLED,
    )

    stressed = stressed_fill_model(base, 1.5)

    assert stressed.spread_points == pytest.approx(0.30)
    assert stressed.slippage_points == pytest.approx(0.15)
    assert stressed.commission_points == pytest.approx(0.15)
    assert stressed.latency_ms == base.latency_ms
    assert stressed.same_bar_policy is base.same_bar_policy
    assert stressed.gap_policy is base.gap_policy
    assert stressed.partial_fill_policy is base.partial_fill_policy
    assert stressed.schema_version == base.schema_version
    assert stressed.fingerprint != base.fingerprint


def test_cost_stress_rejects_non_positive_multiplier() -> None:
    with pytest.raises(ValueError, match="positive"):
        stressed_fill_model(PaperFillModelConfig(), 0.0)


def test_runner_measures_only_declared_oos_slice_for_each_cost_model() -> None:
    evidence = run_cand001_oos_measurements(
        _session(),
        dataset_fingerprint=DATASET_SHA,
    )

    assert evidence.schema_version == CAND001_OOS_MEASUREMENT_SCHEMA
    assert evidence.source_session_days == 70
    assert evidence.window_count == 1
    assert evidence.cost_model_count == 3
    assert evidence.measurement_count == 3
    assert len(evidence.measurements) == 3
    assert [item.cost_model for item in evidence.measurements] == [
        "normal",
        "stress_1.5x",
        "stress_2x",
    ]
    assert [item.cost_multiplier for item in evidence.measurements] == [1.0, 1.5, 2.0]
    assert all(item.window_number == 1 for item in evidence.measurements)
    assert all(item.processed_sessions == 20 for item in evidence.measurements)
    assert all(item.processed_bars == 80 for item in evidence.measurements)
    assert all(item.completed_trades == 0 for item in evidence.measurements)
    assert all(item.execution_capability == "NONE" for item in evidence.measurements)
    assert all(item.order_execution_enabled is False for item in evidence.measurements)
    assert evidence.execution_capability == "NONE"
    assert evidence.order_execution_enabled is False
    assert len({item.result_fingerprint for item in evidence.measurements}) == 3
    assert len({item.fill_model_fingerprint for item in evidence.measurements}) == 3


def test_runner_is_fully_deterministic() -> None:
    session = _session()

    first = run_cand001_oos_measurements(session, dataset_fingerprint=DATASET_SHA)
    second = run_cand001_oos_measurements(session, dataset_fingerprint=DATASET_SHA)

    assert first == second
    assert first.bundle_fingerprint == second.bundle_fingerprint
    assert [item.result_fingerprint for item in first.measurements] == [
        item.result_fingerprint for item in second.measurements
    ]


def test_runner_does_not_use_train_rows_as_replay_input() -> None:
    session = _session()
    evidence = run_cand001_oos_measurements(session, dataset_fingerprint=DATASET_SHA)
    measurement = evidence.measurements[0]

    # 45 train days are chronology-only. Only 20 OOS days x 4 bars are replayed.
    assert measurement.processed_bars == 20 * 4
    assert measurement.processed_sessions == 20
    assert measurement.oos_start == "2014-02-15"
    assert measurement.oos_end == "2014-03-06"


def test_runner_rejects_bad_dataset_identity_and_non_chronological_session() -> None:
    session = _session()
    with pytest.raises(ValueError, match="dataset_fingerprint"):
        run_cand001_oos_measurements(session, dataset_fingerprint="z" * 64)

    reversed_session = session.iloc[::-1]
    with pytest.raises(ValueError, match="chronological"):
        run_cand001_oos_measurements(
            reversed_session,
            dataset_fingerprint=DATASET_SHA,
        )


def test_bundle_fails_closed_if_measurement_count_is_tampered() -> None:
    evidence = run_cand001_oos_measurements(
        _session(),
        dataset_fingerprint=DATASET_SHA,
    )
    with pytest.raises(ValueError, match="measurement_count"):
        replace(evidence, measurement_count=2)
