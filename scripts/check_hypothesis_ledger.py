"""Fail closed if the research hypothesis ledger loses trial-accounting integrity."""
from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    ledger = json.loads((root / "research/HYPOTHESIS_LEDGER_V1.json").read_text())
    registry = json.loads((root / "research/RESEARCH_FAMILY_REGISTRY_V1.json").read_text())
    if ledger.get("schema_version") != "DAXLAB_HYPOTHESIS_LEDGER_V1":
        raise SystemExit("unexpected hypothesis ledger schema")
    trials = ledger.get("trials")
    if not isinstance(trials, list) or not trials:
        raise SystemExit("hypothesis ledger must contain trials")
    ids = [row.get("id") for row in trials]
    if len(ids) != len(set(ids)) or any(not value for value in ids):
        raise SystemExit("hypothesis trial ids must be non-empty and unique")
    families = {row["id"] for row in registry["families"]}
    unknown = sorted({row.get("family") for row in trials} - families)
    if unknown:
        raise SystemExit(f"hypothesis ledger references unknown families: {unknown}")
    illegal = [
        row["id"]
        for row in trials
        if row.get("origin") == "OOS_DIAGNOSTIC_DERIVED" and row.get("promotion_proof") is True
    ]
    if illegal:
        raise SystemExit(f"OOS-diagnostic trials cannot be promotion proof: {illegal}")
    print(f"Hypothesis ledger integrity OK | trials={len(trials)} | unique={len(set(ids))}")


if __name__ == "__main__":
    main()
