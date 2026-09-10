"""Fail closed if the read-only dashboard drifts from canonical repository state."""
from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    ref = json.loads((root / "research/V112_REFERENCE_V1/reference_result.json").read_text())
    registry = json.loads((root / "research/RESEARCH_FAMILY_REGISTRY_V1.json").read_text())
    v12_registry = json.loads((root / "research/V12_CANDIDATE_REGISTRY.json").read_text())
    web = json.loads((root / "web/status.json").read_text())

    checks = {
        "experiment_id": (web["active_reference"]["experiment_id"], ref["experiment_id"]),
        "strategy": (web["active_reference"]["strategy"], ref["strategy"]),
        "dataset_rows": (web["dataset"]["session_rows"], ref["dataset"]["session_m5_rows"]),
        "dataset_days": (web["dataset"]["session_days"], ref["dataset"]["valid_session_days"]),
        "dataset_sha": (web["dataset"]["session_sha256"], ref["dataset"]["session_ohlc_sha256"]),
        "engine_sha": (web["engine"]["exact_candidate_sha256"], ref["engine"]["exact_candidate_source_sha256"]),
        "oracle_sha": (web["engine"]["oracle_sha256"], ref["engine"]["oracle_source_sha256"]),
        "variants": (web["engine"]["variants"], ref["engine"]["variants"]),
        "wf_windows": (web["walk_forward"]["windows"], ref["walk_forward"]["windows"]),
        "oos_trades": (web["reference_results"]["normal_oos_trades"], ref["results"]["normal"]["oos_trades"]),
        "oos_return_r": (web["reference_results"]["normal_oos_return_r"], ref["results"]["normal"]["oos_return_r"]),
        "positive_wfs": (web["reference_results"]["positive_wfs"], ref["results"]["normal"]["positive_wfs"]),
        "negative_wfs": (web["reference_results"]["negative_wfs"], ref["results"]["normal"]["negative_wfs"]),
        "research_registry_schema": (web["research_families"]["registry_schema"], registry["schema_version"]),
        "research_family_count": (web["research_families"]["count"], len(registry["families"])),
    }
    drift = {name: values for name, values in checks.items() if values[0] != values[1]}
    if drift:
        raise SystemExit(f"web status drift detected: {drift}")

    web_families = {item["id"]: (item["status"], item["evidence_maturity"]) for item in web["research_families"]["items"]}
    registry_families = {item["id"]: (item["status"], item["evidence_maturity"]) for item in registry["families"]}
    if web_families != registry_families:
        raise SystemExit(f"web research-family drift detected: web={web_families} registry={registry_families}")
    if web["active_reference"]["immutable"] is not True:
        raise SystemExit("web status must mark V11.2 active reference immutable")
    if web["readiness"]["paper"] != "BLOCKED" or web["readiness"]["live"] != "BLOCKED":
        raise SystemExit("web status must not expose Paper/Live as ready")

    replay = web.get("historical_sequential_replay")
    if not isinstance(replay, dict):
        raise SystemExit("web status must expose historical sequential replay state")
    if replay.get("state") != "COMPLETE" or replay.get("milestones") != "241-245":
        raise SystemExit("historical replay milestones must be represented as complete")
    if replay.get("schema") != "DAXLAB_HISTORICAL_SEQUENTIAL_REPLAY_V1":
        raise SystemExit("unexpected historical replay schema")
    if replay.get("evidence_state") != "HISTORICAL_REPLAY_ONLY_NOT_BROKER_EVIDENCE":
        raise SystemExit("historical replay must never be represented as broker evidence")
    if replay.get("dataset_identity") != "HASH_VERIFIED":
        raise SystemExit("historical replay must remain bound to hash-verified dataset evidence")
    if replay.get("reference_experiment_id") != ref["experiment_id"]:
        raise SystemExit("historical replay experiment binding drift")
    if replay.get("reference_engine_sha256") != ref["engine"]["exact_candidate_source_sha256"]:
        raise SystemExit("historical replay engine binding drift")
    if replay.get("closed_m5_only") is not True or replay.get("chronological_only") is not True:
        raise SystemExit("historical replay must remain closed-M5 chronological only")
    if replay.get("future_bar_access") != "PROHIBITED_AND_TESTED":
        raise SystemExit("historical replay future-bar guard missing")
    if replay.get("duplicate_bar_idempotency") != "TESTED":
        raise SystemExit("historical replay duplicate idempotency must remain tested")
    if replay.get("checkpoint_resume_parity") != "TESTED":
        raise SystemExit("historical replay checkpoint/resume parity must remain tested")
    if replay.get("deterministic_replay_fingerprint") != "IMPLEMENTED":
        raise SystemExit("historical replay fingerprint contract missing")
    if replay.get("action") != "NO_ORDER_ONLY" or replay.get("execution_capability") != "NONE":
        raise SystemExit("historical replay must remain observation-only")
    if replay.get("order_execution_enabled") is not False:
        raise SystemExit("historical replay must keep execution disabled")

    selection = web.get("v12_candidate_selection")
    if not isinstance(selection, dict):
        raise SystemExit("web status must expose V12 candidate-selection state")
    if selection.get("state") != "MILESTONES_246_248_COMPLETE":
        raise SystemExit("V12 selection milestones 246-248 must be complete")
    if selection.get("registry_schema") != v12_registry["schema_version"]:
        raise SystemExit("V12 candidate registry schema drift")
    web_candidates = {item["id"]: item["state"] for item in selection.get("items", [])}
    registry_candidates = {item["family"]: item["state"] for item in v12_registry["candidates"]}
    if web_candidates != registry_candidates:
        raise SystemExit(f"V12 candidate-selection drift detected: web={web_candidates} registry={registry_candidates}")
    robust_count = sum(state == "ROBUST_CANDIDATE" for state in registry_candidates.values())
    if selection.get("robust_candidate_count") != robust_count:
        raise SystemExit("V12 robust-candidate count drift")
    if robust_count != 0 or selection.get("interaction_test") != "NO_INTERACTION_AUTHORIZED":
        raise SystemExit("V12 interaction telemetry must remain blocked without a robust candidate")
    if selection.get("production_promotion") is not False:
        raise SystemExit("V12 selection must not imply production promotion")
    if selection.get("paper_started") is not False or selection.get("live_authorized") is not False:
        raise SystemExit("V12 selection must not imply Paper/LIVE readiness")
    if selection.get("order_execution_enabled") is not False:
        raise SystemExit("V12 selection must keep execution disabled")

    forward = web.get("forward_monitoring")
    if not isinstance(forward, dict):
        raise SystemExit("web status must expose Forward SHADOW monitoring state")
    if forward.get("state") != "CONTRACT_IMPLEMENTED_AWAITING_REAL_FORWARD_EVIDENCE":
        raise SystemExit("Forward monitoring must remain awaiting real forward evidence")
    if forward.get("schema") != "DAXLAB_FORWARD_MONITORING_OPERATOR_VIEW_V1":
        raise SystemExit("unexpected Forward monitoring schema")
    if forward.get("source") != "src/daxlab/operator/forward_monitoring_view.py":
        raise SystemExit("Forward monitoring source contract drift")
    if forward.get("mode") != "SHADOW" or forward.get("read_only") is not True:
        raise SystemExit("Forward monitoring must remain read-only SHADOW")
    if forward.get("monitoring_only") is not True:
        raise SystemExit("Forward monitoring must remain monitoring-only")
    if forward.get("real_forward_evidence_present") is not False:
        raise SystemExit("web status must not fabricate real forward evidence")
    if forward.get("rolling_degradation_available") is not False:
        raise SystemExit("rolling degradation must not be shown available without real forward evidence")
    if forward.get("statistical_significance_claimed") is not False:
        raise SystemExit("Forward monitoring must not claim statistical significance")
    if forward.get("composite_score") is not None:
        raise SystemExit("Forward monitoring must not expose a composite score")
    if forward.get("automatic_promotion") is not False:
        raise SystemExit("Forward monitoring must not auto-promote")
    if forward.get("execution_capability") != "NONE" or forward.get("order_execution_enabled") is not False:
        raise SystemExit("Forward monitoring must preserve NO_ORDER")

    mt5 = web.get("mt5_adapter")
    if not isinstance(mt5, dict):
        raise SystemExit("web status must expose MT5 adapter preparation state")
    if mt5.get("mode") != "READ_ONLY_ONLY":
        raise SystemExit("MT5 adapter must remain read-only during architecture preparation")
    if mt5.get("order_execution_enabled") is not False:
        raise SystemExit("MT5 order execution must remain disabled before explicit Paper authorization")
    if mt5.get("execution_ready") is not False:
        raise SystemExit("read-only web status must never imply MT5 execution readiness")
    if mt5.get("phase") != "ARCHITECTURE_PREPARATION":
        raise SystemExit("unexpected MT5 adapter phase")
    if mt5.get("health_snapshot_schema") != "MT5_WATCHDOG_V1":
        raise SystemExit("missing deterministic MT5 watchdog schema")
    if mt5.get("host_observation_evidence_schema") != "MT5_HOST_EVIDENCE_V1":
        raise SystemExit("missing credential-free MT5 host evidence schema")
    if not isinstance(mt5.get("why_no_trade"), str) or not mt5["why_no_trade"]:
        raise SystemExit("MT5 why_no_trade blocker must be explicit")

    host = web.get("host_readiness")
    if not isinstance(host, dict):
        raise SystemExit("web status must expose credential-free host readiness")
    if host.get("state") != "AWAITING_REAL_WINDOWS_HOST":
        raise SystemExit("host readiness must remain externally blocked until real host evidence exists")
    if host.get("bundle_schema") != "DAXLAB_MT5_WINDOWS_BUNDLE_V1":
        raise SystemExit("unexpected Windows MT5 bundle schema")
    if host.get("shadow_bridge") != "IMPLEMENTED_OFFLINE":
        raise SystemExit("offline MT5-to-SHADOW bridge state missing")
    if host.get("single_instance_lock_required") is not True:
        raise SystemExit("single-instance lock must be required")
    if host.get("real_host_evidence_present") is not False:
        raise SystemExit("web status must not fabricate real host evidence")
    if host.get("order_execution_enabled") is not False:
        raise SystemExit("host readiness must keep execution disabled")

    gate = web.get("pre_host_gate")
    if not isinstance(gate, dict):
        raise SystemExit("web status must expose explicit pre-host gate")
    if gate.get("external_mt5_milestones_102_110_complete") is not False:
        raise SystemExit("external MT5 milestones 102-110 must remain incomplete before real host evidence")
    if gate.get("next_external_milestone") != 102:
        raise SystemExit("next external milestone must remain 102")
    if gate.get("synthetic_evidence_satisfies_real_host_readiness") is not False:
        raise SystemExit("synthetic evidence must never satisfy real-host readiness")
    if gate.get("paper_started") is not False:
        raise SystemExit("Paper must remain not started before verified host evidence")
    if gate.get("live_authorized") is not False:
        raise SystemExit("LIVE must remain unauthorized")
    if gate.get("order_execution_enabled") is not False:
        raise SystemExit("pre-host gate must keep execution disabled")

    soak = web.get("synthetic_shadow_soak")
    if not isinstance(soak, dict):
        raise SystemExit("web status must expose synthetic SHADOW soak state")
    if soak.get("evidence_state") != "SYNTHETIC_ONLY_NOT_BROKER_EVIDENCE":
        raise SystemExit("synthetic soak must never be represented as broker evidence")
    if soak.get("checkpoint_schema") != "DAXLAB_SHADOW_SOAK_CHECKPOINT_V2":
        raise SystemExit("synthetic soak must expose strengthened checkpoint V2")
    if soak.get("recovery_schema") != "DAXLAB_SHADOW_SOAK_RECOVERY_V2":
        raise SystemExit("synthetic soak must expose strengthened recovery V2")
    if soak.get("action") != "NO_ORDER_ONLY" or soak.get("order_execution_enabled") is not False:
        raise SystemExit("synthetic soak must remain observation-only")

    paper = web.get("paper_preparation")
    if not isinstance(paper, dict):
        raise SystemExit("web status must expose paper preparation state")
    if paper.get("paper_started") is not False or paper.get("broker_adapter_present") is not False:
        raise SystemExit("paper preparation must not imply Paper start or broker adapter")
    if paper.get("execution_capability") != "SIMULATION_ONLY":
        raise SystemExit("paper preparation capability must remain simulation-only")

    if web["recovery"].get("mt5_host_evidence_manifest") != "IMPLEMENTED_CREDENTIAL_FREE":
        raise SystemExit("MT5 host evidence recovery manifest contract missing")

    print("Web status integrity OK | V11.2 frozen | Forward SHADOW truthful | Paper/Live BLOCKED")


if __name__ == "__main__":
    main()
