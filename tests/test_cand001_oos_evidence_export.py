from dataclasses import replace
from datetime import date, datetime, time, timedelta
import json
from pathlib import Path

import pandas as pd
import pytest

from daxlab.research.cand001_oos_aggregation import aggregate_cand001_oos
from daxlab.research.cand001_oos_evidence_export import (
    AGGREGATION_FILENAME,
    CAND001_OOS_EVIDENCE_EXPORT_SCHEMA,
    MANIFEST_FILENAME,
    MEASUREMENTS_FILENAME,
    build_cand001_oos_evidence_payloads,
    write_cand001_oos_evidence_directory,
)
from daxlab.research.cand001_oos_measurement_runner import run_cand001_oos_measurements
from daxlab.runtime.decision import stable_fingerprint


DATASET_SHA = "e51bba6cb2befe5e7eb0376318e43b096a3e2ecaae3f556019862975c60286a2"


def _session(days: int = 70) -> pd.DataFrame:
    rows: list[dict[str, float]] = []
    index: list[pd.Timestamp] = []
    start = date(2014, 1, 1)
    for day_index in range(days):
        day = start + timedelta(days=day_index)
        for bar_index in range(4):
            stamp = datetime.combine(day, time(9, 0)) + timedelta(minutes=5 * bar_index)
            index.append(pd.Timestamp(stamp, tz="Europe/Berlin"))
            rows.append({"open": 100.0, "high": 100.2, "low": 99.8, "close": 100.0})
    return pd.DataFrame(rows, index=pd.DatetimeIndex(index, name="timestamp"))


def _evidence():
    measurement = run_cand001_oos_measurements(
        _session(),
        dataset_fingerprint=DATASET_SHA,
    )
    aggregation = aggregate_cand001_oos(measurement)
    return measurement, aggregation


def test_payload_builder_is_deterministic_and_binds_all_lineage() -> None:
    measurement, aggregation = _evidence()

    first = build_cand001_oos_evidence_payloads(measurement, aggregation)
    second = build_cand001_oos_evidence_payloads(measurement, aggregation)

    assert first == second
    manifest = first.manifest
    assert manifest.schema_version == CAND001_OOS_EVIDENCE_EXPORT_SCHEMA
    assert manifest.dataset_fingerprint == measurement.dataset_fingerprint
    assert manifest.measurement_bundle_fingerprint == measurement.bundle_fingerprint
    assert manifest.measurement_payload_fingerprint == stable_fingerprint(measurement.to_payload())
    assert manifest.aggregation_fingerprint == aggregation.aggregation_fingerprint
    assert manifest.aggregation_payload_fingerprint == stable_fingerprint(aggregation.to_payload())
    assert manifest.execution_capability == "NONE"
    assert manifest.order_execution_enabled is False


def test_writer_creates_exact_immutable_three_file_evidence_bundle(tmp_path: Path) -> None:
    measurement, aggregation = _evidence()
    target = tmp_path / "cand001_oos_evidence"

    manifest = write_cand001_oos_evidence_directory(target, measurement, aggregation)

    assert {path.name for path in target.iterdir()} == {
        MEASUREMENTS_FILENAME,
        AGGREGATION_FILENAME,
        MANIFEST_FILENAME,
    }
    measurements_payload = json.loads((target / MEASUREMENTS_FILENAME).read_text())
    aggregation_payload = json.loads((target / AGGREGATION_FILENAME).read_text())
    manifest_payload = json.loads((target / MANIFEST_FILENAME).read_text())
    assert stable_fingerprint(measurements_payload) == manifest.measurement_payload_fingerprint
    assert stable_fingerprint(aggregation_payload) == manifest.aggregation_payload_fingerprint
    assert manifest_payload == manifest.to_payload()
    assert manifest_payload["write_policy"] == "NEW_DIRECTORY_ONLY_MANIFEST_LAST"


def test_writer_refuses_existing_directory_without_changing_it(tmp_path: Path) -> None:
    measurement, aggregation = _evidence()
    target = tmp_path / "existing"
    target.mkdir()
    sentinel = target / "keep.txt"
    sentinel.write_text("untouched", encoding="utf-8")

    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        write_cand001_oos_evidence_directory(target, measurement, aggregation)

    assert sentinel.read_text(encoding="utf-8") == "untouched"
    assert list(target.iterdir()) == [sentinel]


def test_export_rejects_wrong_source_bundle_identity() -> None:
    measurement, aggregation = _evidence()
    drifted = replace(aggregation, source_bundle_fingerprint="d" * 64)

    with pytest.raises(ValueError, match="source bundle fingerprint mismatch"):
        build_cand001_oos_evidence_payloads(measurement, drifted)


def test_export_rejects_measurement_payload_drift_even_with_old_bundle_id() -> None:
    measurement, aggregation = _evidence()
    changed = list(measurement.measurements)
    changed[0] = replace(changed[0], max_drawdown_r=999.0)
    drifted_measurement = replace(measurement, measurements=tuple(changed))

    with pytest.raises(ValueError, match="source payload fingerprint mismatch"):
        build_cand001_oos_evidence_payloads(drifted_measurement, aggregation)
