"""Deterministic dataset identity for the NextGen historical bar catalog."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from hashlib import sha256
import json
from typing import Any, Iterable

from daxlab.domain.market import Candle


DATASET_SCHEMA_VERSION = "DAXLAB_BAR_DATASET_V1"
MANIFEST_SCHEMA_VERSION = "DAXLAB_DATASET_MANIFEST_V1"


@dataclass(frozen=True, slots=True)
class DatasetManifest:
    """Content identity plus physical-object integrity for one immutable dataset."""

    dataset_fingerprint: str
    parquet_sha256: str
    instrument_id: str
    timeframe: str
    row_count: int
    first_event_time: datetime
    last_event_time: datetime
    manifest_fingerprint: str
    schema_version: str = MANIFEST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require_sha256(self.dataset_fingerprint, "dataset_fingerprint")
        _require_sha256(self.parquet_sha256, "parquet_sha256")
        _require_sha256(self.manifest_fingerprint, "manifest_fingerprint")
        if self.schema_version != MANIFEST_SCHEMA_VERSION:
            raise ValueError("unsupported dataset manifest schema")
        if not self.instrument_id.strip() or not self.timeframe.strip():
            raise ValueError("instrument_id and timeframe are required")
        if self.row_count <= 0:
            raise ValueError("row_count must be positive")
        _require_utc(self.first_event_time, "first_event_time")
        _require_utc(self.last_event_time, "last_event_time")
        if self.last_event_time < self.first_event_time:
            raise ValueError("last_event_time cannot precede first_event_time")
        if self.manifest_fingerprint != _fingerprint(self._identity_payload()):
            raise ValueError("dataset manifest fingerprint mismatch")

    @classmethod
    def build(
        cls,
        *,
        dataset_fingerprint: str,
        parquet_sha256: str,
        instrument_id: str,
        timeframe: str,
        row_count: int,
        first_event_time: datetime,
        last_event_time: datetime,
    ) -> "DatasetManifest":
        payload = {
            "schema_version": MANIFEST_SCHEMA_VERSION,
            "dataset_fingerprint": dataset_fingerprint,
            "parquet_sha256": parquet_sha256,
            "instrument_id": instrument_id,
            "timeframe": timeframe,
            "row_count": row_count,
            "first_event_time": first_event_time.isoformat(),
            "last_event_time": last_event_time.isoformat(),
        }
        return cls(
            dataset_fingerprint=dataset_fingerprint,
            parquet_sha256=parquet_sha256,
            instrument_id=instrument_id,
            timeframe=timeframe,
            row_count=row_count,
            first_event_time=first_event_time,
            last_event_time=last_event_time,
            manifest_fingerprint=_fingerprint(payload),
        )

    def _identity_payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "dataset_fingerprint": self.dataset_fingerprint,
            "parquet_sha256": self.parquet_sha256,
            "instrument_id": self.instrument_id,
            "timeframe": self.timeframe,
            "row_count": self.row_count,
            "first_event_time": self.first_event_time.isoformat(),
            "last_event_time": self.last_event_time.isoformat(),
        }

    def to_dict(self) -> dict[str, object]:
        return {**self._identity_payload(), "manifest_fingerprint": self.manifest_fingerprint}

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "DatasetManifest":
        required = {
            "schema_version",
            "dataset_fingerprint",
            "parquet_sha256",
            "instrument_id",
            "timeframe",
            "row_count",
            "first_event_time",
            "last_event_time",
            "manifest_fingerprint",
        }
        if set(payload) != required:
            missing = sorted(required - set(payload))
            extra = sorted(set(payload) - required)
            raise ValueError(f"dataset manifest fields mismatch; missing={missing} extra={extra}")
        try:
            first = datetime.fromisoformat(str(payload["first_event_time"]))
            last = datetime.fromisoformat(str(payload["last_event_time"]))
        except ValueError as exc:
            raise ValueError("invalid dataset manifest timestamp") from exc
        return cls(
            schema_version=str(payload["schema_version"]),
            dataset_fingerprint=str(payload["dataset_fingerprint"]),
            parquet_sha256=str(payload["parquet_sha256"]),
            instrument_id=str(payload["instrument_id"]),
            timeframe=str(payload["timeframe"]),
            row_count=int(payload["row_count"]),
            first_event_time=first,
            last_event_time=last,
            manifest_fingerprint=str(payload["manifest_fingerprint"]),
        )


def fingerprint_candles(candles: Iterable[Candle]) -> str:
    """Hash canonical candle content independently of Parquet encoder bytes."""

    rows = [_canonical_candle(candle) for candle in candles]
    return _fingerprint({"schema_version": DATASET_SCHEMA_VERSION, "rows": rows})


def canonical_manifest_json(manifest: DatasetManifest) -> str:
    return json.dumps(manifest.to_dict(), sort_keys=True, indent=2, ensure_ascii=True) + "\n"


def _canonical_candle(candle: Candle) -> dict[str, object]:
    return {
        "instrument_id": candle.instrument_id.value,
        "timeframe": candle.timeframe,
        "event_time": candle.event_time.isoformat(),
        "close_time": candle.close_time.isoformat(),
        "open": float(candle.open),
        "high": float(candle.high),
        "low": float(candle.low),
        "close": float(candle.close),
        "volume": None if candle.volume is None else float(candle.volume),
        "source": candle.source,
        "received_at": candle.received_at.isoformat(),
        "is_closed": candle.is_closed,
        "quality_state": candle.quality_state.value,
    }


def _fingerprint(payload: object) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256(canonical.encode("utf-8")).hexdigest()


def _require_sha256(value: str, field_name: str) -> None:
    if len(value) != 64:
        raise ValueError(f"{field_name} must be sha256 hex")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be sha256 hex") from exc


def _require_utc(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError(f"{field_name} must be timezone-aware UTC")
