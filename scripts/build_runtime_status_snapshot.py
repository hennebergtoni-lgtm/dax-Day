#!/usr/bin/env python3
"""Build a compact public read-only MT5 SHADOW runtime snapshot from Neon.

This script reads telemetry only. It has no MetaTrader5 dependency, no control
path to Windows, and no order capability. The generated JSON is an operator
read surface, not a canonical research artifact.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any

import psycopg

_SCHEMA = "DAXLAB_MT5_SHADOW_RUNTIME_STATUS_V1"
_OUTPUT = Path(__file__).resolve().parents[1] / "web" / "runtime_status.json"


def _iso(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat()
    return str(value)


def _latest_heartbeat(conn: psycopg.Connection) -> dict[str, Any] | None:
    row = conn.execute(
        """
        select observed_at_utc, status, symbol, closed_m5_bars,
               latest_closed_bar_age_seconds, processed_total, new_decisions,
               duplicates_suppressed, evidence_state, cross_cycle_status,
               cross_cycle_overlapping_bars, cross_cycle_identical_overlaps,
               cross_cycle_mutated_overlaps, blockers, history_archive_status,
               execution_capability, order_execution_enabled, payload_sha256
        from mt5_shadow_heartbeats
        order by observed_at_utc desc, id desc
        limit 1
        """
    ).fetchone()
    if row is None:
        return None
    return {
        "observed_at_utc": _iso(row[0]),
        "status": row[1],
        "symbol": row[2],
        "closed_m5_bars": row[3],
        "latest_closed_bar_age_seconds": row[4],
        "processed_total": row[5],
        "new_decisions": row[6],
        "duplicates_suppressed": row[7],
        "evidence_state": row[8],
        "cross_cycle_status": row[9],
        "cross_cycle_overlapping_bars": row[10],
        "cross_cycle_identical_overlaps": row[11],
        "cross_cycle_mutated_overlaps": row[12],
        "blockers": row[13],
        "history_archive_status": row[14],
        "execution_capability": row[15],
        "order_execution_enabled": row[16],
        "payload_sha256": row[17],
    }


def _bar_summary(conn: psycopg.Connection) -> dict[str, Any]:
    count_row = conn.execute("select count(*) from mt5_shadow_bars").fetchone()
    latest = conn.execute(
        """
        select symbol, open_time, open, high, low, close, bar_fingerprint,
               broker_timezone, timestamp_interpretation
        from mt5_shadow_bars
        order by open_time desc, id desc
        limit 1
        """
    ).fetchone()
    count = int(count_row[0]) if count_row is not None else 0
    if latest is None:
        return {"stored_bars": count, "latest": None}
    return {
        "stored_bars": count,
        "latest": {
            "symbol": latest[0],
            "open_time": _iso(latest[1]),
            "open": latest[2],
            "high": latest[3],
            "low": latest[4],
            "close": latest[5],
            "bar_fingerprint": latest[6],
            "broker_timezone": latest[7],
            "timestamp_interpretation": latest[8],
        },
    }


def build_snapshot(database_url: str) -> dict[str, Any]:
    generated_at = datetime.now(timezone.utc)
    with psycopg.connect(database_url, connect_timeout=15) as conn:
        heartbeat = _latest_heartbeat(conn)
        bars = _bar_summary(conn)

    if heartbeat is not None:
        if heartbeat["execution_capability"] != "NONE":
            raise RuntimeError("runtime snapshot rejected non-NONE execution capability")
        if heartbeat["order_execution_enabled"] is not False:
            raise RuntimeError("runtime snapshot rejected enabled order execution")

    return {
        "schema_version": _SCHEMA,
        "generated_at_utc": generated_at.isoformat(),
        "source": "NEON_MT5_SHADOW_TELEMETRY",
        "mode": "SHADOW",
        "read_only": True,
        "monitoring_only": True,
        "heartbeat_present": heartbeat is not None,
        "heartbeat": heartbeat,
        "bars": bars,
        "decisions_stream_state": "NOT_PERSISTED_YET",
        "execution_capability": "NONE",
        "order_execution_enabled": False,
    }


def main() -> None:
    database_url = os.environ.get("NEON_DATABASE_URL")
    if not database_url:
        raise SystemExit("NEON_DATABASE_URL is not configured")
    snapshot = build_snapshot(database_url)
    _OUTPUT.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "Runtime status snapshot OK | "
        f"heartbeat_present={snapshot['heartbeat_present']} | "
        f"stored_bars={snapshot['bars']['stored_bars']} | "
        "execution_capability=NONE | order_execution_enabled=false"
    )


if __name__ == "__main__":
    main()
