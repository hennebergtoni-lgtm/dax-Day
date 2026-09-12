"""Strict round-trip verifier for exported CAND-001 OOS/WF evidence.

External evidence is never trusted merely because it is valid JSON. The reader
requires the exact Step-2107 three-file layout, reconstructs typed Step-2105/2106
objects, re-runs their validation and recomputes all export lineage/fingerprints.
"""
from __future__ import annotations

from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any, Mapping, TypeVar

from daxlab.research.cand001_oos_aggregation import (
    Cand001OosAggregation,
    Cand001OosCostDegradation,
    Cand001OosCostSummary,
)
from daxlab.research.cand001_oos_evidence_export import (
    AGGREGATION_FILENAME,
    MANIFEST_FILENAME,
    MEASUREMENTS_FILENAME,
    Cand001OosEvidenceManifest,
    build_cand001_oos_evidence_payloads,
)
from daxlab.research.cand001_oos_measurement_runner import (
    Cand001OosMeasurement,
    Cand001OosMeasurementBundle,
)
from daxlab.runtime.atomic_json import read_json_object
from daxlab.runtime.decision import stable_fingerprint


T = TypeVar("T")
_EXPECTED_FILES = {
    MEASUREMENTS_FILENAME,
    AGGREGATION_FILENAME,
    MANIFEST_FILENAME,
}


@dataclass(frozen=True, slots=True)
class VerifiedCand001OosEvidence:
    measurement: Cand001OosMeasurementBundle
    aggregation: Cand001OosAggregation
    manifest: Cand001OosEvidenceManifest
    verification_fingerprint: str
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        _assert_sha256(self.verification_fingerprint, field="verification_fingerprint")
        if self.execution_capability != "NONE" or self.order_execution_enabled:
            raise ValueError("verified OOS evidence cannot authorize execution")


def load_cand001_oos_evidence_directory(
    directory: str | Path,
) -> VerifiedCand001OosEvidence:
    """Load and fully re-verify one immutable Step-2107 evidence directory."""
    root = Path(directory)
    if not root.is_dir():
        raise FileNotFoundError(f"OOS evidence directory missing: {root}")
    entries = {item.name for item in root.iterdir()}
    if entries != _EXPECTED_FILES:
        missing = sorted(_EXPECTED_FILES - entries)
        extra = sorted(entries - _EXPECTED_FILES)
        raise ValueError(
            f"OOS evidence directory layout mismatch: missing={missing} extra={extra}"
        )

    raw_measurement = read_json_object(root / MEASUREMENTS_FILENAME)
    raw_aggregation = read_json_object(root / AGGREGATION_FILENAME)
    raw_manifest = read_json_object(root / MANIFEST_FILENAME)

    measurement = _parse_measurement_bundle(raw_measurement)
    aggregation = _parse_aggregation(raw_aggregation)
    manifest = _strict_construct(Cand001OosEvidenceManifest, raw_manifest, "manifest")

    rebuilt = build_cand001_oos_evidence_payloads(measurement, aggregation)
    if stable_fingerprint(raw_measurement) != manifest.measurement_payload_fingerprint:
        raise ValueError("measurement JSON payload fingerprint mismatch")
    if stable_fingerprint(raw_aggregation) != manifest.aggregation_payload_fingerprint:
        raise ValueError("aggregation JSON payload fingerprint mismatch")
    if raw_manifest != rebuilt.manifest.to_payload():
        raise ValueError("manifest does not match recomputed OOS evidence lineage")
    if stable_fingerprint(raw_measurement) != stable_fingerprint(rebuilt.measurements):
        raise ValueError("measurement JSON does not round-trip to canonical payload")
    if stable_fingerprint(raw_aggregation) != stable_fingerprint(rebuilt.aggregation):
        raise ValueError("aggregation JSON does not round-trip to canonical payload")

    verification_identity = {
        "manifest_fingerprint": manifest.manifest_fingerprint,
        "measurement_payload_fingerprint": manifest.measurement_payload_fingerprint,
        "aggregation_payload_fingerprint": manifest.aggregation_payload_fingerprint,
        "dataset_fingerprint": manifest.dataset_fingerprint,
        "candidate_id": manifest.candidate_id,
        "execution_capability": "NONE",
        "order_execution_enabled": False,
    }
    return VerifiedCand001OosEvidence(
        measurement=measurement,
        aggregation=aggregation,
        manifest=manifest,
        verification_fingerprint=stable_fingerprint(verification_identity),
    )


def _parse_measurement_bundle(
    payload: Mapping[str, Any],
) -> Cand001OosMeasurementBundle:
    _assert_exact_fields(Cand001OosMeasurementBundle, payload, "measurement bundle")
    raw_items = payload.get("measurements")
    if not isinstance(raw_items, list):
        raise ValueError("measurement bundle measurements must be a list")
    measurements = tuple(
        _strict_construct(Cand001OosMeasurement, item, f"measurement[{index}]")
        for index, item in enumerate(raw_items, start=1)
    )
    values = dict(payload)
    values["measurements"] = measurements
    return Cand001OosMeasurementBundle(**values)


def _parse_aggregation(payload: Mapping[str, Any]) -> Cand001OosAggregation:
    _assert_exact_fields(Cand001OosAggregation, payload, "aggregation")
    raw_summaries = payload.get("cost_summaries")
    raw_degradations = payload.get("degradations")
    if not isinstance(raw_summaries, list):
        raise ValueError("aggregation cost_summaries must be a list")
    if not isinstance(raw_degradations, list):
        raise ValueError("aggregation degradations must be a list")

    summaries: list[Cand001OosCostSummary] = []
    for index, item in enumerate(raw_summaries, start=1):
        if not isinstance(item, Mapping):
            raise ValueError(f"cost_summary[{index}] must be an object")
        values = dict(item)
        raw_fingerprints = values.get("window_result_fingerprints")
        if not isinstance(raw_fingerprints, list):
            raise ValueError(
                f"cost_summary[{index}] window_result_fingerprints must be a list"
            )
        values["window_result_fingerprints"] = tuple(raw_fingerprints)
        summaries.append(
            _strict_construct(
                Cand001OosCostSummary,
                values,
                f"cost_summary[{index}]",
            )
        )

    degradations = tuple(
        _strict_construct(
            Cand001OosCostDegradation,
            item,
            f"degradation[{index}]",
        )
        for index, item in enumerate(raw_degradations, start=1)
    )
    values = dict(payload)
    values["cost_summaries"] = tuple(summaries)
    values["degradations"] = degradations
    return Cand001OosAggregation(**values)


def _strict_construct(cls: type[T], payload: Any, label: str) -> T:
    if not isinstance(payload, Mapping):
        raise ValueError(f"{label} must be an object")
    _assert_exact_fields(cls, payload, label)
    return cls(**dict(payload))


def _assert_exact_fields(cls: type[Any], payload: Mapping[str, Any], label: str) -> None:
    expected = {item.name for item in fields(cls)}
    observed = set(payload)
    if observed != expected:
        missing = sorted(expected - observed)
        unknown = sorted(observed - expected)
        raise ValueError(f"{label} field mismatch: missing={missing} unknown={unknown}")


def _assert_sha256(value: str, *, field: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{field} must be sha256")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field} must be hexadecimal") from exc
