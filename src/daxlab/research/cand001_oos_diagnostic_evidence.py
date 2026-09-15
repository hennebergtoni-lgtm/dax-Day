"""Deterministic machine-readable diagnostic evidence for frozen CAND-001 OOS.

This module does not modify the Step-2107 three-file base export. It builds one
separate descriptive diagnostic artifact bound to the canonical measurement,
aggregation, base-export manifest, PASS cost-consistency audit and temporal
stability diagnostics. No threshold, composite score, promotion or execution
capability exists here.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from daxlab.research.cand001_oos_aggregation import Cand001OosAggregation
from daxlab.research.cand001_oos_cost_consistency import (
    Cand001OosCostConsistencyAudit,
    CostConsistencyState,
    audit_cand001_oos_cost_consistency,
)
from daxlab.research.cand001_oos_evidence_export import (
    build_cand001_oos_evidence_payloads,
)
from daxlab.research.cand001_oos_measurement_runner import Cand001OosMeasurementBundle
from daxlab.research.cand001_oos_stability import (
    Cand001OosStabilityDiagnostics,
    build_cand001_oos_stability_diagnostics,
)
from daxlab.research.cand001_oos_walk_forward import ECONOMIC_CLAIM, EVIDENCE_CLASS
from daxlab.runtime.atomic_json import atomic_write_json
from daxlab.runtime.decision import stable_fingerprint


CAND001_OOS_DIAGNOSTIC_EVIDENCE_SCHEMA = "DAXLAB_CAND001_OOS_DIAGNOSTIC_EVIDENCE_V1"
DIAGNOSTIC_FILENAME = "diagnostics.json"


@dataclass(frozen=True, slots=True)
class Cand001OosDiagnosticEvidence:
    schema_version: str
    dataset_fingerprint: str
    contract_fingerprint: str
    candidate_id: str
    config_fingerprint: str
    source_measurement_bundle_fingerprint: str
    source_aggregation_fingerprint: str
    source_base_export_manifest_fingerprint: str
    source_cost_consistency_fingerprint: str
    source_stability_fingerprint: str
    cost_consistency_payload_fingerprint: str
    stability_payload_fingerprint: str
    cost_consistency: dict[str, object]
    stability: dict[str, object]
    artifact_fingerprint: str
    evidence_class: str = EVIDENCE_CLASS
    economic_claim: str = ECONOMIC_CLAIM
    interpretation: str = "DESCRIPTIVE_DIAGNOSTICS_ONLY_NOT_ECONOMIC_PROMOTION"
    threshold_policy: str = "NO_COMPOSITE_SCORE_NO_PASS_THRESHOLD"
    automatic_promotion: bool = False
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != CAND001_OOS_DIAGNOSTIC_EVIDENCE_SCHEMA:
            raise ValueError("unsupported CAND-001 OOS diagnostic evidence schema")
        for field, value in (
            ("dataset_fingerprint", self.dataset_fingerprint),
            ("contract_fingerprint", self.contract_fingerprint),
            ("config_fingerprint", self.config_fingerprint),
            ("source_measurement_bundle_fingerprint", self.source_measurement_bundle_fingerprint),
            ("source_aggregation_fingerprint", self.source_aggregation_fingerprint),
            ("source_base_export_manifest_fingerprint", self.source_base_export_manifest_fingerprint),
            ("source_cost_consistency_fingerprint", self.source_cost_consistency_fingerprint),
            ("source_stability_fingerprint", self.source_stability_fingerprint),
            ("cost_consistency_payload_fingerprint", self.cost_consistency_payload_fingerprint),
            ("stability_payload_fingerprint", self.stability_payload_fingerprint),
            ("artifact_fingerprint", self.artifact_fingerprint),
        ):
            _assert_sha256(value, field=field)
        if not self.candidate_id:
            raise ValueError("candidate_id must be non-empty")
        if self.threshold_policy != "NO_COMPOSITE_SCORE_NO_PASS_THRESHOLD":
            raise ValueError("diagnostic evidence cannot introduce an economic threshold")
        if self.automatic_promotion:
            raise ValueError("diagnostic evidence cannot auto-promote a candidate")
        if self.execution_capability != "NONE" or self.order_execution_enabled:
            raise ValueError("diagnostic evidence cannot authorize execution")
        if self.cost_consistency.get("state") != CostConsistencyState.PASS.value:
            raise ValueError("diagnostic evidence requires PASS cost-consistency payload")
        if self.stability.get("descriptive_only") is not True:
            raise ValueError("diagnostic stability payload must remain descriptive")
        if self.stability.get("composite_score") is not None:
            raise ValueError("diagnostic stability payload cannot carry composite score")

    def to_payload(self) -> dict[str, object]:
        return asdict(self)


def build_cand001_oos_diagnostic_evidence(
    measurement: Cand001OosMeasurementBundle,
    aggregation: Cand001OosAggregation,
    cost_consistency: Cand001OosCostConsistencyAudit,
    stability: Cand001OosStabilityDiagnostics,
) -> Cand001OosDiagnosticEvidence:
    """Build one canonical threshold-free diagnostic artifact from verified sources."""
    base_export = build_cand001_oos_evidence_payloads(measurement, aggregation)

    canonical_cost = audit_cand001_oos_cost_consistency(measurement, aggregation)
    if cost_consistency != canonical_cost:
        raise ValueError("cost-consistency evidence is not canonical for diagnostic source")
    if canonical_cost.state is not CostConsistencyState.PASS:
        raise ValueError("diagnostic evidence requires PASS cost-consistency audit")

    canonical_stability = build_cand001_oos_stability_diagnostics(
        measurement,
        aggregation,
        canonical_cost,
    )
    if stability != canonical_stability:
        raise ValueError("stability evidence is not canonical for diagnostic source")

    cost_payload = canonical_cost.to_payload()
    stability_payload = canonical_stability.to_payload()
    cost_payload_fingerprint = stable_fingerprint(cost_payload)
    stability_payload_fingerprint = stable_fingerprint(stability_payload)

    identity = {
        "schema_version": CAND001_OOS_DIAGNOSTIC_EVIDENCE_SCHEMA,
        "dataset_fingerprint": measurement.dataset_fingerprint,
        "contract_fingerprint": measurement.contract_fingerprint,
        "candidate_id": measurement.candidate_id,
        "config_fingerprint": measurement.config_fingerprint,
        "source_measurement_bundle_fingerprint": measurement.bundle_fingerprint,
        "source_aggregation_fingerprint": aggregation.aggregation_fingerprint,
        "source_base_export_manifest_fingerprint": base_export.manifest.manifest_fingerprint,
        "source_cost_consistency_fingerprint": canonical_cost.audit_fingerprint,
        "source_stability_fingerprint": canonical_stability.diagnostics_fingerprint,
        "cost_consistency_payload_fingerprint": cost_payload_fingerprint,
        "stability_payload_fingerprint": stability_payload_fingerprint,
        "evidence_class": EVIDENCE_CLASS,
        "economic_claim": ECONOMIC_CLAIM,
        "interpretation": "DESCRIPTIVE_DIAGNOSTICS_ONLY_NOT_ECONOMIC_PROMOTION",
        "threshold_policy": "NO_COMPOSITE_SCORE_NO_PASS_THRESHOLD",
        "automatic_promotion": False,
        "execution_capability": "NONE",
        "order_execution_enabled": False,
    }
    artifact_fingerprint = stable_fingerprint(
        {
            **identity,
            "cost_consistency": cost_payload,
            "stability": stability_payload,
        }
    )
    return Cand001OosDiagnosticEvidence(
        **identity,
        cost_consistency=cost_payload,
        stability=stability_payload,
        artifact_fingerprint=artifact_fingerprint,
    )


def write_cand001_oos_diagnostic_evidence(
    output_file: str | Path,
    measurement: Cand001OosMeasurementBundle,
    aggregation: Cand001OosAggregation,
    cost_consistency: Cand001OosCostConsistencyAudit,
    stability: Cand001OosStabilityDiagnostics,
) -> Cand001OosDiagnosticEvidence:
    """Write one immutable standalone diagnostic JSON artifact."""
    target = Path(output_file)
    if target.exists():
        raise FileExistsError(f"refusing to overwrite diagnostic evidence: {target}")
    if target.name != DIAGNOSTIC_FILENAME:
        raise ValueError(f"diagnostic filename must be {DIAGNOSTIC_FILENAME!r}")
    evidence = build_cand001_oos_diagnostic_evidence(
        measurement,
        aggregation,
        cost_consistency,
        stability,
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(target, evidence.to_payload())
    return evidence


def _assert_sha256(value: str, *, field: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{field} must be sha256")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field} must be hexadecimal") from exc
