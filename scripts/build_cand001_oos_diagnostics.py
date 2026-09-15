#!/usr/bin/env python3
"""Build standalone CAND-001 OOS diagnostics from verified exported evidence.

This is post-processing only. It never re-runs historical measurement, never
modifies the Step-2107 three-file evidence directory and has no execution path.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from daxlab.research.cand001_oos_cost_consistency import audit_cand001_oos_cost_consistency
from daxlab.research.cand001_oos_diagnostic_evidence import (
    DIAGNOSTIC_FILENAME,
    write_cand001_oos_diagnostic_evidence,
)
from daxlab.research.cand001_oos_evidence_reader import load_cand001_oos_evidence_directory
from daxlab.research.cand001_oos_stability import build_cand001_oos_stability_diagnostics


def build_diagnostics(*, evidence_dir: Path, output_dir: Path) -> dict[str, object]:
    source = evidence_dir.resolve()
    target_dir = output_dir.resolve()
    if source == target_dir:
        raise ValueError("diagnostic output directory must be separate from base OOS evidence")

    verified = load_cand001_oos_evidence_directory(source)
    cost_consistency = audit_cand001_oos_cost_consistency(
        verified.measurement,
        verified.aggregation,
    )
    stability = build_cand001_oos_stability_diagnostics(
        verified.measurement,
        verified.aggregation,
        cost_consistency,
    )
    target = target_dir / DIAGNOSTIC_FILENAME
    evidence = write_cand001_oos_diagnostic_evidence(
        target,
        verified.measurement,
        verified.aggregation,
        cost_consistency,
        stability,
    )
    return {
        "status": "DIAGNOSTIC_EVIDENCE_WRITTEN",
        "source_evidence_dir": str(source),
        "output_file": str(target),
        "source_verification_fingerprint": verified.verification_fingerprint,
        "source_base_export_manifest_fingerprint": (
            evidence.source_base_export_manifest_fingerprint
        ),
        "cost_consistency_fingerprint": evidence.source_cost_consistency_fingerprint,
        "stability_fingerprint": evidence.source_stability_fingerprint,
        "diagnostic_artifact_fingerprint": evidence.artifact_fingerprint,
        "interpretation": evidence.interpretation,
        "threshold_policy": evidence.threshold_policy,
        "automatic_promotion": evidence.automatic_promotion,
        "execution_capability": evidence.execution_capability,
        "order_execution_enabled": evidence.order_execution_enabled,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build descriptive CAND-001 OOS diagnostics from an already verified "
            "Step-2107 evidence directory (NO EXECUTION)."
        )
    )
    parser.add_argument(
        "--evidence-dir",
        required=True,
        type=Path,
        help="Existing immutable three-file CAND-001 OOS evidence directory.",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="Separate directory for diagnostics.json; existing file is refused.",
    )
    args = parser.parse_args()

    result = build_diagnostics(
        evidence_dir=args.evidence_dir,
        output_dir=args.output_dir,
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
