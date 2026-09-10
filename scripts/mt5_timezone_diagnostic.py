#!/usr/bin/env python3
"""Read-only diagnostic for broker timezone candidates from an MT5 evidence bundle."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Mapping
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from daxlab.runtime.mt5_broker_session import server_wall_clock_epoch_to_utc


SCHEMA_VERSION = "DAXLAB_MT5_TIMEZONE_DIAGNOSTIC_V1"


def _note_delta(notes: list[Any], prefix: str) -> float | None:
    for note in notes:
        text = str(note)
        if text.startswith(prefix):
            try:
                return float(text.split("=", 1)[1])
            except (IndexError, ValueError):
                return None
    return None


def diagnose_timezone_candidate(
    bundle: Mapping[str, Any], *, candidate_timezone: str
) -> dict[str, Any]:
    candidate = candidate_timezone.strip()
    blockers: list[str] = []
    try:
        ZoneInfo(candidate)
    except (ZoneInfoNotFoundError, ValueError):
        blockers.append("CANDIDATE_TIMEZONE_INVALID")

    notes = list(bundle.get("notes") or [])
    raw_delta = _note_delta(notes, "RAW_TICK_CLOCK_DELTA_SECONDS=")
    normalized_delta = _note_delta(notes, "NORMALIZED_TICK_CLOCK_DELTA_SECONDS=")
    if raw_delta is None:
        blockers.append("RAW_TICK_DELTA_MISSING")
    if normalized_delta is None:
        blockers.append("NORMALIZED_TICK_DELTA_MISSING")

    feed = bundle.get("closed_m5_feed") or {}
    if feed.get("broker_timezone") != candidate:
        blockers.append("FEED_TIMEZONE_MISMATCH")
    if feed.get("timestamp_interpretation") != "EXPLICIT_BROKER_WALL_CLOCK":
        blockers.append("FEED_TIMESTAMP_INTERPRETATION_NOT_EXPLICIT")

    host = bundle.get("host_probe") or {}
    if host.get("order_execution_enabled") is not False:
        blockers.append("ORDER_EXECUTION_NOT_FALSE")
    if host.get("broker_timezone") != candidate:
        blockers.append("HOST_TIMEZONE_MISMATCH")

    improvement_seconds = None
    if raw_delta is not None and normalized_delta is not None:
        improvement_seconds = abs(raw_delta) - abs(normalized_delta)

    # Diagnostic only: even a strong improvement is not proof by itself.
    return {
        "schema_version": SCHEMA_VERSION,
        "candidate_timezone": candidate or None,
        "raw_tick_delta_seconds": raw_delta,
        "normalized_tick_delta_seconds": normalized_delta,
        "absolute_delta_improvement_seconds": improvement_seconds,
        "internally_consistent": not blockers,
        "broker_timezone_verified": False,
        "verification_state": "REQUIRES_EXPLICIT_HOST_CLOCK_REVIEW",
        "blockers": blockers,
        "execution_capability": "NONE",
        "order_execution_enabled": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle")
    parser.add_argument("--candidate-timezone", required=True)
    args = parser.parse_args()
    payload = json.loads(Path(args.bundle).read_text(encoding="utf-8"))
    result = diagnose_timezone_candidate(payload, candidate_timezone=args.candidate_timezone)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
