"""Deterministic machine-readable export for CAND-001 OOS/WF evidence.

This layer adds no strategy, replay, aggregation, selection or execution logic.
It only validates lineage between the Step-2105 measurement bundle and Step-2106
aggregation and writes immutable JSON evidence with a manifest written last.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping

from daxlab.research.cand001_oos_aggregation import Cand001OosAggregation
from daxlab.research.cand001_oos_measurement_runner import Cand001OosMeasurementBundle
from daxlab.research.cand001_oos_walk_forward import ECONOMIC_CLAIM, EVIDENCE_CLASS
from daxlab.runtime.atomic_json import atomic_write_json
from daxlab.runtime.decision import stable_fingerprint


CAND001_OOS_EVIDENCE_EXPORT_SCHEMA = "DAXLAB_CAND001_OOS_WF_EVIDENCE_EXPORT_V1"
MEASUREMENTS_FILENAME = "measurements.json"
AGGREGATION_FILENAME = "aggregation.json"
MANIFEST_FILENAME = "manifest.json"


@dataclass(frozen=True, slots=True)
class Cand001OosEvidenceManifest:
    schema_version: str
    dataset_fingerprint: str
    contract_fingerprint: str
    candidate_id: str
    config_fingerprint: str
    window_count: int
    measurement_count: int
    measurement_bundle_fingerprint: str
    measurement_payload_fingerprint: str
    aggregation_fingerprint: str
    aggregation_payload_fingerprint: str
    measurements_file: str
    aggregation_file: str
    manifest_file: str
    manifest_fingerprint: str
    evidence_class: str = EVIDENCE_CLASS
    economic_claim: str = ECONOMIC_CLAIM
    selection_policy: str = "FROZEN_PREDECLARED_CANDIDATE_NO_TUNING"
    write_policy: str = "NEW_DIRECTORY_ONLY_MANIFEST_LAST"
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != CAND001_OOS_EVIDENCE_EXPORT_SCHEMA:
            raise ValueError("unsupported CAND-001 OOS evidence export schema")
        for field, value in (
            ("dataset_fingerprint", self.dataset_fingerprint),
            ("contract_fingerprint", self.contract_fingerprint),
            ("config_fingerprint", self.config_fingerprint),
            ("measurement_bundle_fingerprint", self.measurement_bundle_fingerprint),
            ("measurement_payload_fingerprint", self.measurement_payload_fingerprint),
            ("aggregation_fingerprint", self.aggregation_fingerprint),
            ("aggregation_payload_fingerprint", self.aggregation_payload_fingerprint),
            ("manifest_fingerprint", self.manifest_fingerprint),
        ):
            _assert_sha256(value, field=field)
        if self.window_count <= 0 or self.measurement_count <= 0:
            raise ValueError("OOS evidence manifest counts must be positive")
        if (
            self.measurements_file != MEASUREMENTS_FILENAME
            or self.aggregation_file != AGGREGATION_FILENAME
            or self.manifest_file != MANIFEST_FILENAME
        ):
            raise ValueError("OOS evidence filenames are fixed by schema")
        if self.execution_capability != "NONE" or self.order_execution_enabled:
            raise ValueError("OOS evidence export cannot authorize execution")

    def to_payload(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class Cand001OosEvidencePayloads:
    measurements: Mapping[str, object]
    aggregation: Mapping[str, object]
    manifest: Cand001OosEvidenceManifest


def build_cand001_oos_evidence_payloads(
    measurement: Cand001OosMeasurementBundle,
    aggregation: Cand001OosAggregation,
) -> Cand001OosEvidencePayloads:
    """Validate cross-artifact lineage and build deterministic export payloads."""
    _validate_lineage(measurement, aggregation)
    measurement_payload = measurement.to_payload()
    aggregation_payload = aggregation.to_payload()
    measurement_payload_fingerprint = stable_fingerprint(measurement_payload)
    aggregation_payload_fingerprint = stable_fingerprint(aggregation_payload)

    manifest_identity = {
        "schema_version": CAND001_OOS_EVIDENCE_EXPORT_SCHEMA,
        "dataset_fingerprint": measurement.dataset_fingerprint,
        "contract_fingerprint": measurement.contract_fingerprint,
        "candidate_id": measurement.candidate_id,
        "config_fingerprint": measurement.config_fingerprint,
        "window_count": measurement.window_count,
        "measurement_count": measurement.measurement_count,
        "measurement_bundle_fingerprint": measurement.bundle_fingerprint,
        "measurement_payload_fingerprint": measurement_payload_fingerprint,
        "aggregation_fingerprint": aggregation.aggregation_fingerprint,
        "aggregation_payload_fingerprint": aggregation_payload_fingerprint,
        "measurements_file": MEASUREMENTS_FILENAME,
        "aggregation_file": AGGREGATION_FILENAME,
        "manifest_file": MANIFEST_FILENAME,
        "evidence_class": EVIDENCE_CLASS,
        "economic_claim": ECONOMIC_CLAIM,
        "selection_policy": "FROZEN_PREDECLARED_CANDIDATE_NO_TUNING",
        "write_policy": "NEW_DIRECTORY_ONLY_MANIFEST_LAST",
        "execution_capability": "NONE",
        "order_execution_enabled": False,
    }
    manifest = Cand001OosEvidenceManifest(
        **manifest_identity,
        manifest_fingerprint=stable_fingerprint(manifest_identity),
    )
    return Cand001OosEvidencePayloads(
        measurements=measurement_payload,
        aggregation=aggregation_payload,
        manifest=manifest,
    )


def write_cand001_oos_evidence_directory(
    output_dir: str | Path,
    measurement: Cand001OosMeasurementBundle,
    aggregation: Cand001OosAggregation,
) -> Cand001OosEvidenceManifest:
    """Write one immutable evidence directory; refuse any pre-existing target."""
    target = Path(output_dir)
    if target.exists():
        raise FileExistsError(f"refusing to overwrite existing evidence directory: {target}")

    payloads = build_cand001_oos_evidence_payloads(measurement, aggregation)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.mkdir()
    try:
        atomic_write_json(target / MEASUREMENTS_FILENAME, payloads.measurements)
        atomic_write_json(target / AGGREGATION_FILENAME, payloads.aggregation)
        # Completion marker: manifest is deliberately written last.
        atomic_write_json(target / MANIFEST_FILENAME, payloads.manifest.to_payload())
    except Exception:
        # Keep any completed files as crash evidence; the directory is intentionally
        # not reusable because future runs must never mix evidence generations.
        raise
    return payloads.manifest


def _validate_lineage(
    measurement: Cand001OosMeasurementBundle,
    aggregation: Cand001OosAggregation,
) -> None:
    if measurement.execution_capability != "NONE" or measurement.order_execution_enabled:
        raise ValueError("measurement bundle is not execution-safe")
    if aggregation.execution_capability != "NONE" or aggregation.order_execution_enabled:
        raise ValueError("aggregation is not execution-safe")
    if aggregation.source_bundle_fingerprint != measurement.bundle_fingerprint:
        raise ValueError("aggregation source bundle fingerprint mismatch")
    expected_measurement_payload = stable_fingerprint(measurement.to_payload())
    if aggregation.source_payload_fingerprint != expected_measurement_payload:
        raise ValueError("aggregation source payload fingerprint mismatch")
    for field in (
        "dataset_fingerprint",
        "contract_fingerprint",
        "candidate_id",
        "config_fingerprint",
        "window_count",
        "measurement_count",
    ):
        if getattr(aggregation, field) != getattr(measurement, field):
            raise ValueError(f"OOS evidence lineage mismatch: {field}")


def _assert_sha256(value: str, *, field: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{field} must be sha256")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field} must be hexadecimal") from exc
