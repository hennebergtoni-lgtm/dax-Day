"""Exercise idempotent detail-row write semantics in an isolated Neon schema."""
from __future__ import annotations

import json
import os
from uuid import uuid4

import psycopg
from psycopg import sql

from daxlab.detail_import import plan_detail_rows, reconcile_planned_rows
from daxlab.import_guard import validate_postimport


def _fixture() -> list[dict[str, object]]:
    return [
        {
            "wf": 1,
            "cost": "normal",
            "variant_index": 120,
            "trades": 12,
            "return_r": 2.5,
            "pf": 1.4,
            "avg_r": 0.2,
            "max_dd_r": -3.0,
        },
        {
            "wf": 2,
            "cost": "normal",
            "variant_index": 84,
            "trades": 9,
            "return_r": -1.5,
            "pf": 0.8,
            "avg_r": -0.16,
            "max_dd_r": -4.0,
        },
    ]


def _existing(conn: psycopg.Connection) -> dict[str, str]:
    rows = conn.execute("select source_row_id, payload_sha256 from detail_row_staging").fetchall()
    return {str(row_id): str(payload_sha) for row_id, payload_sha in rows}


def _apply(conn: psycopg.Connection, planned) -> tuple[int, int]:
    plan = reconcile_planned_rows(planned, existing_payload_hashes=_existing(conn))
    blockers = validate_postimport(plan.reconciliation)
    if blockers:
        raise RuntimeError(f"detail import drill blocked: {blockers}")
    for row in plan.to_insert:
        conn.execute(
            "insert into detail_row_staging(source_row_id, payload_sha256, payload) values (%s, %s, %s::jsonb)",
            (row.source_row_id, row.payload_sha256, json.dumps(row.payload, default=str)),
        )
    return plan.reconciliation.inserted_rows, plan.reconciliation.unchanged_rows


def main() -> None:
    database_url = os.environ.get("NEON_DATABASE_URL")
    if not database_url:
        raise SystemExit("NEON_DATABASE_URL is not configured")
    schema = f"daxlab_import_drill_{uuid4().hex[:12]}"
    planned = plan_detail_rows(
        experiment_key="V112_REFERENCE_V1",
        detail_kind="WF_METRICS",
        rows=_fixture(),
    )

    with psycopg.connect(database_url, connect_timeout=15, autocommit=True) as conn:
        try:
            conn.execute(sql.SQL("create schema {}").format(sql.Identifier(schema)))
            conn.execute(sql.SQL("set search_path to {}, public").format(sql.Identifier(schema)))
            conn.execute(
                "create table detail_row_staging ("
                "source_row_id text primary key, payload_sha256 text not null, payload jsonb not null)"
            )

            with conn.transaction():
                inserted, unchanged = _apply(conn, planned)
                if (inserted, unchanged) != (2, 0):
                    raise RuntimeError("first import drill reconciliation mismatch")

            with conn.transaction():
                inserted, unchanged = _apply(conn, planned)
                if (inserted, unchanged) != (0, 2):
                    raise RuntimeError("idempotent retry drill reconciliation mismatch")

            row_count_before = conn.execute("select count(*) from detail_row_staging").fetchone()[0]
            victim = planned[0]
            conn.execute(
                "update detail_row_staging set payload_sha256 = %s where source_row_id = %s",
                ("0" * 64, victim.source_row_id),
            )
            try:
                with conn.transaction():
                    _apply(conn, planned)
            except RuntimeError as exc:
                if "CONFLICTING_ROWS" not in str(exc):
                    raise
            else:
                raise RuntimeError("conflicting import drill unexpectedly committed")

            row_count_after = conn.execute("select count(*) from detail_row_staging").fetchone()[0]
            if row_count_after != row_count_before:
                raise RuntimeError("conflict drill changed staging row count")

            print(
                "Detail import DB drill OK | first=2 inserts | retry=2 unchanged | "
                "conflict=blocked | productive_tables=untouched"
            )
        finally:
            conn.execute("set search_path to public")
            conn.execute(sql.SQL("drop schema if exists {} cascade").format(sql.Identifier(schema)))


if __name__ == "__main__":
    main()
