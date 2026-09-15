#!/usr/bin/env python3
"""Read the latest CAND-001 operator snapshot from Neon as credential-free JSON.

This is a server/operator-side read adapter, not a browser endpoint. The database
credential is read only from the process environment and is never emitted.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os

import psycopg

from daxlab.runtime.candidate_operator_query import build_candidate_operator_current


def read_current(database_url: str) -> dict[str, object]:
    with psycopg.connect(database_url, connect_timeout=15) as connection:
        row = connection.execute(
            "select payload from cand001_operator_current limit 1"
        ).fetchone()
    if row is None:
        return {
            "schema_version": "DAXLAB_CAND001_OPERATOR_CURRENT_V1",
            "queried_at_utc": datetime.now(timezone.utc).isoformat(),
            "source": "cand001_operator_current",
            "state": "NO_DATA",
            "execution_capability": "NONE",
            "order_execution_enabled": False,
        }
    payload = row[0]
    if not isinstance(payload, dict):
        raise RuntimeError("Candidate current view payload is not a JSON object")
    return build_candidate_operator_current(
        payload,
        queried_at=datetime.now(timezone.utc),
    ).as_dict()


def main() -> None:
    database_url = os.environ.get("NEON_DATABASE_URL")
    if not database_url:
        raise SystemExit("NEON_DATABASE_URL is not configured")
    print(json.dumps(read_current(database_url), sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
