"""Fail closed if the read-only dashboard drifts from canonical repository state."""
from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    ref = json.loads((root / "research/V112_REFERENCE_V1/reference_result.json").read_text())
    registry = json.loads((root / "research/RESEARCH_FAMILY_REGISTRY_V1.json").read_text())
    web = json.loads((root / "web/status.json").read_text())

    checks = {
        "experiment_id": (web["active_reference"]["experiment_id"], ref["experiment_id"]),
        "strategy": (web["active_reference"]["strategy"], ref["strategy"]),
        "dataset_rows": (web["dataset"]["session_rows"], ref["dataset"]["session_m5_rows"]),
        "dataset_days": (web["dataset"]["session_days"], ref["dataset"]["valid_session_days"]),
        "dataset_sha": (web["dataset"]["session_sha256"], ref["dataset"]["session_ohlc_sha256"]),
        "engine_sha": (
            web["engine"]["exact_candidate_sha256"],
            ref["engine"]["exact_candidate_source_sha256"],
        ),
        "oracle_sha": (web["engine"]["oracle_sha256"], ref["engine"]["oracle_source_sha256"]),
        "variants": (web["engine"]["variants"], ref["engine"]["variants"]),
        "wf_windows": (web["walk_forward"]["windows"], ref["walk_forward"]["windows"]),
        "oos_trades": (
            web["reference_results"]["normal_oos_trades"],
            ref["results"]["normal"]["oos_trades"],
        ),
        "oos_return_r": (
            web["reference_results"]["normal_oos_return_r"],
            ref["results"]["normal"]["oos_return_r"],
        ),
        "positive_wfs": (
            web["reference_results"]["positive_wfs"],
            ref["results"]["normal"]["positive_wfs"],
        ),
        "negative_wfs": (
            web["reference_results"]["negative_wfs"],
            ref["results"]["normal"]["negative_wfs"],
        ),
        "research_registry_schema": (
            web["research_families"]["registry_schema"],
            registry["schema_version"],
        ),
        "research_family_count": (
            web["research_families"]["count"],
            len(registry["families"]),
        ),
    }
    drift = {name: values for name, values in checks.items() if values[0] != values[1]}
    if drift:
        raise SystemExit(f"web status drift detected: {drift}")

    web_families = {
        item["id"]: (item["status"], item["evidence_maturity"])
        for item in web["research_families"]["items"]
    }
    registry_families = {
        item["id"]: (item["status"], item["evidence_maturity"])
        for item in registry["families"]
    }
    if web_families != registry_families:
        raise SystemExit(
            f"web research-family drift detected: web={web_families} registry={registry_families}"
        )
    if web["active_reference"]["immutable"] is not True:
        raise SystemExit("web status must mark V11.2 active reference immutable")
    if web["readiness"]["paper"] != "BLOCKED" or web["readiness"]["live"] != "BLOCKED":
        raise SystemExit("web status must not expose Paper/Live as ready")
    print(
        "Web status integrity OK | canonical reference + research registry match | Paper/Live BLOCKED"
    )


if __name__ == "__main__":
    main()
