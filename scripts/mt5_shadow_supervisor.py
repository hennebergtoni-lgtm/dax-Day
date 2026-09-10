#!/usr/bin/env python3
"""Continuous credential-free Windows MT5 read-only SHADOW supervisor.

This script has no order API. It reuses the existing `mt5_windows_probe.collect_probe`
function, persists a provenance-bound SHADOW resume envelope and heartbeat, and
relies on Windows Task Scheduler for process restart after exit/crash.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import signal
import threading

from mt5_windows_probe import collect_probe

from daxlab.runtime.atomic_json import atomic_write_json, read_json_object
from daxlab.runtime.mt5_shadow_integration import mt5_shadow_resume_payload
from daxlab.runtime.mt5_shadow_supervisor import (
    load_mt5_resume_payload,
    process_mt5_shadow_cycle,
    supervisor_error_heartbeat,
    supervisor_stopped_heartbeat,
)
from daxlab.runtime.single_instance import SingleInstanceLock

_IDENTITY = "DAXLAB_MT5_SHADOW_SUPERVISOR_V1"


def _load_resume(path: Path):
    if not path.exists():
        return None
    return load_mt5_resume_payload(read_json_object(path))


def _load_previous_bundle(path: Path):
    if not path.exists():
        return None
    return read_json_object(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="DE40")
    parser.add_argument("--bars", type=int, default=20)
    parser.add_argument("--max-age-seconds", type=float, default=600.0)
    parser.add_argument("--broker-timezone", required=True)
    parser.add_argument("--interval-seconds", type=float, default=60.0)
    parser.add_argument("--state-dir", default=".runtime/mt5_shadow")
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()

    if args.interval_seconds < 1.0:
        raise SystemExit("--interval-seconds must be >= 1")
    if args.bars < 2:
        raise SystemExit("--bars must be >= 2")

    state_dir = Path(args.state_dir).resolve()
    heartbeat_path = state_dir / "heartbeat.json"
    resume_path = state_dir / "resume.json"
    latest_bundle_path = state_dir / "latest_bundle.json"
    rejected_bundle_path = state_dir / "rejected_bundle.json"
    lock_path = state_dir / "supervisor.lock"
    state_dir.mkdir(parents=True, exist_ok=True)

    stop = threading.Event()

    def request_stop(signum, frame) -> None:
        del signum, frame
        stop.set()

    signal.signal(signal.SIGINT, request_stop)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, request_stop)

    lock = SingleInstanceLock(path=lock_path, identity=_IDENTITY)
    try:
        lock.acquire()
    except Exception:
        # A losing second instance must never overwrite the legitimate owner's
        # shared heartbeat or resume state.
        return 4

    try:
        try:
            resume_state = _load_resume(resume_path)
            previous_bundle_payload = _load_previous_bundle(latest_bundle_path)
        except Exception:
            atomic_write_json(
                heartbeat_path,
                supervisor_error_heartbeat(error_code="RESUME_OR_BUNDLE_STATE_INVALID"),
            )
            return 3

        while not stop.is_set():
            try:
                bundle_payload = collect_probe(
                    configured_symbol=args.symbol,
                    bars=args.bars,
                    max_age_seconds=args.max_age_seconds,
                    broker_timezone=args.broker_timezone,
                )
                cycle = process_mt5_shadow_cycle(
                    bundle_payload,
                    resume_state=resume_state,
                    single_instance_lock_held=lock.held,
                    previous_bundle_payload=previous_bundle_payload,
                )

                if cycle.heartbeat.get("cross_cycle_status") == "BLOCKED":
                    atomic_write_json(rejected_bundle_path, bundle_payload)
                else:
                    atomic_write_json(latest_bundle_path, bundle_payload)
                    previous_bundle_payload = bundle_payload
                    if rejected_bundle_path.exists():
                        rejected_bundle_path.unlink()

                if cycle.resume_state is not None:
                    resume_state = cycle.resume_state
                    atomic_write_json(resume_path, mt5_shadow_resume_payload(resume_state))
                atomic_write_json(heartbeat_path, cycle.heartbeat)
            except Exception:
                atomic_write_json(
                    heartbeat_path,
                    supervisor_error_heartbeat(error_code="PROBE_OR_CYCLE_FAILED"),
                )
                if args.once:
                    return 2

            if args.once:
                return 0
            stop.wait(args.interval_seconds)
    finally:
        lock.release()
        if stop.is_set():
            atomic_write_json(heartbeat_path, supervisor_stopped_heartbeat())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
