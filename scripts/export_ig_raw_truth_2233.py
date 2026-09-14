"""Offline, exclusive export of original Step2233 RAW evidence; never broker calls."""
from __future__ import annotations

import argparse
from datetime import timedelta
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ig_raw_m5_timestamp_diagnostic as raw  # noqa: E402
from daxlab.runtime.single_instance import SingleInstanceLock  # noqa: E402

EVIDENCE_HEAD = "2a99f96e06f7ce1f311c767dec43d236bb63eedd"
NAMESPACE = ".runtime/ig_raw_m5_truth_2233_v2_attempt_03"
FILES = ("A.json", "B.json", "C.json", "AB.json", "BC.json", "SUMMARY.json")
MAX_BYTES = 2_000_000


class ExportBlocked(RuntimeError):
    pass


def require(condition, code):
    if not condition:
        raise ExportBlocked(code)


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "RAW_EXPORT_DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def decode(data):
    require(len(data) <= MAX_BYTES, "RAW_EXPORT_RESOURCE_LIMIT")
    payload = json.loads(data.decode("utf-8"), object_pairs_hook=_pairs)
    require(isinstance(payload, dict), "RAW_EXPORT_INVALID_JSON")
    return payload


def validate_attempt(payloads):
    captures = {name: payloads[name + ".json"] for name in ("A", "B", "C")}
    for capture in captures.values():
        raw.validate_snapshot(capture)
        require(capture["exact_code_head"] == EVIDENCE_HEAD, "RAW_EXPORT_EVIDENCE_HEAD")
    for pair in ("AB", "BC"):
        require(payloads[pair + ".json"] == raw.compare(captures[pair[0]], captures[pair[1]]),
                "RAW_EXPORT_COMPARE_MISMATCH")
    summary = payloads["SUMMARY.json"]
    start, finish = raw.utc(summary["started_at"]), raw.utc(summary["finished_at"])
    require(start <= finish, "RAW_EXPORT_CLOCK")
    expected_raw = {}
    schedules = []
    for name, capture in captures.items():
        item = summary["raw"][name]
        scheduled = raw.utc(item["scheduled_at"])
        invoked = raw.utc(item["invoked_at"])
        requested = raw.utc(capture["request_started_at_utc"])
        observed = raw.utc(capture["response_observed_at_utc"])
        require(start <= scheduled <= invoked <= requested <= observed <= finish,
                "RAW_EXPORT_CLOCK")
        require(requested < scheduled + timedelta(seconds=60), "RAW_EXPORT_REQUEST_WINDOW")
        require(scheduled.minute % 5 == 1 and scheduled.second == scheduled.microsecond == 0,
                "RAW_EXPORT_SCHEDULE")
        schedules.append(scheduled)
        expected_raw[name] = {
            "scheduled_at": item["scheduled_at"], "invoked_at": item["invoked_at"],
            "requested": True, "success": True, "exit": 0, "status": "SUCCESS",
            "request_started_at_utc": capture["request_started_at_utc"],
            "response_observed_at_utc": capture["response_observed_at_utc"],
            "fingerprint": capture["fingerprint"],
        }
    require(all(b - a == timedelta(minutes=5) for a, b in zip(schedules, schedules[1:])),
            "RAW_EXPORT_SCHEDULE")
    expected = {
        "schema": "DAX_IG_RAW_TRUTH_ATTEMPT_V2", "exact_head": EVIDENCE_HEAD,
        "attempt_namespace": NAMESPACE,
        "session": {"model": "ONE_LOGIN_IN_MEMORY_V1", "login_attempted": True,
                    "login_success": True, "cleanup_attempted": True,
                    "cleanup_success": True, "cleanup_error_code": None},
        "started_at": summary["started_at"], "finished_at": summary["finished_at"],
        "sampling_offset_seconds": 60, "sampling_window_seconds": 60,
        "raw": expected_raw,
        "compare": {pair: {"status": "SUCCESS", "exit": 0,
                           "fingerprint": payloads[pair + ".json"]["fingerprint"]}
                    for pair in ("AB", "BC")},
        "final_state": "SUCCESS", "error_code": None,
        "execution_capability": "NONE", "order_execution_enabled": False,
        "candidate_processing_performed": False,
        "timestamp_semantics": "UNKNOWN", "classification_state": "UNVERIFIED",
    }
    expected["fingerprint"] = raw._fingerprint(expected)
    # Closed structural projection: unknown nested strings/fields cannot be exported.
    require(summary == expected, "RAW_EXPORT_SUMMARY_CONTRACT_OR_HASH")
    raw._assert_credential_free(summary)
    return captures


def review(payloads):
    captures = validate_attempt(payloads)
    return {
        "schema": "DAX_IG_RAW_REVIEW_V1", "evidence_head": EVIDENCE_HEAD,
        "classification": "OTHER_UNKNOWN", "classification_state": "UNKNOWN",
        "reason": "CROSS_BOUNDARY_MUTATIONS_ALONE_DO_NOT_IDENTIFY_INTERVAL_SEMANTICS",
        "provider_finalization": "UNKNOWN", "revision_bound_seconds": None,
        "candidate_processing_performed": False, "execution_capability": "NONE",
        "order_execution_enabled": False,
        "observations": {name: {"request_started_at": item["request_started_at_utc"],
                               "response_observed_at": item["response_observed_at_utc"],
                               "rows": item["raw_m5_count"], "fingerprint": item["fingerprint"]}
                         for name, item in captures.items()},
        "pairs": {pair: {"common": payloads[pair + ".json"]["common_raw_timestamp_count"],
                         "changed": payloads[pair + ".json"]["changed_raw_timestamp_count"],
                         "mutations": [row for row in payloads[pair + ".json"]["comparisons"]
                                       if row["changed_fields"]]}
                  for pair in ("AB", "BC")},
        "unchanged_observation_is_not_finality_proof": True,
        "hash_integrity_is_not_provider_authentication": True,
    }


def bundle_bytes(originals, *, runtime_head):
    require(set(originals) == set(FILES), "RAW_EXPORT_REQUIRED_FILES")
    require(re.fullmatch(r"[0-9a-f]{40}", runtime_head) is not None, "RAW_EXPORT_RUNTIME_HEAD")
    payloads = {name: decode(originals[name]) for name in FILES}
    report = review(payloads)
    manifest = {
        "schema": "DAX_IG_RAW_EXPORT_V1", "export_runtime_head": runtime_head,
        "evidence_head": EVIDENCE_HEAD, "namespace": NAMESPACE,
        "files": {name: {"sha256": hashlib.sha256(originals[name]).hexdigest(),
                         "size_bytes": len(originals[name]),
                         "fingerprint": payloads[name]["fingerprint"]}
                  for name in FILES},
        "classification": "OTHER_UNKNOWN", "execution_capability": "NONE",
        "order_execution_enabled": False, "broker_side_effects": 0,
    }
    manifest["fingerprint"] = raw._fingerprint(manifest)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in FILES:
            archive.writestr(name, originals[name])
        for name, value in (("MANIFEST.json", manifest), ("REVIEW.json", report)):
            archive.writestr(name, json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n")
    return buffer.getvalue(), manifest


def export(expected_head, *, root=None):
    head = raw.check_code(expected_head)
    root = Path(root or Path(__file__).resolve().parents[1]).resolve()
    runtime = root / ".runtime"
    source = root / NAMESPACE
    require(not runtime.is_symlink() and not source.is_symlink(), "RAW_EXPORT_SYMLINK")
    output = runtime / "ig_raw_truth_2233_attempt_03_originals.zip"
    temporary = output.with_suffix(".zip.partial")
    require(not os.path.lexists(output) and not os.path.lexists(temporary),
            "RAW_EXPORT_OUTPUT_EXISTS")
    originals = {}
    for name in FILES:
        path = source / name
        require(path.is_file() and not path.is_symlink(), "RAW_EXPORT_MISSING_OR_SYMLINK")
        require(path.stat().st_size <= MAX_BYTES, "RAW_EXPORT_RESOURCE_LIMIT")
        with path.open("rb") as stream:
            originals[name] = stream.read(MAX_BYTES + 1)
    content, manifest = bundle_bytes(originals, runtime_head=head)
    with SingleInstanceLock(runtime / "ig_raw_truth_2233_export.lock", "IG_RAW_EXPORT"):
        created = False
        try:
            with temporary.open("xb") as stream:
                created = True
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            require(all((source / name).read_bytes() == data for name, data in originals.items()),
                    "RAW_EXPORT_SOURCE_CHANGED")
            raw.check_code(head)
            os.link(temporary, output)  # Exclusive complete publication; never replace/fallback.
        finally:
            if created and temporary.is_file() and not temporary.is_symlink():
                temporary.unlink()
    return output, manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-head", required=True)
    args = parser.parse_args(argv)
    try:
        output, manifest = export(args.expected_head)
        print(json.dumps({"status": "SUCCESS", "bundle": str(output),
                          "manifest_fingerprint": manifest["fingerprint"],
                          "classification": "OTHER_UNKNOWN", "broker_side_effects": 0,
                          "execution_capability": "NONE", "order_execution_enabled": False}))
        return 0
    except Exception:
        print(json.dumps({"status": "BLOCKED", "error_code": "RAW_EXPORT_FAILED_CLOSED",
                          "prior_evidence_is_not_current": True, "broker_side_effects": 0,
                          "execution_capability": "NONE", "order_execution_enabled": False}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
