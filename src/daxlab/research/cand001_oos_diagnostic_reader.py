"""Strict verifier for standalone CAND-001 OOS diagnostic evidence.

The JSON artifact is never trusted on syntax alone. Verification requires the
already verified Step-2105/2106 source objects; canonical cost consistency,
temporal stability and the full Step-2111 diagnostic payload are recomputed and
must match exactly after canonical JSON normalization.
"""
from __future__ import annotations

from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any, Mapping

from daxlab.research.cand001_oos_aggregation import Cand001OosAggregation
from daxlab.research.cand001_oos_cost_consistency import audit_cand001_oos_cost_consistency
from daxlab.research.cand001_oos_diagnostic_evidence import (
    DIAGNOSTIC_FILENAME,
    Cand001OosDiagnosticEvidence,
    build_cand001_oos_diagnostic_evidence,
)
from daxlab.research.cand001_oos_measurement_runner import Cand001OosMeasurementBundle
from daxlab.research.cand001_oos_stability import build_cand001_oos_stability_diagnostics
from daxlab.runtime.atomic_json import read_json_object
from daxlab.runtime.decision import stable_fingerprint


@dataclass(frozen=True, slots=True)
class VerifiedCand001OosDiagnosticEvidence:
    evidence: Cand001OosDiagnosticEvidence
    verification_fingerprint: str
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        _assert_sha256(self.verification_fingerprint, field="verification_fingerprint")
        if self.execution_capability != "NONE" or self.order_execution_enabled:
            raise ValueError("verified diagnostic evidence cannot authorize execution")


def load_cand001_oos_diagnostic_evidence(
    path: str | Path,
    *,
    measurement: Cand001OosMeasurementBundle,
    aggregation: Cand001OosAggregation,
) -> VerifiedCand001OosDiagnosticEvidence:
    """Load and fully re-verify one standalone Step-2111 diagnostic artifact."""
    target = Path(path)
    if not target.is_file():
        raise FileNotFoundError(f"OOS diagnostic evidence missing: {target}")
    if target.name != DIAGNOSTIC_FILENAME:
        raise ValueError(f"diagnostic filename must be {DIAGNOSTIC_FILENAME!r}")

    raw = read_json_object(target)
    _assert_exact_fields(Cand001OosDiagnosticEvidence, raw, "diagnostic evidence")

    cost_consistency = audit_cand001_oos_cost_consistency(measurement, aggregation)
    stability = build_cand001_oos_stability_diagnostics(
        measurement,
        aggregation,
        cost_consistency,
    )
    expected = build_cand001_oos_diagnostic_evidence(
        measurement,
        aggregation,
        cost_consistency,
        stability,
    )
    expected_payload = expected.to_payload()

    # JSON serialization normalizes Python tuples to arrays/lists. Compare the
    # canonical JSON identity rather than raw Python container types.
    if stable_fingerprint(raw) != stable_fingerprint(expected_payload):
        raise ValueError("diagnostic JSON does not match recomputed canonical evidence")

    verification_identity = {
        "artifact_fingerprint": expected.artifact_fingerprint,
        "source_measurement_bundle_fingerprint": expected.source_measurement_bundle_fingerprint,
        "source_aggregation_fingerprint": expected.source_aggregation_fingerprint,
        "source_base_export_manifest_fingerprint": expected.source_base_export_manifest_fingerprint,
        "source_cost_consistency_fingerprint": expected.source_cost_consistency_fingerprint,
        "source_stability_fingerprint": expected.source_stability_fingerprint,
        "execution_capability": "NONE",
        "order_execution_enabled": False,
    }
    return VerifiedCand001OosDiagnosticEvidence(
        evidence=expected,
        verification_fingerprint=stable_fingerprint(verification_identity),
    )


def _assert_exact_fields(
    cls: type[Any],
    payload: Mapping[str, Any],
    label: str,
) -> None:
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
