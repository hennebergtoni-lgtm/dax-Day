"""Fail-closed preflight for V11.2 clean detail CSV artifacts."""
from __future__ import annotations

import csv
import hashlib
import io
from dataclasses import dataclass

from daxlab.detail_import import PlannedDetailRow, plan_detail_rows
from daxlab.reference.detail_artifacts import DetailArtifactSpec


@dataclass(frozen=True, slots=True)
class DetailArtifactPreflight:
    detail_kind: str
    observed_rows: int
    observed_sha256: str
    planned_rows: tuple[PlannedDetailRow, ...]


def preflight_detail_csv(
    *,
    content: bytes,
    spec: DetailArtifactSpec,
    experiment_key: str = "V112_REFERENCE_V1",
) -> DetailArtifactPreflight:
    observed_sha = hashlib.sha256(content).hexdigest()
    if observed_sha != spec.sha256:
        raise ValueError("ARTIFACT_HASH_MISMATCH")
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("ARTIFACT_NOT_UTF8") from exc
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise ValueError("CSV_HEADER_MISSING")
    rows = list(reader)
    if len(rows) != spec.expected_rows:
        raise ValueError("ROW_COUNT_MISMATCH")
    planned = plan_detail_rows(
        experiment_key=experiment_key,
        detail_kind=spec.detail_kind,
        rows=rows,
    )
    if len(planned) != spec.expected_rows:
        raise ValueError("PLANNED_ROW_COUNT_MISMATCH")
    return DetailArtifactPreflight(
        detail_kind=spec.detail_kind,
        observed_rows=len(rows),
        observed_sha256=observed_sha,
        planned_rows=planned,
    )
