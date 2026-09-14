"""Bounded Windows orchestration of the existing RAW diagnostic, never Candidate processing."""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ig_raw_m5_timestamp_diagnostic as diagnostic  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
NAMESPACE = ".runtime/ig_raw_m5_truth_2233_v2_attempt_02"
CREDENTIALS = Path(r"C:\Users\Mandy\ig_demo.env")
PERIOD_SECONDS = 300
SAMPLE_OFFSET_SECONDS = 60  # Sampling position, NOT a provider-finalization grace.
SAMPLE_WINDOW_SECONDS = 60
WAIT_CHUNK_SECONDS = 30
CLOCK_DRIFT_SECONDS = 5
SCHEMA = "DAX_IG_RAW_TRUTH_ATTEMPT_V1"


class AttemptBlocked(RuntimeError):
    """Fixed codes only; never render exceptions from subprocesses or the provider."""


def require(condition, code):
    if not condition:
        raise AttemptBlocked(code)


def now_utc():
    return datetime.now(timezone.utc)


def schedule(start):
    require(start.utcoffset() == timedelta(0), "CLOCK_INVALID_UTC")
    boundary = start.replace(second=0, microsecond=0)
    boundary -= timedelta(minutes=boundary.minute % 5)
    boundary += timedelta(seconds=PERIOD_SECONDS)
    a = boundary + timedelta(seconds=SAMPLE_OFFSET_SECONDS)
    return {name: a + timedelta(seconds=index * PERIOD_SECONDS)
            for index, name in enumerate(("A", "B", "C"))}


def wait_for(target, *, clock=now_utc, sleep=time.sleep, monotonic=time.monotonic):
    origin, tick = clock(), monotonic()
    require(origin.utcoffset() == timedelta(0), "CLOCK_INVALID_UTC")
    previous = origin
    while True:
        current = clock()
        require(current.utcoffset() == timedelta(0), "CLOCK_INVALID_UTC")
        require(current >= previous, "CLOCK_MOVED_BACKWARDS")
        require(abs((current - origin).total_seconds() - (monotonic() - tick))
                <= CLOCK_DRIFT_SECONDS, "CLOCK_DISCONTINUITY")
        require(current < target + timedelta(seconds=SAMPLE_WINDOW_SECONDS),
                "RAW_SAMPLING_WINDOW_MISSED")
        if current >= target:
            return
        previous = current
        sleep(min(WAIT_CHUNK_SECONDS, (target - current).total_seconds()))


def execute(argv):
    # No shell, no inherited provider stdout/stderr, no retry, same Python interpreter.
    timeout = 30 if "--compare" in argv else 120
    result = subprocess.run(
        [sys.executable, str(REPO / "scripts/ig_raw_m5_timestamp_diagnostic.py"), *argv],
        cwd=REPO, capture_output=True, text=True, timeout=timeout, check=False,
    )
    # Only recognize a single fixed auth code; never project arbitrary child strings.
    code = "RAW_DIAGNOSTIC_FAILED" if result.returncode else None
    try:
        message = json.loads(result.stdout.strip())
        if message.get("error_code") == "IG_AUTHENTICATION_FAILED_NO_RETRY":
            code = "IG_AUTHENTICATION_FAILED_NO_RETRY"
    except (ValueError, AttributeError):
        pass
    return result.returncode, code


def read_snapshot(path, *, head, target):
    payload = diagnostic.read_json_object(path)
    diagnostic.validate_snapshot(payload)
    require(payload["exact_code_head"] == head, "GOVERNANCE_HEAD_MISMATCH")
    requested = diagnostic.utc(payload["request_started_at_utc"])
    observed = diagnostic.utc(payload["response_observed_at_utc"])
    require(target <= requested < target + timedelta(seconds=SAMPLE_WINDOW_SECONDS),
            "RAW_REQUEST_OUTSIDE_SAMPLING_WINDOW")
    require(observed >= requested, "CLOCK_INVALID_UTC")
    return payload


def publish_summary(directory, summary):
    # Final summary is written once with exclusive creation; never replace prior files.
    payload = {**summary, "fingerprint": diagnostic._fingerprint(summary)}
    with (directory / "SUMMARY.json").open("x", encoding="utf-8") as stream:
        json.dump(payload, stream, sort_keys=True, indent=2)
        stream.write("\n")


def run(expected_head, *, namespace=NAMESPACE, credentials_file=CREDENTIALS,
        clock=now_utc, wait=wait_for, executor=execute, check=None, root=REPO):
    check = check or diagnostic.check_code
    summary = {
        "schema": SCHEMA, "exact_head": None, "attempt_namespace": None,
        "started_at": clock().isoformat(), "finished_at": None,
        "sampling_offset_seconds": SAMPLE_OFFSET_SECONDS,
        "sampling_window_seconds": SAMPLE_WINDOW_SECONDS,
        "raw": {name: {"scheduled_at": None, "invoked_at": None, "requested": False,
                       "success": False, "exit": None, "status": "NOT_RUN",
                       "request_started_at_utc": None, "response_observed_at_utc": None,
                       "fingerprint": None} for name in ("A", "B", "C")},
        "compare": {name: {"status": "NOT_RUN", "exit": None, "fingerprint": None}
                    for name in ("AB", "BC")},
        "final_state": "ABORTED_FAIL_CLOSED", "error_code": None,
        "execution_capability": "NONE", "order_execution_enabled": False,
        "candidate_processing_performed": False,
        "timestamp_semantics": "UNKNOWN", "classification_state": "UNVERIFIED",
    }
    directory = None
    print("STEP 2233 RAW ATTEMPT", flush=True)
    try:
        require(platform.system() == "Windows", "GOVERNANCE_WINDOWS_HOST_REQUIRED")
        require(re.fullmatch(r"[0-9a-f]{40}", expected_head) is not None,
                "GOVERNANCE_INVALID_HEAD")
        summary["exact_head"] = check(expected_head)
        # Namespace is a restricted relative basename, never arbitrary provider/user text.
        require(re.fullmatch(r"\.runtime/ig_raw_m5_truth_2233_v2_attempt_[0-9]{2,}", namespace)
                is not None, "RAW_INVALID_ATTEMPT_NAMESPACE")
        summary["attempt_namespace"] = namespace
        root = root.resolve()
        runtime = root / ".runtime"
        require(not runtime.is_symlink(), "RAW_NAMESPACE_SYMLINK")
        runtime.mkdir(exist_ok=True)
        directory_candidate = root / namespace
        require(not os.path.lexists(directory_candidate), "RAW_ATTEMPT_NAMESPACE_EXISTS")
        require(credentials_file.is_file(), "RAW_CREDENTIALS_FILE_UNAVAILABLE")
        directory_candidate.mkdir()  # Atomic namespace claim; concurrent attempts STOP.
        directory = directory_candidate
        planned = schedule(clock())
        for name, target in planned.items():
            summary["raw"][name]["scheduled_at"] = target.isoformat()
        print(f"HEAD: {summary['exact_head']}", flush=True)
        print(f"NAMESPACE: {namespace}", flush=True)
        for name, target in planned.items():
            print(f"{name} scheduled: {target.isoformat()}", flush=True)
        captures = {}
        for name, target in planned.items():
            item = summary["raw"][name]
            print(f"WAITING FOR {name}", flush=True)
            wait(target)
            check(expected_head)
            require(target <= clock() < target + timedelta(seconds=SAMPLE_WINDOW_SECONDS),
                    "RAW_SAMPLING_WINDOW_MISSED")
            output = directory / f"{name}.json"
            require(not os.path.lexists(output), "RAW_OUTPUT_ALREADY_EXISTS")
            item.update(requested=True, status="RUNNING", invoked_at=clock().isoformat())
            try:
                exit_code, error = executor([
                    "--expected-head", expected_head, "--credentials-file", str(credentials_file),
                    "--output", str(output),
                ])
                item["exit"] = exit_code
                if exit_code:
                    raise AttemptBlocked("IG_AUTHENTICATION_FAILED_NO_RETRY"
                                         if error == "IG_AUTHENTICATION_FAILED_NO_RETRY"
                                         else "RAW_DIAGNOSTIC_FAILED")
                payload = read_snapshot(output, head=expected_head, target=target)
                item.update(success=True, status="SUCCESS",
                            request_started_at_utc=payload["request_started_at_utc"],
                            response_observed_at_utc=payload["response_observed_at_utc"],
                            fingerprint=payload["fingerprint"])
                captures[name] = payload
            except BaseException:
                item["status"] = "FAILED"
                raise
            finally:
                print(f"RAW {name}: {item['status']}\nExit: {item['exit']}", flush=True)
        for pair in ("AB", "BC"):
            check(expected_head)
            item = summary["compare"][pair]
            output = directory / f"{pair}.json"
            require(not os.path.lexists(output), "RAW_OUTPUT_ALREADY_EXISTS")
            item["status"] = "RUNNING"
            try:
                exit_code, _ = executor([
                    "--expected-head", expected_head, "--compare",
                    str(directory / f"{pair[0]}.json"), str(directory / f"{pair[1]}.json"),
                    "--output", str(output),
                ])
                item["exit"] = exit_code
                require(exit_code == 0, "RAW_COMPARE_FAILED")
                payload = diagnostic.read_json_object(output)
                expected = diagnostic.compare(captures[pair[0]], captures[pair[1]])
                require(payload == expected, "RAW_COMPARE_EVIDENCE_MISMATCH")
                item.update(status="SUCCESS", fingerprint=payload["fingerprint"])
            except BaseException:
                item["status"] = "FAILED"
                raise
        check(expected_head)
        summary["final_state"] = "SUCCESS"
    except KeyboardInterrupt:
        summary["error_code"] = "RAW_ATTEMPT_INTERRUPTED"
    except subprocess.TimeoutExpired:
        summary["error_code"] = "RAW_DIAGNOSTIC_TIMEOUT_NO_RETRY"
    except Exception as exc:
        allowed = {
            "GOVERNANCE_WINDOWS_HOST_REQUIRED", "GOVERNANCE_INVALID_HEAD",
            "GOVERNANCE_HEAD_MISMATCH", "GOVERNANCE_TRACKED_DRIFT",
            "GOVERNANCE_UNTRACKED_CODE", "GOVERNANCE_IMPORT_PARITY",
            "RAW_INVALID_ATTEMPT_NAMESPACE", "RAW_NAMESPACE_SYMLINK",
            "RAW_ATTEMPT_NAMESPACE_EXISTS", "RAW_CREDENTIALS_FILE_UNAVAILABLE",
            "CLOCK_INVALID_UTC", "CLOCK_MOVED_BACKWARDS", "CLOCK_DISCONTINUITY",
            "RAW_SAMPLING_WINDOW_MISSED", "RAW_REQUEST_OUTSIDE_SAMPLING_WINDOW",
            "RAW_OUTPUT_ALREADY_EXISTS", "IG_AUTHENTICATION_FAILED_NO_RETRY",
            "RAW_DIAGNOSTIC_FAILED", "RAW_COMPARE_FAILED", "RAW_COMPARE_EVIDENCE_MISMATCH",
        }
        summary["error_code"] = str(exc) if (
            isinstance(exc, (AttemptBlocked, diagnostic.HostTestBlocked)) and str(exc) in allowed
        ) else "RAW_ATTEMPT_FAILED"
    finally:
        summary["finished_at"] = clock().isoformat()
        if directory is not None:
            try:
                publish_summary(directory, summary)
            except Exception:
                summary.update(final_state="ABORTED_FAIL_CLOSED",
                               error_code="RAW_SUMMARY_PUBLICATION_FAILED")
        for name, item in summary["raw"].items():
            if item["status"] == "NOT_RUN":
                print(f"RAW {name}: NOT RUN", flush=True)
        for pair, item in summary["compare"].items():
            print(f"{pair} COMPARE: {item['status']}", flush=True)
        print(f"FINAL STATUS: {summary['final_state']}", flush=True)
        if summary["error_code"]:
            print(f"error_code: {summary['error_code']}", flush=True)
        # Preflight rejection intentionally creates no attempt; its safe summary is stdout only.
        print(json.dumps(summary, sort_keys=True), flush=True)
    return 0 if summary["final_state"] == "SUCCESS" else 2


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--namespace", default=NAMESPACE)
    parser.add_argument("--credentials-file", type=Path, default=CREDENTIALS)
    args = parser.parse_args(argv)
    # Suppress dependency diagnostics during orchestration; only fixed runner output is emitted.
    return run(args.expected_head, namespace=args.namespace, credentials_file=args.credentials_file)


if __name__ == "__main__":
    raise SystemExit(main())
