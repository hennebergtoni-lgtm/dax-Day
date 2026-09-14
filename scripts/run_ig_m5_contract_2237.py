"""One-session Windows closeout for the canonical IG M5 contract.

The runner performs one authenticated read-only session, a fresh Candidate cycle,
waits for the next true M5 close, performs one resume cycle, validates Operator
projection, and preserves both evidence envelopes. It has no dealing capability.
"""
from __future__ import annotations

import argparse
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timedelta, timezone
import io
import json
import os
from pathlib import Path
import platform
import re
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import ig_cand001_shadow_e2e as candidate  # noqa: E402
import ig_demo_readonly_probe as probe  # noqa: E402
from daxlab.adapters.ig_rest_readonly import IgDemoReadOnlyClient, IgReadOnlyError  # noqa: E402
from daxlab.runtime.atomic_json import atomic_write_json, read_json_object  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
NAMESPACE = ".runtime/ig_m5_contract_2237_interval_start_v2_attempt_01"
CREDENTIALS = Path(r"C:\Users\Mandy\ig_demo.env")
WAIT_CHUNK_SECONDS = 30
RESUME_OFFSET_SECONDS = 5
CLOCK_DRIFT_SECONDS = 5
SCHEMA = "DAX_IG_M5_CONTRACT_2237_HOST_CLOSEOUT_V1"

ERROR_CODES = frozenset({
    "GOVERNANCE_WINDOWS_HOST_REQUIRED",
    "GOVERNANCE_INVALID_HEAD",
    "GOVERNANCE_HEAD_MISMATCH",
    "GOVERNANCE_TRACKED_DRIFT",
    "GOVERNANCE_UNTRACKED_CODE",
    "GOVERNANCE_IMPORT_PARITY",
    "STATE_INVALID_NAMESPACE",
    "STATE_NAMESPACE_SYMLINK",
    "STATE_NAMESPACE_EXISTS",
    "STATE_PUBLICATION_FAILED",
    "STATE_CHANGED_OVERLAP",
    "STATE_ANCHOR_NOT_FOUND",
    "STATE_NO_NEW_FINALIZED_M5",
    "DATA_IG_M5_PROVIDER_CONTRACT_UNVERIFIED",
    "DATA_STALE_AT_PROCESSING",
    "DATA_TEST_FAILED",
    "IG_AUTHENTICATION_FAILED_NO_RETRY",
    "IG_SESSION_READ_FAILED_NO_RETRY",
    "IG_SESSION_CLEANUP_FAILED",
    "CLOCK_INVALID_UTC",
    "CLOCK_MOVED_BACKWARDS",
    "CLOCK_DISCONTINUITY",
    "SAFETY_EXECUTION_CAPABILITY",
    "RUNNER_UNEXPECTED_FAILURE",
})


class CloseoutBlocked(RuntimeError):
    """Fixed, credential-free failure codes only."""


def require(condition: bool, code: str) -> None:
    if code not in ERROR_CODES:
        raise RuntimeError("undeclared closeout error code")
    if not condition:
        raise CloseoutBlocked(code)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def resume_target(latest_close: datetime) -> datetime:
    require(
        latest_close.tzinfo is not None and latest_close.utcoffset() == timedelta(0),
        "CLOCK_INVALID_UTC",
    )
    return latest_close + timedelta(minutes=5, seconds=RESUME_OFFSET_SECONDS)


def wait_for(
    target: datetime,
    *,
    clock=now_utc,
    sleep=time.sleep,
    monotonic=time.monotonic,
) -> None:
    origin, tick = clock(), monotonic()
    require(origin.tzinfo is not None and origin.utcoffset() == timedelta(0), "CLOCK_INVALID_UTC")
    previous = origin
    while True:
        current = clock()
        require(current >= previous, "CLOCK_MOVED_BACKWARDS")
        require(
            abs((current - origin).total_seconds() - (monotonic() - tick))
            <= CLOCK_DRIFT_SECONDS,
            "CLOCK_DISCONTINUITY",
        )
        if current >= target:
            return
        previous = current
        sleep(min(WAIT_CHUNK_SECONDS, (target - current).total_seconds()))


def _exclusive_json(path: Path, payload: dict[str, object]) -> None:
    try:
        with path.open("x", encoding="utf-8") as stream:
            json.dump(payload, stream, sort_keys=True, indent=2, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        raise CloseoutBlocked("STATE_PUBLICATION_FAILED") from None


def _cycle(
    client: IgDemoReadOnlyClient,
    *,
    head: str,
    prior: dict[str, object] | None,
    clock=now_utc,
) -> dict[str, object]:
    candidate.check_code(head)
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        broker_view, rows = probe.collect_authenticated_probe(
            client,
            epic=candidate.DEFAULT_EPIC,
            instrument_id=candidate.DEFAULT_INSTRUMENT_ID,
            bars=40,
        )
    observed_at = clock()
    payload = candidate.process_live_window(
        broker_view,
        rows,
        head=head,
        observed_at=observed_at,
        prior=prior,
    )
    payload["exported_at_utc"] = clock().isoformat()
    payload["fingerprint"] = candidate._fingerprint(payload)
    candidate.validate_evidence(payload, head=head, now=clock())
    return payload


def run(
    expected_head: str,
    *,
    namespace: str = NAMESPACE,
    credentials_file: Path = CREDENTIALS,
    root: Path = REPO,
    clock=now_utc,
    wait=wait_for,
    client_factory=IgDemoReadOnlyClient,
) -> tuple[int, dict[str, object]]:
    summary: dict[str, object] = {
        "schema": SCHEMA,
        "status": "BLOCKED",
        "error_code": None,
        "exact_code_head": None,
        "namespace": namespace,
        "session_model": "ONE_LOGIN_TWO_READ_CYCLES_ONE_CLEANUP",
        "fresh_start": "NOT_RUN",
        "resume": "NOT_RUN",
        "operator": "NOT_RUN",
        "state_changed_overlap": "STRICT",
        "execution_capability": "NONE",
        "order_execution_enabled": False,
        "broker_side_effects": 0,
    }
    directory: Path | None = None
    client: IgDemoReadOnlyClient | None = None
    try:
        require(platform.system() == "Windows", "GOVERNANCE_WINDOWS_HOST_REQUIRED")
        require(re.fullmatch(r"[0-9a-f]{40}", expected_head) is not None, "GOVERNANCE_INVALID_HEAD")
        summary["exact_code_head"] = candidate.check_code(expected_head)
        candidate.require_verified_live_provider_contract()
        require(
            re.fullmatch(
                r"\.runtime/ig_m5_contract_2237_interval_start_v2_attempt_[0-9]{2,}",
                namespace,
            )
            is not None,
            "STATE_INVALID_NAMESPACE",
        )
        root = root.resolve()
        runtime = root / ".runtime"
        require(not runtime.is_symlink(), "STATE_NAMESPACE_SYMLINK")
        runtime.mkdir(exist_ok=True)
        directory = root / namespace
        require(not os.path.lexists(directory), "STATE_NAMESPACE_EXISTS")
        directory.mkdir()
        credentials = probe._credentials_from_file(credentials_file)
        client = client_factory(credentials=credentials)
        require(
            client.execution_capability == "NONE"
            and client.order_execution_enabled is False,
            "SAFETY_EXECUTION_CAPABILITY",
        )
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            client.login()
        fresh = _cycle(client, head=expected_head, prior=None, clock=clock)
        atomic_write_json(directory / "evidence.json", fresh)
        _exclusive_json(directory / "FRESH_START.json", fresh)
        summary["fresh_start"] = "SUCCESS"

        latest = candidate.utc(fresh["latest_finalized_m5"]["close_time"])
        wait(resume_target(latest))
        prior = read_json_object(directory / "evidence.json")
        resume = _cycle(client, head=expected_head, prior=prior, clock=clock)
        require(
            resume["recovery_state"] == "RESUME_ANCHOR_RECONCILED",
            "STATE_ANCHOR_NOT_FOUND",
        )
        atomic_write_json(directory / "evidence.json", resume)
        _exclusive_json(directory / "RESUME.json", resume)
        summary["resume"] = "SUCCESS"
        candidate.validate_evidence(resume, head=expected_head, now=clock())
        _exclusive_json(directory / "OPERATOR.json", {
            "schema": "DAX_IG_M5_CONTRACT_2237_OPERATOR_V1",
            "exact_code_head": expected_head,
            "evidence_fingerprint": resume["fingerprint"],
            "operator_snapshot": resume["operator_snapshot"],
            "operator_projection": resume["operator_projection"],
            "execution_capability": "NONE",
            "order_execution_enabled": False,
        })
        summary["operator"] = "SUCCESS"
        summary["status"] = "SUCCESS"
    except KeyboardInterrupt:
        summary["error_code"] = "RUNNER_UNEXPECTED_FAILURE"
    except IgReadOnlyError as exc:
        summary["error_code"] = (
            "IG_AUTHENTICATION_FAILED_NO_RETRY"
            if re.search(r"\bHTTP 401\b", str(exc))
            else "IG_SESSION_READ_FAILED_NO_RETRY"
        )
    except Exception as exc:
        code = str(exc)
        summary["error_code"] = code if code in ERROR_CODES else "RUNNER_UNEXPECTED_FAILURE"
    finally:
        if client is not None:
            try:
                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    client.logout()
            except Exception:
                if summary["status"] == "SUCCESS":
                    summary["status"] = "BLOCKED"
                    summary["error_code"] = "IG_SESSION_CLEANUP_FAILED"
        if directory is not None and not (directory / "SUMMARY.json").exists():
            try:
                _exclusive_json(directory / "SUMMARY.json", summary)
            except Exception:
                summary["status"] = "BLOCKED"
                summary["error_code"] = "STATE_PUBLICATION_FAILED"
    return (0 if summary["status"] == "SUCCESS" else 2), summary


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--namespace", default=NAMESPACE)
    parser.add_argument("--credentials-file", type=Path, default=CREDENTIALS)
    args = parser.parse_args(argv)
    code, summary = run(
        args.expected_head,
        namespace=args.namespace,
        credentials_file=args.credentials_file,
    )
    print(json.dumps(summary, sort_keys=True, allow_nan=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
