"""Pure integrity guards for detailed research artifact imports."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ArtifactImportSpec:
    experiment_key: str
    expected_sha256: str
    expected_rows: int
    dataset_sha256: str
    engine_sha256: str
    schema_version: str


@dataclass(frozen=True, slots=True)
class ArtifactObservation:
    sha256: str
    rows: int
    dataset_sha256: str
    engine_sha256: str
    schema_version: str


@dataclass(frozen=True, slots=True)
class ImportReconciliation:
    source_rows: int
    inserted_rows: int
    unchanged_rows: int
    conflicting_rows: int


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def validate_preimport(
    spec: ArtifactImportSpec, observation: ArtifactObservation
) -> tuple[str, ...]:
    """Return blockers; empty means the artifact may enter a write transaction."""
    blockers: list[str] = []
    if observation.sha256 != spec.expected_sha256:
        blockers.append("ARTIFACT_HASH_MISMATCH")
    if observation.rows != spec.expected_rows:
        blockers.append("ROW_COUNT_MISMATCH")
    if observation.dataset_sha256 != spec.dataset_sha256:
        blockers.append("DATASET_FINGERPRINT_MISMATCH")
    if observation.engine_sha256 != spec.engine_sha256:
        blockers.append("ENGINE_FINGERPRINT_MISMATCH")
    if observation.schema_version != spec.schema_version:
        blockers.append("SCHEMA_VERSION_MISMATCH")
    return tuple(blockers)


def validate_postimport(reconciliation: ImportReconciliation) -> tuple[str, ...]:
    """Require exact source reconciliation before transaction commit."""
    blockers: list[str] = []
    if reconciliation.conflicting_rows:
        blockers.append("CONFLICTING_ROWS")
    if reconciliation.inserted_rows + reconciliation.unchanged_rows != reconciliation.source_rows:
        blockers.append("SOURCE_ROW_RECONCILIATION_MISMATCH")
    return tuple(blockers)


def deterministic_source_row_id(*parts: object) -> str:
    """Create stable source-row identity for idempotent importers."""
    payload = "\x1f".join(str(part) for part in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
