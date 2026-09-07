"""Apply versioned SQL migrations to the configured research database."""

from __future__ import annotations

import os
from pathlib import Path

import psycopg

MIGRATION_DIR = Path(__file__).resolve().parents[1] / "db" / "migrations"


def migration_version(path: Path) -> str:
    return path.stem


def migration_files() -> list[Path]:
    files = sorted(MIGRATION_DIR.glob("*.sql"))
    versions = [migration_version(path) for path in files]
    if len(versions) != len(set(versions)):
        raise RuntimeError("duplicate database migration versions")
    return files


def applied_versions(connection: psycopg.Connection) -> set[str]:
    exists = connection.execute(
        "select to_regclass('public.schema_migrations') is not null"
    ).fetchone()[0]
    if not exists:
        return set()
    rows = connection.execute("select version from schema_migrations").fetchall()
    return {str(row[0]) for row in rows}


def main() -> None:
    database_url = os.environ.get("NEON_DATABASE_URL")
    if not database_url:
        raise SystemExit("NEON_DATABASE_URL is not configured")

    files = migration_files()
    if not files:
        raise SystemExit("no database migrations found")

    with psycopg.connect(database_url, connect_timeout=15) as connection:
        applied = applied_versions(connection)
        for migration_file in files:
            version = migration_version(migration_file)
            if version in applied:
                print(f"Skipped migration: {migration_file.name} (already applied)")
                continue

            sql = migration_file.read_text(encoding="utf-8")
            connection.execute(sql)

            # Migrations normally register themselves. This fallback keeps the
            # runner portable if a future migration omits the bookkeeping row.
            exists = connection.execute(
                "select to_regclass('public.schema_migrations') is not null"
            ).fetchone()[0]
            if not exists:
                raise RuntimeError(
                    f"{migration_file.name} did not create schema_migrations"
                )
            connection.execute(
                "insert into schema_migrations(version) values (%s) "
                "on conflict (version) do nothing",
                (version,),
            )
            connection.commit()
            applied.add(version)
            print(f"Applied migration: {migration_file.name}")


if __name__ == "__main__":
    main()
