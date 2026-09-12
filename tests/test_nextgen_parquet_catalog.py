from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

import pyarrow.parquet as pq
import pytest

from daxlab.data.catalog import ParquetBarCatalog
from daxlab.domain.market import Candle, DataQualityState, InstrumentId


UTC = timezone.utc


def _candles() -> tuple[Candle, ...]:
    start = datetime(2026, 9, 11, 8, 0, tzinfo=UTC)
    instrument = InstrumentId("DAX40.CFD")
    return (
        Candle(
            instrument_id=instrument,
            timeframe="5m",
            event_time=start,
            close_time=start + timedelta(minutes=5),
            open=25000.0,
            high=25020.0,
            low=24990.0,
            close=25010.0,
            volume=100.0,
            source="synthetic-fixture",
            received_at=start + timedelta(minutes=5, seconds=1),
            is_closed=True,
        ),
        Candle(
            instrument_id=instrument,
            timeframe="5m",
            event_time=start + timedelta(minutes=5),
            close_time=start + timedelta(minutes=10),
            open=25010.0,
            high=25030.0,
            low=25000.0,
            close=25025.0,
            volume=None,
            source="synthetic-fixture",
            received_at=start + timedelta(minutes=10, seconds=1),
            is_closed=True,
            quality_state=DataQualityState.SOURCE_DISAGREEMENT,
        ),
        Candle(
            instrument_id=instrument,
            timeframe="5m",
            event_time=start + timedelta(minutes=10),
            close_time=start + timedelta(minutes=15),
            open=25025.0,
            high=25040.0,
            low=25015.0,
            close=25035.0,
            volume=125.5,
            source="synthetic-fixture",
            received_at=start + timedelta(minutes=15, seconds=1),
            is_closed=True,
        ),
    )


def test_parquet_catalog_round_trip_is_exact_and_manifested(tmp_path: Path) -> None:
    catalog = ParquetBarCatalog(tmp_path)
    expected = _candles()

    manifest = catalog.write(expected)
    observed, loaded_manifest = catalog.read(manifest.dataset_fingerprint)

    assert observed == expected
    assert loaded_manifest == manifest
    assert manifest.instrument_id == "DAX40.CFD"
    assert manifest.timeframe == "5m"
    assert manifest.row_count == 3
    assert manifest.first_event_time == expected[0].event_time
    assert manifest.last_event_time == expected[-1].event_time
    assert len(manifest.dataset_fingerprint) == 64
    assert len(manifest.parquet_sha256) == 64
    assert len(manifest.manifest_fingerprint) == 64

    parquet_path = tmp_path / "bars" / f"{manifest.dataset_fingerprint}.parquet"
    schema = pq.read_schema(parquet_path)
    assert schema.field("event_time").type.tz == "UTC"
    assert schema.field("close_time").type.tz == "UTC"
    assert schema.field("received_at").type.tz == "UTC"


def test_identical_write_is_idempotent(tmp_path: Path) -> None:
    catalog = ParquetBarCatalog(tmp_path)
    first = catalog.write(_candles())
    parquet_path = tmp_path / "bars" / f"{first.dataset_fingerprint}.parquet"
    original_bytes = parquet_path.read_bytes()

    second = catalog.write(_candles())

    assert second == first
    assert parquet_path.read_bytes() == original_bytes


def test_catalog_rejects_mixed_series_open_and_unordered_data(tmp_path: Path) -> None:
    catalog = ParquetBarCatalog(tmp_path)
    rows = _candles()

    mixed_instrument = (
        rows[0],
        Candle(
            **{
                **_candle_values(rows[1]),
                "instrument_id": InstrumentId("OTHER.INSTRUMENT"),
            }
        ),
    )
    with pytest.raises(ValueError, match="one instrument"):
        catalog.write(mixed_instrument)

    mixed_timeframe = (
        rows[0],
        Candle(**{**_candle_values(rows[1]), "timeframe": "1m"}),
    )
    with pytest.raises(ValueError, match="one timeframe"):
        catalog.write(mixed_timeframe)

    open_candle = Candle(**{**_candle_values(rows[0]), "is_closed": False})
    with pytest.raises(ValueError, match="closed candles only"):
        catalog.write((open_candle,))

    with pytest.raises(ValueError, match="strictly increasing"):
        catalog.write((rows[1], rows[0]))
    with pytest.raises(ValueError, match="strictly increasing"):
        catalog.write((rows[0], rows[0]))


def test_catalog_fails_closed_on_parquet_tamper(tmp_path: Path) -> None:
    catalog = ParquetBarCatalog(tmp_path)
    manifest = catalog.write(_candles())
    parquet_path = tmp_path / "bars" / f"{manifest.dataset_fingerprint}.parquet"
    parquet_path.write_bytes(parquet_path.read_bytes() + b"tamper")

    with pytest.raises(RuntimeError, match="SHA256 mismatch"):
        catalog.read(manifest.dataset_fingerprint)


def test_catalog_fails_closed_on_manifest_tamper(tmp_path: Path) -> None:
    catalog = ParquetBarCatalog(tmp_path)
    manifest = catalog.write(_candles())
    manifest_path = tmp_path / "manifests" / f"{manifest.dataset_fingerprint}.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["row_count"] = 999
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(RuntimeError, match="manifest integrity check failed"):
        catalog.read(manifest.dataset_fingerprint)


def test_catalog_rejects_incomplete_manifest_parquet_pair(tmp_path: Path) -> None:
    catalog = ParquetBarCatalog(tmp_path)
    manifest = catalog.write(_candles())
    manifest_path = tmp_path / "manifests" / f"{manifest.dataset_fingerprint}.json"
    manifest_path.unlink()

    with pytest.raises(RuntimeError, match="pair mismatch"):
        catalog.write(_candles())


def test_catalog_surface_has_no_legacy_candidate_or_mt5_dependency() -> None:
    catalog_root = Path(__file__).resolve().parents[1] / "src" / "daxlab" / "data" / "catalog"
    source = "\n".join(
        path.read_text(encoding="utf-8").lower()
        for path in sorted(catalog_root.glob("*.py"))
    )
    for forbidden in ("legacy_dataset", "cand001", "metatrader5", "v112_bridge"):
        assert forbidden not in source


def _candle_values(candle: Candle) -> dict[str, object]:
    return {
        "instrument_id": candle.instrument_id,
        "timeframe": candle.timeframe,
        "event_time": candle.event_time,
        "close_time": candle.close_time,
        "open": candle.open,
        "high": candle.high,
        "low": candle.low,
        "close": candle.close,
        "volume": candle.volume,
        "source": candle.source,
        "received_at": candle.received_at,
        "is_closed": candle.is_closed,
        "quality_state": candle.quality_state,
    }
