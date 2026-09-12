from datetime import date, datetime, time, timedelta
import json
from pathlib import Path

import pandas as pd
import pytest

from daxlab.research.cand001_oos_aggregation import aggregate_cand001_oos
from daxlab.research.cand001_oos_evidence_export import (
    AGGREGATION_FILENAME,
    MANIFEST_FILENAME,
    MEASUREMENTS_FILENAME,
    write_cand001_oos_evidence_directory,
)
from daxlab.research.cand001_oos_evidence_reader import (
    load_cand001_oos_evidence_directory,
)
from daxlab.research.cand001_oos_measurement_runner import run_cand001_oos_measurements


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


def _write(tmp_path: Path):
    measurement = run_cand001_oos_measurements(
        _session(),
        dataset_fingerprint=DATASET_SHA,
    )
    aggregation = aggregate_cand001_oos(measurement)
    root = tmp_path / "evidence"
    manifest = write_cand001_oos_evidence_directory(root, measurement, aggregation)
    return root, measurement, aggregation, manifest


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_export_round_trips_to_exact_typed_evidence(tmp_path: Path) -> None:
    root, measurement, aggregation, manifest = _write(tmp_path)

    verified = load_cand001_oos_evidence_directory(root)

    assert verified.measurement == measurement
    assert verified.aggregation == aggregation
    assert verified.manifest == manifest
    assert len(verified.verification_fingerprint) == 64
    assert verified.execution_capability == "NONE"
    assert verified.order_execution_enabled is False


def test_reader_rejects_extra_or_missing_file(tmp_path: Path) -> None:
    root, *_ = _write(tmp_path)
    extra = root / "unexpected.json"
    extra.write_text("{}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="layout mismatch"):
        load_cand001_oos_evidence_directory(root)

    extra.unlink()
    (root / AGGREGATION_FILENAME).unlink()
    with pytest.raises(ValueError, match="layout mismatch"):
        load_cand001_oos_evidence_directory(root)


def test_reader_rejects_unknown_nested_measurement_field(tmp_path: Path) -> None:
    root, *_ = _write(tmp_path)
    path = root / MEASUREMENTS_FILENAME
    payload = _read(path)
    payload["measurements"][0]["surprise"] = "not allowed"
    _write_json(path, payload)

    with pytest.raises(ValueError, match="field mismatch"):
        load_cand001_oos_evidence_directory(root)


def test_reader_rejects_metric_tamper_even_when_old_ids_remain(tmp_path: Path) -> None:
    root, *_ = _write(tmp_path)
    path = root / MEASUREMENTS_FILENAME
    payload = _read(path)
    payload["measurements"][0]["max_drawdown_r"] = 999.0
    _write_json(path, payload)

    with pytest.raises(ValueError, match="source payload fingerprint mismatch"):
        load_cand001_oos_evidence_directory(root)


def test_reader_rejects_manifest_tamper(tmp_path: Path) -> None:
    root, *_ = _write(tmp_path)
    path = root / MANIFEST_FILENAME
    payload = _read(path)
    payload["manifest_fingerprint"] = "f" * 64
    _write_json(path, payload)

    with pytest.raises(ValueError, match="manifest does not match"):
        load_cand001_oos_evidence_directory(root)


def test_reader_rejects_execution_safety_inversion(tmp_path: Path) -> None:
    root, *_ = _write(tmp_path)
    path = root / AGGREGATION_FILENAME
    payload = _read(path)
    payload["order_execution_enabled"] = True
    _write_json(path, payload)

    with pytest.raises(ValueError, match="cannot authorize execution"):
        load_cand001_oos_evidence_directory(root)
