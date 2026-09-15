#!/usr/bin/env python3
"""Execute the bounded synthetic V1 acceptance union in a fresh pytest process.

Run pass1 and pass2 separately. All assertions use fixed independent test oracles;
pass2 changes the helper session/date/price sequence. JUnit statuses are measured,
never inferred from test-name presence. Only sanitized result metadata is retained.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
# Existing owner suites are supporting regression, not an assertion that every
# registered failure facet has full integration/real-host/broker coverage.
GROUP_MODULES = {
    "T01": ("test_ig_cand001_shadow_e2e", "test_candidate_shadow_orchestrator"),
    "T02": ("test_bot_helper_review", "test_runtime_quality", "test_runtime_time", "test_shadow_resume_anchor", "test_ig_market_data"),
    "T03": ("test_ig_predemo_safety", "test_operator_console_inventory", "test_operator_console_reconciliation"),
    "T04": ("test_broker_reconciliation", "test_broker_order_lifecycle", "test_demo_transport_query", "test_demo_transport_restart"),
    "T05": ("test_bot_helper_review", "test_ig_predemo_safety", "test_demo_transport_attempt_reservation"),
    "T06": ("test_independent_pretrade_controls", "test_broker_execution_protection", "test_nextgen_execution_protection_binding"),
    "T07": ("test_run_ig_predemo_readiness_2238", "test_dax_windows_host_preflight", "test_dax_windows_python_runtime_probe"),
    "T08": ("test_ig_readiness_observation_durability", "test_operator_console_malformed", "test_operator_console_http"),
    "T09": ("test_ig_readiness_observation_durability", "test_candidate_shadow_checkpoint", "test_candidate_lifecycle_semantic_restore", "test_recovery_bundle_integrity", "test_recovery_bundle_resilience", "test_candidate_state", "test_candidate_active_trade_state"),
    "T10": ("test_bot_helper_review", "test_single_instance",),
    "T11": ("test_operator_console_credentials", "test_ig_readiness_observation_durability"),
    "T12": ("test_bot_helper_operator", "test_operator_console_dom", "test_operator_console_http", "test_operator_console_execution", "test_operator_console_projection"),
    "T13": ("test_ig_readiness_observation_durability",),
    "T14": ("test_bot_helper_review", "test_bot_helper_operator", "test_ig_predemo_safety", "test_ig_cand001_shadow_e2e"),
    "T15": (),
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_name(value: str) -> str:
    # Parameter display IDs can contain deliberate credential fixtures. Keep only
    # module/function identifiers plus an irreversible case identifier.
    base = value.split("[", 1)[0]
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.]{0,240}", base):
        base = "UNCLASSIFIED_TEST"
    return base


def read_results(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    tree = ET.parse(path)
    results = []
    for case in tree.iter("testcase"):
        name = case.get("name", "")
        module = safe_name(case.get("classname", ""))
        status = "ERROR" if case.find("error") is not None else (
            "FAIL" if case.find("failure") is not None else (
                "SKIPPED" if case.find("skipped") is not None else "PASS"))
        results.append({"module": module, "test": safe_name(name),
                        "case_sha256": sha((module + "::" + name).encode()), "status": status})
    return results


def summarize(cases: list[dict]) -> dict:
    counts = dict(Counter(case["status"] for case in cases))
    if not cases:
        status = "NOT_EXECUTED"
    elif counts.get("FAIL", 0) or counts.get("ERROR", 0):
        status = "FAIL"
    elif counts.get("SKIPPED", 0):
        status = "INCOMPLETE"
    else:
        status = "PASS"
    return {"status": status, "executed_cases": len(cases), "counts": counts, "cases": cases}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--pass-name", choices=("pass1", "pass2"), required=True)
    args = parser.parse_args()
    destination = args.output_dir.resolve() / args.pass_name
    destination.mkdir(parents=True, exist_ok=False)
    (destination / "attempt.json").write_text(json.dumps({
        "schema": "DAX_BOT_HELPER_ACCEPTANCE_ATTEMPT_V1",
        "pass_name": args.pass_name, "status": "STARTED_NOT_ACCEPTED",
        "evidence_scope": "SYNTHETIC", "execution_capability": "NONE",
        "order_execution_enabled": False,
    }, sort_keys=True) + "\n")
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(str(ROOT / part) for part in ("src", "scripts"))
    env["BOT_HELPER_PASS"] = "1" if args.pass_name == "pass1" else "2"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    imported = subprocess.run([sys.executable, "-c", "from daxlab.runtime import bot_helper; print(bot_helper.__file__)"],
                              cwd=ROOT, env=env, capture_output=True, text=True, check=True)
    imported_path = Path(imported.stdout.strip()).resolve()
    if not imported_path.is_relative_to(ROOT / "src"):
        raise RuntimeError("ACCEPTANCE_WRONG_IMPORT_OWNER")
    modules = {module for values in GROUP_MODULES.values() for module in values}
    modules.update(path.stem for path in (ROOT / "tests").glob("test_bot_helper*.py"))
    test_paths = [f"tests/{module}.py" for module in sorted(modules)]
    missing = [path for path in test_paths if not (ROOT / path).is_file()]
    if missing:
        raise RuntimeError("ACCEPTANCE_REQUIRED_TEST_MISSING")
    def source_snapshot():
        patterns = ("src/daxlab/runtime/*.py", "src/daxlab/adapters/*.py", "src/daxlab/domain/*.py",
                    "scripts/run_bot_helper_acceptance.py", "scripts/ig_cand001_shadow_e2e.py",
                    "scripts/run_ig_predemo_readiness_2238.py", "scripts/serve_operator_console.py",
                    "tests/fixtures/bot_helper_acceptance_v1.json", "web/operator.*", *test_paths)
        return {str(path.relative_to(ROOT)): sha(path.read_bytes())
                for pattern in patterns for path in ROOT.glob(pattern)}
    source_before = source_snapshot()
    started = datetime.now(timezone.utc).isoformat()
    with tempfile.TemporaryDirectory(prefix="bot-helper-acceptance-") as temporary:
        junit = Path(temporary) / "raw-junit.xml"
        # Raw assertion output exists only in bounded child capture/temporary XML.
        # Do not publish arbitrary provider/exception/parameter text.
        completed = subprocess.run([sys.executable, "-m", "pytest", *test_paths, "-q",
                                    "--disable-warnings", f"--junitxml={junit}"],
                                   cwd=ROOT, env=env, capture_output=True, text=True, timeout=1200)
        cases = read_results(junit)
    group_results = {}
    for group, mapping in GROUP_MODULES.items():
        selected = [case for case in cases if case["module"].split(".")[-1] in mapping
                    or (case["module"].endswith("test_bot_helper_acceptance")
                        and case["test"].startswith(f"test_{group}_"))]
        group_results[group] = summarize(selected)
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                          text=True, check=True).stdout.strip()
    changed = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True,
                             text=True, check=True).stdout
    hashes = source_snapshot()
    source_stable = hashes == source_before
    summary = summarize(cases)
    passed = (source_stable and completed.returncode == 0 and summary["status"] == "PASS"
              and all(g["status"] == "PASS" for g in group_results.values()))
    report = {"schema": "DAX_BOT_HELPER_ACCEPTANCE_RUN_V1", "pass_name": args.pass_name,
              "started_at": started, "completed_at": datetime.now(timezone.utc).isoformat(),
              "status": "PASS" if passed else "ACCEPTANCE_INCOMPLETE_OR_FAILED",
              "pytest_exit_code": completed.returncode, "git_head": head,
              "worktree_dirty": bool(changed), "imported_source": str(imported_path.relative_to(ROOT)),
              "source_file_sha256": source_before, "source_snapshot_stable": source_stable,
              "source_after_sha256": sha(json.dumps(hashes, sort_keys=True).encode()),
              "evidence_scope": "SYNTHETIC",
              "real_host_coverage": "NOT_PROVEN", "real_broker_coverage": "NOT_PROVEN",
              "execution_capability": "NONE", "order_execution_enabled": False,
              "selected_tests": test_paths, "summary": summary, "groups": group_results,
              "coverage_caveat": "MEASURED_SELECTED_ASSERTIONS; NOT_ALL_REGISTRY_FACETS_SOLVED",
              "browser_required": env.get("BOT_HELPER_REQUIRE_BROWSER") == "1",
              "artifact_retention_days": 30,
              "artifact_upload_status": "OWNED_BY_CI_UPLOAD_STEP_NOT_PROVEN_BY_LOCAL_RUN"}
    (destination / "acceptance.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    safe_junit = ET.Element("testsuite", name="bot-helper-acceptance", tests=str(len(cases)))
    for case in cases:
        element = ET.SubElement(safe_junit, "testcase", classname=case["module"],
                                name=case["test"] + "_" + case["case_sha256"][:12])
        if case["status"] != "PASS":
            ET.SubElement(element, {"FAIL": "failure", "ERROR": "error", "SKIPPED": "skipped"}[case["status"]],
                          message=case["status"])
    ET.ElementTree(safe_junit).write(destination / "junit.xml", encoding="utf-8", xml_declaration=True)
    print(json.dumps({"pass": args.pass_name, "status": report["status"],
                      "counts": summary["counts"],
                      "groups": {key: value["status"] for key, value in group_results.items()}}))
    return 0 if passed else 2


if __name__ == "__main__":
    try:
        exit_code = main()
    except Exception:
        print(json.dumps({"status": "ACCEPTANCE_HARNESS_FAILED",
                          "execution_capability": "NONE", "order_execution_enabled": False}))
        exit_code = 2
    raise SystemExit(exit_code)
