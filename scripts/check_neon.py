"""Fail-fast connectivity check for the configured research PostgreSQL store."""

from __future__ import annotations

import os

import psycopg


def main() -> None:
    database_url = os.environ.get("NEON_DATABASE_URL")
    if not database_url:
        raise SystemExit("NEON_DATABASE_URL is not configured")

    with psycopg.connect(database_url, connect_timeout=15) as connection:
        with connection.cursor() as cursor:
            cursor.execute("select current_database(), current_user")
            database, user = cursor.fetchone()

    print(f"PostgreSQL connection OK | database={database} | role={user}")


if __name__ == "__main__":
    main()
