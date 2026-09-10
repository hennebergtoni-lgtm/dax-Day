#!/usr/bin/env python3
"""Evaluate broker-timezone evidence without guessing or mutating MT5 state."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


SCHEMA_VERSION = "DAXLAB_MT5_BROKER_TIMEZONE_EVIDENCE_V1"


def evaluate_broker_timezone_evidence(
    probe_payload: Mapping[str, Any],
    *,
    candidate_timezone: str,
) -> dict[str, Any]:
    blockers: list[str] = []
    candidate = candidate_timezone.strip()
    if not candidate:
        blockers.append("CANDIDATE_TIMEZONE_MISSING")
        zone = None
    else:
        try:
            zone = ZoneInfo(candidate)
        except ZoneInfoNotFoundError:
            zone = None
            blockers.append("CANDIDATE_TIMEZONE_INVALID")

    if probe_payload.get("order_execution_enabled") is not False:
        blockers.append("ORDER_EXECUTION_NOT_FALSE")
    if probe_payload.get("broker_timezone") != candidate:
        blockers.append("PROBE_TIMEZONE_MISMATCH")
    if probe_payload.get("timestamp_interpretation") != "EXPLICIT_BROKER_WALL_CLOCK":
        blockers.append("TIMESTAMP_INTERPRETATION_NOT_EXPLICIT")

    observed_raw = probe_payload.get("observed_at_utc")
    try:
        observed = datetime.fromisoformat(str(observed_raw).replace("Z", "+00:00"))
        if observed.tzinfo is None:
            raise ValueError
        observed = observed.astimezone(timezone.utc)
    except (TypeError, ValueError):
        observed = None
        blockers.append("OBSERVED_AT_UTC_INVALID")

    # A valid IANA zone and internally consistent probe metadata are necessary
    # evidence, but not sufficient to prove the broker/server wall clock. The
    # real Windows host comparison must explicitly set host_clock_compared=True.
    host_clock_compared = probe_payload.get("host_clock_compared") is True
    if not host_clock_compared:
        blockers.append("HOST_CLOCK_COMPARISON_REQUIRED")

    verified = not blockers and zone is not None and observed is not None
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "VERIFIED" if verified else "UNVERIFIED",
        "candidate_timezone": candidate or None,
        "blockers": blockers,
        "broker_timezone_verified": verified,
        "execution_capability": "NONE",
        "order_execution_enabled": False,
    }
