"""Immutable Parquet-backed historical bar catalog for canonical NextGen candles."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Iterable

import pyarrow as pa
import pyarrow.parquet as pq

from daxlab.data.catalog.manifest import (
    DatasetManifest,
    canonical_manifest_json,
    fingerprint_candles,
)
from daxlab.domain.market import Candle, DataQualityState, InstrumentId


BAR_SCHEMA = pa.schema(
    [
        pa.field("instrument_id", pa.string(), nullable=False),
        pa.field("timeframe", pa.string(), nullable=False),
        pa.field("event_time", pa.timestamp("us", tz="UTC"), nullable=False),
        pa.field("close_time", pa.timestamp("us", tz="UTC"), nullable=False),
        pa.field("open", pa.float64(), nullable=False),
        pa.field("high", pa.float64(), nullable=False),
        pa.field("low", pa.float64(), nullable=False),
        pa.field("close", pa.float64(), nullable=False),
        pa.field("volume", pa.float64(), nullable=True),
        pa.field("source", pa.string(), nullable=False),
        pa.field("received_at", pa.timestamp("us", tz="UTC"), nullable=False),
        pa.field("is_closed", pa.bool_(), nullable=False),
        pa.field("quality_state", pa.string(), nullable=False),
    ]
)


class ParquetBarCatalog:
    """Fingerprint-addressed local catalog for immutable one-series bar datasets."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def write(self, candles: Iterable[Candle]) -> DatasetManifest:
        rows = tuple(candles)
        _validate_dataset(rows)
        dataset_fingerprint = fingerprint_candles(rows)
        parquet_path = self._parquet_path(dataset_fingerprint)
        manifest_path = self._manifest_path(dataset_fingerprint)

        parquet_exists = parquet_path.exists()
        manifest_exists = manifest_path.exists()
        if parquet_exists != manifest_exists:
            raise RuntimeError("catalog dataset is incomplete: Parquet/manifest pair mismatch")
        if parquet_exists:
            existing_rows, existing_manifest = self.read(dataset_fingerprint)
            if existing_rows != rows:
                raise RuntimeError("dataset fingerprint collision or non-canonical existing object")
            return existing_manifest

        parquet_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)

        parquet_tmp = parquet_path.with_name(parquet_path.name + ".tmp")
        manifest_tmp = manifest_path.with_name(manifest_path.name + ".tmp")
        try:
            table = pa.Table.from_pylist([_candle_to_row(candle) for candle in rows], schema=BAR_SCHEMA)
            pq.write_table(
                table,
                parquet_tmp,
                compression="zstd",
                version="2.6",
                write_statistics=True,
            )
            parquet_sha256 = _sha256_file(parquet_tmp)
            manifest = DatasetManifest.build(
                dataset_fingerprint=dataset_fingerprint,
                parquet_sha256=parquet_sha256,
                instrument_id=rows[0].instrument_id.value,
                timeframe=rows[0].timeframe,
                row_count=len(rows),
                first_event_time=rows[0].event_time,
                last_event_time=rows[-1].event_time,
            )
            manifest_tmp.write_text(canonical_manifest_json(manifest), encoding="utf-8")
            parquet_tmp.replace(parquet_path)
            manifest_tmp.replace(manifest_path)
            return manifest
        finally:
            parquet_tmp.unlink(missing_ok=True)
            manifest_tmp.unlink(missing_ok=True)

    def read(self, dataset_fingerprint: str) -> tuple[tuple[Candle, ...], DatasetManifest]:
        manifest = self.load_manifest(dataset_fingerprint)
        parquet_path = self._parquet_path(dataset_fingerprint)
        if not parquet_path.is_file():
            raise FileNotFoundError(f"Parquet object missing for dataset {dataset_fingerprint}")
        if _sha256_file(parquet_path) != manifest.parquet_sha256:
            raise RuntimeError("Parquet object SHA256 mismatch")

        table = pq.read_table(parquet_path)
        if not table.schema.equals(BAR_SCHEMA, check_metadata=False):
            raise RuntimeError(f"Parquet schema mismatch: {table.schema}")

        try:
            rows = tuple(_row_to_candle(row) for row in table.to_pylist())
        except (KeyError, TypeError, ValueError) as exc:
            raise RuntimeError("Parquet rows violate canonical candle schema") from exc
        _validate_dataset(rows)

        observed_fingerprint = fingerprint_candles(rows)
        if observed_fingerprint != manifest.dataset_fingerprint:
            raise RuntimeError("canonical dataset content fingerprint mismatch")
        if len(rows) != manifest.row_count:
            raise RuntimeError("dataset row-count mismatch")
        if rows[0].instrument_id.value != manifest.instrument_id:
            raise RuntimeError("dataset instrument identity mismatch")
        if rows[0].timeframe != manifest.timeframe:
            raise RuntimeError("dataset timeframe mismatch")
        if rows[0].event_time != manifest.first_event_time:
            raise RuntimeError("dataset first-event-time mismatch")
        if rows[-1].event_time != manifest.last_event_time:
            raise RuntimeError("dataset last-event-time mismatch")
        return rows, manifest

    def load_manifest(self, dataset_fingerprint: str) -> DatasetManifest:
        _require_sha256(dataset_fingerprint)
        manifest_path = self._manifest_path(dataset_fingerprint)
        if not manifest_path.is_file():
            raise FileNotFoundError(f"manifest missing for dataset {dataset_fingerprint}")
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError("dataset manifest is unreadable") from exc
        if not isinstance(payload, dict):
            raise RuntimeError("dataset manifest must be a JSON object")
        try:
            manifest = DatasetManifest.from_dict(payload)
        except (TypeError, ValueError) as exc:
            raise RuntimeError("dataset manifest integrity check failed") from exc
        if manifest.dataset_fingerprint != dataset_fingerprint:
            raise RuntimeError("manifest path/content dataset fingerprint mismatch")
        return manifest

    def _parquet_path(self, dataset_fingerprint: str) -> Path:
        _require_sha256(dataset_fingerprint)
        return self.root / "bars" / f"{dataset_fingerprint}.parquet"

    def _manifest_path(self, dataset_fingerprint: str) -> Path:
        _require_sha256(dataset_fingerprint)
        return self.root / "manifests" / f"{dataset_fingerprint}.json"


def _validate_dataset(rows: tuple[Candle, ...]) -> None:
    if not rows:
        raise ValueError("historical bar dataset must not be empty")
    instrument_id = rows[0].instrument_id
    timeframe = rows[0].timeframe
    previous_event_time = None
    for candle in rows:
        if candle.instrument_id != instrument_id:
            raise ValueError("historical bar dataset must contain exactly one instrument")
        if candle.timeframe != timeframe:
            raise ValueError("historical bar dataset must contain exactly one timeframe")
        if not candle.is_closed:
            raise ValueError("historical bar catalog accepts closed candles only")
        if previous_event_time is not None and candle.event_time <= previous_event_time:
            raise ValueError("historical bar event_time must be strictly increasing and unique")
        previous_event_time = candle.event_time


def _candle_to_row(candle: Candle) -> dict[str, object]:
    return {
        "instrument_id": candle.instrument_id.value,
        "timeframe": candle.timeframe,
        "event_time": candle.event_time,
        "close_time": candle.close_time,
        "open": float(candle.open),
        "high": float(candle.high),
        "low": float(candle.low),
        "close": float(candle.close),
        "volume": None if candle.volume is None else float(candle.volume),
        "source": candle.source,
        "received_at": candle.received_at,
        "is_closed": candle.is_closed,
        "quality_state": candle.quality_state.value,
    }


def _row_to_candle(row: dict[str, object]) -> Candle:
    return Candle(
        instrument_id=InstrumentId(str(row["instrument_id"])),
        timeframe=str(row["timeframe"]),
        event_time=row["event_time"],  # type: ignore[arg-type]
        close_time=row["close_time"],  # type: ignore[arg-type]
        open=float(row["open"]),
        high=float(row["high"]),
        low=float(row["low"]),
        close=float(row["close"]),
        volume=None if row["volume"] is None else float(row["volume"]),
        source=str(row["source"]),
        received_at=row["received_at"],  # type: ignore[arg-type]
        is_closed=bool(row["is_closed"]),
        quality_state=DataQualityState(str(row["quality_state"])),
    )


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require_sha256(value: str) -> None:
    if len(value) != 64:
        raise ValueError("dataset fingerprint must be sha256 hex")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError("dataset fingerprint must be sha256 hex") from exc
