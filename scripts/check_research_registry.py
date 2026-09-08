"""Fail closed if the V6 research-family registry drifts from its control contract."""
from __future__ import annotations

import json
from pathlib import Path

ALLOWED_STATUSES = {"PLANNED", "RESEARCH", "RETAINED", "REJECTED", "VALIDATED", "DEPLOYABLE"}
ALLOWED_MATURITY = {
    "PLAN_ONLY",
    "CAUSALITY_TESTED",
    "DESCRIPTIVE",
    "OOS_TESTED",
    "WF_TESTED",
    "COST_STRESSED",
    "STABILITY_TESTED",
    "PROSPECTIVE_TESTED",
}
REQUIRED_FAMILIES = {
    "BB001",
    "FIB001",
    "GAP001",
    "FAIL001",
    "BOOST001",
    "ATR001",
    "LIQ001",
    "STRUCT001",
    "MOM001",
    "SESSION001",
    "ENTRY001",
    "EXIT001",
}


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    path = root / "research" / "RESEARCH_FAMILY_REGISTRY_V1.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "DAXLAB_RESEARCH_FAMILY_REGISTRY_V1":
        raise SystemExit("research registry schema drift")
    baseline = payload.get("baseline", {})
    if baseline.get("experiment_id") != "V112_REFERENCE_V1" or baseline.get("immutable") is not True:
        raise SystemExit("research registry must bind immutable V112_REFERENCE_V1")
    families = payload.get("families", [])
    ids = [item.get("id") for item in families]
    if len(ids) != len(set(ids)):
        raise SystemExit("duplicate research family ids")
    missing = sorted(REQUIRED_FAMILIES - set(ids))
    if missing:
        raise SystemExit(f"research registry missing required families: {missing}")
    for item in families:
        if item.get("status") not in ALLOWED_STATUSES:
            raise SystemExit(f"invalid status for {item.get('id')}: {item.get('status')}")
        if item.get("evidence_maturity") not in ALLOWED_MATURITY:
            raise SystemExit(
                f"invalid evidence maturity for {item.get('id')}: {item.get('evidence_maturity')}"
            )
        if item.get("promotion_allowed") is not False:
            raise SystemExit(f"research family may not auto-promote: {item.get('id')}")
        if "known_negative_findings" not in item or "provenance_notes" not in item:
            raise SystemExit(f"research family evidence fields incomplete: {item.get('id')}")
    print(f"Research registry integrity OK | families={len(families)} | baseline=V112_REFERENCE_V1")


if __name__ == "__main__":
    main()
