#!/usr/bin/env python3
"""Run frozen CAND-001 OOS/WF measurement and export deterministic evidence.

No optimization, candidate selection, broker execution, PAPER or LIVE path is
available here. The expected audited dataset fingerprint must be supplied by the
operator/caller and is verified before any result artifact is written.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from daxlab.research.cand001_oos_aggregation import aggregate_cand001_oos
from daxlab.research.cand001_oos_evidence_export import (
    write_cand001_oos_evidence_directory,
)
from daxlab.research.cand001_oos_measurement_runner import (
    run_audited_recovered_m5_cand001_oos_wf,
)


def run_export(
    *,
    data_dir: Path,
    output_dir: Path,
    expected_dataset_fingerprint: str,
) -> dict[str, object]:
    measurement = run_audited_recovered_m5_cand001_oos_wf(
        data_dir,
        expected_dataset_fingerprint=expected_dataset_fingerprint,
    )
    aggregation = aggregate_cand001_oos(measurement)
    manifest = write_cand001_oos_evidence_directory(
        output_dir,
        measurement,
        aggregation,
    )
    return {
        "status": "EVIDENCE_WRITTEN",
        "output_dir": str(output_dir),
        "dataset_fingerprint": manifest.dataset_fingerprint,
        "candidate_id": manifest.candidate_id,
        "window_count": manifest.window_count,
        "measurement_count": manifest.measurement_count,
        "measurement_bundle_fingerprint": manifest.measurement_bundle_fingerprint,
        "aggregation_fingerprint": manifest.aggregation_fingerprint,
        "manifest_fingerprint": manifest.manifest_fingerprint,
        "evidence_class": manifest.evidence_class,
        "economic_claim": manifest.economic_claim,
        "execution_capability": manifest.execution_capability,
        "order_execution_enabled": manifest.order_execution_enabled,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run frozen CAND-001 OOS/WF evidence measurement (NO EXECUTION)."
    )
    parser.add_argument(
        "--data-dir",
        required=True,
        type=Path,
        help="Directory containing the audited recovered daily M5 CSV files.",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="New output directory. Existing paths are refused.",
    )
    parser.add_argument(
        "--expected-dataset-fingerprint",
        required=True,
        help="Expected audited session OHLC SHA256; mismatch fails closed.",
    )
    args = parser.parse_args()

    result = run_export(
        data_dir=args.data_dir.resolve(),
        output_dir=args.output_dir.resolve(),
        expected_dataset_fingerprint=args.expected_dataset_fingerprint.strip(),
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
