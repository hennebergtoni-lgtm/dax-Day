"""Apply versioned SQL migrations to the configured research database."""

from __future__ import annotations

import os
from pathlib import Path

import psycopg

MIGRATION_DIR = Path(__file__).resolve().parents[1] / "db" / "migrations"


def main() -> None:
    database_url = os.environ.get("NEON_DATABASE_URL")
    if not database_url:
        raise SystemExit("NEON_DATABASE_URL is not configured")

    migration_files = sorted(MIGRATION_DIR.glob("*.sql"))
    if not migration_files:
        raise SystemExit("no database migrations found")

    with psycopg.connect(database_url, connect_timeout=15) as connection:
        for migration_file in migration_files:
            sql = migration_file.read_text(encoding="utf-8")
            connection.execute(sql)
            print(f"Applied migration: {migration_file.name}")


if __name__ == "__main__":
    main()
