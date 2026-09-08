"""Database integrity gate for the research store.

This script is intentionally read-only. It verifies schema/migration health and
checks that frozen reference metadata cannot silently drift when present.
"""
from __future__ import annotations

import os

import psycopg

EXPECTED_MIGRATIONS = {"0001_research_core", "0002_reference_provenance"}
EXPECTED_ENGINE_SHA = "9561b9089c57c543798dc587ce240a729b7995230dd5d665a1bdd029f3990887"


def main() -> None:
    database_url = os.environ.get("NEON_DATABASE_URL")
    if not database_url:
        raise SystemExit("NEON_DATABASE_URL is not configured")

    with psycopg.connect(database_url, connect_timeout=15) as connection, connection.cursor() as cursor:
        cursor.execute("select version from schema_migrations")
        migrations = {row[0] for row in cursor.fetchall()}
        missing = EXPECTED_MIGRATIONS - migrations
        if missing:
            raise SystemExit(f"database integrity failed: missing migrations {sorted(missing)}")

        cursor.execute(
            "select sha256, frozen, metadata from engine_references where name = %s",
            ("V11.2 Exact Reference Engine",),
        )
        row = cursor.fetchone()
        if row is None:
            raise SystemExit("database integrity failed: frozen V11.2 engine reference missing")
        sha256, frozen, metadata = row
        if sha256 != EXPECTED_ENGINE_SHA or frozen is not True:
            raise SystemExit("database integrity failed: V11.2 engine reference drift")
        if not isinstance(metadata, dict):
            raise SystemExit("database integrity failed: V11.2 metadata is not JSON object")

        cursor.execute("select count(*) from experiments")
        experiments = cursor.fetchone()[0]
        cursor.execute("select count(*) from walk_forward_results")
        wf_rows = cursor.fetchone()[0]
        cursor.execute("select count(*) from trades")
        trade_rows = cursor.fetchone()[0]

    print(
        "Database integrity OK | "
        f"migrations={len(migrations)} | experiments={experiments} | "
        f"wf_rows={wf_rows} | trades={trade_rows} | clean_reference_persistence=UNVERIFIED"
    )


if __name__ == "__main__":
    main()
