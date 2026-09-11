"""Fail closed if the static read-only dashboard drifts from canonical evidence.

The V2 static status is deliberately NOT a current runtime source. Fresh Candidate
runtime truth is published separately through CAND-001 operator telemetry.
"""
from __future__ import annotations

import json
from pathlib import Path

_STATIC_SCHEMA = "DAXLAB_WEB_STATIC_STATUS_V2"
_FORBIDDEN_DYNAMIC_SECTIONS = {
    "mt5_adapter",
    "host_readiness",
    "pre_host_gate",
    "synthetic_shadow_soak",
}


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    ref = json.loads((root / "research/V112_REFERENCE_V1/reference_result.json").read_text())
    registry = json.loads((root / "research/RESEARCH_FAMILY_REGISTRY_V1.json").read_text())
    v12_registry = json.loads((root / "research/V12_CANDIDATE_REGISTRY.json").read_text())
    web = json.loads((root / "web/status.json").read_text())

    if web.get("schema_version") != _STATIC_SCHEMA:
        raise SystemExit("web status must use static-evidence V2 schema")
    if web.get("status_scope") != "STATIC_VERSIONED_EVIDENCE_ONLY":
        raise SystemExit("web status scope must be STATIC_VERSIONED_EVIDENCE_ONLY")
    if web.get("runtime_truth_included") is not False:
        raise SystemExit("static web status must not claim current runtime truth")
    leaked = sorted(_FORBIDDEN_DYNAMIC_SECTIONS.intersection(web))
    if leaked:
        raise SystemExit(f"dynamic runtime sections leaked into static web status: {leaked}")

    boundary = web.get("runtime_boundary")
    if not isinstance(boundary, dict):
        raise SystemExit("static web status must expose explicit runtime boundary")
    if boundary.get("current_candidate_contract") != "docs/CAND001_OPERATOR_TELEMETRY_V1.md":
        raise SystemExit("Candidate runtime telemetry contract drift")
    if boundary.get("current_candidate_store") != "cand001_operator_current":
        raise SystemExit("Candidate current runtime store drift")
    if boundary.get("browser_runtime_endpoint") != "NOT_IMPLEMENTED":
        raise SystemExit("static web status must not fabricate a browser runtime endpoint")
    if boundary.get("static_file_must_not_be_used_for_current_health") is not True:
        raise SystemExit("static web status must explicitly reject current-health usage")

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

    replay = web.get("historical_sequential_replay")
    if not isinstance(replay, dict):
        raise SystemExit("web status must expose historical sequential replay state")
    if replay.get("state") != "COMPLETE" or replay.get("milestones") != "241-245":
        raise SystemExit("historical replay milestones must be represented as complete")
    if replay.get("evidence_state") != "HISTORICAL_REPLAY_ONLY_NOT_BROKER_EVIDENCE":
        raise SystemExit("historical replay must never be represented as broker evidence")
    if replay.get("dataset_identity") != "HASH_VERIFIED":
        raise SystemExit("historical replay must remain bound to hash-verified dataset evidence")
    if replay.get("reference_experiment_id") != ref["experiment_id"]:
        raise SystemExit("historical replay experiment binding drift")
    if replay.get("reference_engine_sha256") != ref["engine"]["exact_candidate_source_sha256"]:
        raise SystemExit("historical replay engine binding drift")
    if replay.get("future_bar_access") != "PROHIBITED_AND_TESTED":
        raise SystemExit("historical replay future-bar guard missing")
    if replay.get("duplicate_bar_idempotency") != "TESTED":
        raise SystemExit("historical replay duplicate idempotency must remain tested")
    if replay.get("checkpoint_resume_parity") != "TESTED":
        raise SystemExit("historical replay checkpoint/resume parity must remain tested")
    if replay.get("action") != "NO_ORDER_ONLY" or replay.get("execution_capability") != "NONE":
        raise SystemExit("historical replay must remain observation-only")
    if replay.get("order_execution_enabled") is not False:
        raise SystemExit("historical replay must keep execution disabled")

    selection = web.get("v12_candidate_selection")
    if not isinstance(selection, dict):
        raise SystemExit("web status must expose V12 candidate-selection state")
    if selection.get("registry_schema") != v12_registry["schema_version"]:
        raise SystemExit("V12 candidate registry schema drift")
    web_candidates = {item["id"]: item["state"] for item in selection.get("items", [])}
    registry_candidates = {
        item["family"]: item["state"] for item in v12_registry["candidates"]
    }
    if web_candidates != registry_candidates:
        raise SystemExit(
            f"V12 candidate-selection drift detected: web={web_candidates} registry={registry_candidates}"
        )
    robust_count = sum(state == "ROBUST_CANDIDATE" for state in registry_candidates.values())
    if selection.get("robust_candidate_count") != robust_count or robust_count != 0:
        raise SystemExit("V12 robust-candidate count drift")
    if selection.get("production_promotion") is not False:
        raise SystemExit("V12 selection must not imply production promotion")
    if selection.get("paper_started") is not False or selection.get("live_authorized") is not False:
        raise SystemExit("V12 selection must not imply Paper/LIVE readiness")
    if selection.get("order_execution_enabled") is not False:
        raise SystemExit("V12 selection must keep execution disabled")

    forward = web.get("forward_monitoring")
    if not isinstance(forward, dict):
        raise SystemExit("web status must expose Forward SHADOW contract state")
    if forward.get("state") != "STATIC_CONTRACT_ONLY":
        raise SystemExit("Forward monitoring in static status must be contract-only")
    if forward.get("mode") != "SHADOW" or forward.get("read_only") is not True:
        raise SystemExit("Forward monitoring contract must remain read-only SHADOW")
    if forward.get("runtime_truth_included") is not False:
        raise SystemExit("Forward monitoring static block must not contain runtime truth")
    if forward.get("current_runtime_source") != "CAND001_OPERATOR_TELEMETRY_V1":
        raise SystemExit("Forward monitoring must point to fresh Candidate telemetry")
    if forward.get("statistical_significance_claimed") is not False:
        raise SystemExit("Forward monitoring must not claim statistical significance")
    if forward.get("automatic_promotion") is not False:
        raise SystemExit("Forward monitoring must not auto-promote")
    if forward.get("execution_capability") != "NONE" or forward.get("order_execution_enabled") is not False:
        raise SystemExit("Forward monitoring must preserve NO_ORDER")

    paper = web.get("paper_preparation")
    if not isinstance(paper, dict):
        raise SystemExit("web status must expose paper preparation state")
    if paper.get("paper_started") is not False or paper.get("broker_adapter_present") is not False:
        raise SystemExit("paper preparation must not imply Paper start or broker adapter")
    if paper.get("execution_capability") != "SIMULATION_ONLY":
        raise SystemExit("paper preparation capability must remain simulation-only")

    print(
        "Web static status integrity OK | V11.2 frozen | runtime truth external | "
        "Paper/Live BLOCKED"
    )


if __name__ == "__main__":
    main()
