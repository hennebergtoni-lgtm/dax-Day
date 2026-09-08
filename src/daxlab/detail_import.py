"""Pure planning/validation for clean-reference detail imports.

This module never writes to the database. It converts source rows into stable,
typed identities and payload hashes so a later transactional writer can prove
idempotency and detect conflicts before commit.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date, datetime
from math import isfinite
from typing import Iterable, Mapping
from zoneinfo import ZoneInfo

from daxlab.import_guard import ImportReconciliation, deterministic_source_row_id

BERLIN = ZoneInfo("Europe/Berlin")
UTC = ZoneInfo("UTC")

DETAIL_KINDS = {"WF_METRICS", "SELECTED_VARIANTS", "TRADES"}
REQUIRED_COLUMNS = {
    "WF_METRICS": {"wf", "cost", "variant_index", "trades", "return_r", "pf", "avg_r", "max_dd_r"},
    "SELECTED_VARIANTS": {
        "wf", "variant_index", "train_start", "train_end", "oos_start", "oos_end",
        "orb_min", "entry_mode", "stop_mode", "rr", "direction",
    },
    "TRADES": {
        "wf", "variant_index", "date", "r", "side", "entry", "exit", "reason",
        "entry_time", "exit_time", "mfe_r", "mae_r",
    },
}


@dataclass(frozen=True, slots=True)
class PlannedDetailRow:
    detail_kind: str
    source_row_id: str
    payload_sha256: str
    payload: dict[str, object]


@dataclass(frozen=True, slots=True)
class ReconciliationPlan:
    reconciliation: ImportReconciliation
    to_insert: tuple[PlannedDetailRow, ...]
    unchanged: tuple[PlannedDetailRow, ...]
    conflicts: tuple[PlannedDetailRow, ...]


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)


def _payload_hash(payload: Mapping[str, object]) -> str:
    return hashlib.sha256(_canonical_json(dict(payload)).encode("utf-8")).hexdigest()


def _finite_float(value: object, field: str) -> float:
    result = float(value)
    if not isfinite(result):
        raise ValueError(f"non-finite {field}")
    return result


def _int(value: object, field: str, *, minimum: int | None = None) -> int:
    result = int(value)
    if minimum is not None and result < minimum:
        raise ValueError(f"{field} below minimum")
    return result


def _iso_date(value: object, field: str) -> str:
    try:
        return date.fromisoformat(str(value)).isoformat()
    except ValueError as exc:
        raise ValueError(f"invalid {field}") from exc


def berlin_wall_clock_to_utc(value: object, field: str) -> str:
    """Interpret frozen trade wall-clock timestamp in Europe/Berlin and return UTC ISO."""
    try:
        wall = datetime.fromisoformat(str(value))
    except ValueError as exc:
        raise ValueError(f"invalid {field}") from exc
    if wall.tzinfo is not None:
        raise ValueError(f"{field} must be naive frozen Berlin wall-clock")
    return wall.replace(tzinfo=BERLIN).astimezone(UTC).isoformat()


def _normalize(kind: str, row: Mapping[str, object]) -> dict[str, object]:
    missing = sorted(REQUIRED_COLUMNS[kind] - set(row))
    if missing:
        raise ValueError(f"{kind} missing columns: {missing}")
    payload = {str(key): value for key, value in row.items()}
    payload["wf"] = _int(row["wf"], "wf", minimum=1)
    payload["variant_index"] = _int(row["variant_index"], "variant_index", minimum=0)

    if kind == "WF_METRICS":
        payload["trades"] = _int(row["trades"], "trades", minimum=0)
        for field in ("return_r", "pf", "avg_r", "max_dd_r"):
            payload[field] = _finite_float(row[field], field)
        payload["cost"] = str(row["cost"])
    elif kind == "SELECTED_VARIANTS":
        for field in ("train_start", "train_end", "oos_start", "oos_end"):
            payload[field] = _iso_date(row[field], field)
        payload["orb_min"] = _int(row["orb_min"], "orb_min", minimum=1)
        payload["rr"] = _finite_float(row["rr"], "rr")
    elif kind == "TRADES":
        payload["date"] = _iso_date(row["date"], "date")
        for field in ("r", "entry", "exit", "mfe_r", "mae_r"):
            payload[field] = _finite_float(row[field], field)
        payload["entry_time_utc"] = berlin_wall_clock_to_utc(row["entry_time"], "entry_time")
        payload["exit_time_utc"] = berlin_wall_clock_to_utc(row["exit_time"], "exit_time")
        if payload["side"] not in {"long", "short"}:
            raise ValueError("invalid side")
    return payload


def _identity_parts(experiment_key: str, kind: str, payload: Mapping[str, object]) -> tuple[object, ...]:
    if kind == "WF_METRICS":
        return experiment_key, kind, payload["wf"], payload["cost"], payload["variant_index"]
    if kind == "SELECTED_VARIANTS":
        return experiment_key, kind, payload["wf"], payload["variant_index"]
    return (
        experiment_key,
        kind,
        payload["wf"],
        payload["variant_index"],
        payload["date"],
        payload["entry_time_utc"],
        payload["side"],
    )


def plan_detail_rows(
    *, experiment_key: str, detail_kind: str, rows: Iterable[Mapping[str, object]]
) -> tuple[PlannedDetailRow, ...]:
    if detail_kind not in DETAIL_KINDS:
        raise ValueError("unsupported detail_kind")
    planned: list[PlannedDetailRow] = []
    seen: dict[str, str] = {}
    for raw in rows:
        payload = _normalize(detail_kind, raw)
        source_row_id = deterministic_source_row_id(*_identity_parts(experiment_key, detail_kind, payload))
        payload_sha = _payload_hash(payload)
        previous = seen.get(source_row_id)
        if previous is not None:
            if previous != payload_sha:
                raise ValueError("conflicting duplicate source_row_id")
            raise ValueError("duplicate source_row_id")
        seen[source_row_id] = payload_sha
        planned.append(
            PlannedDetailRow(
                detail_kind=detail_kind,
                source_row_id=source_row_id,
                payload_sha256=payload_sha,
                payload=payload,
            )
        )
    return tuple(planned)


def reconcile_planned_rows(
    planned: Iterable[PlannedDetailRow], *, existing_payload_hashes: Mapping[str, str]
) -> ReconciliationPlan:
    """Classify planned rows before any DB mutation.

    Existing identity + identical payload is idempotent/unchanged. Existing identity
    + different payload is a hard conflict. Missing identity is eligible for insert.
    """
    planned_rows = tuple(planned)
    inserts: list[PlannedDetailRow] = []
    unchanged: list[PlannedDetailRow] = []
    conflicts: list[PlannedDetailRow] = []
    for row in planned_rows:
        observed = existing_payload_hashes.get(row.source_row_id)
        if observed is None:
            inserts.append(row)
        elif observed == row.payload_sha256:
            unchanged.append(row)
        else:
            conflicts.append(row)
    return ReconciliationPlan(
        reconciliation=ImportReconciliation(
            source_rows=len(planned_rows),
            inserted_rows=len(inserts),
            unchanged_rows=len(unchanged),
            conflicting_rows=len(conflicts),
        ),
        to_insert=tuple(inserts),
        unchanged=tuple(unchanged),
        conflicts=tuple(conflicts),
    )
