"""Rebuild the research schema in an isolated temporary schema, then remove it."""
from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

import psycopg
from psycopg import sql

MIGRATION_DIR = Path(__file__).resolve().parents[1] / "db" / "migrations"
EXPECTED_TABLES = {
    "schema_migrations",
    "datasets",
    "engine_references",
    "experiments",
    "walk_forward_results",
    "trades",
    "source_artifacts",
    "detail_import_registry",
    "detail_evidence_rows",
    "mt5_shadow_heartbeats",
    "mt5_shadow_bars",
    "mt5_shadow_decisions",
}
EXPECTED_VERSIONS = {
    "0001_research_core",
    "0002_reference_provenance",
    "0003_active_reference_registry",
    "0004_detail_evidence_registry",
    "0005_reproduced_detail_sources",
    "0006_detail_evidence_rows",
    "0007_mt5_shadow_telemetry",
}
EXPECTED_DETAIL_SOURCES = {
    "WF_METRICS": "v112_reproduced_wf_metrics_20260908",
    "SELECTED_VARIANTS": "v112_reproduced_selected_variants_20260908",
    "TRADES": "v112_reproduced_trades_normal_20260908",
}


def main() -> None:
    database_url = os.environ.get("NEON_DATABASE_URL")
    if not database_url:
        raise SystemExit("NEON_DATABASE_URL is not configured")

    schema = f"daxlab_restore_{uuid4().hex[:12]}"
    files = sorted(MIGRATION_DIR.glob("*.sql"))
    if {p.stem for p in files} != EXPECTED_VERSIONS:
        raise SystemExit("database restore drill: migration set drift")

    with psycopg.connect(database_url, connect_timeout=15, autocommit=True) as conn:
        try:
            conn.execute(sql.SQL("create schema {}").format(sql.Identifier(schema)))
            conn.execute(sql.SQL("set search_path to {}, public").format(sql.Identifier(schema)))
            for migration in files:
                conn.execute(migration.read_text(encoding="utf-8"))

            rows = conn.execute(
                "select table_name from information_schema.tables where table_schema = %s",
                (schema,),
            ).fetchall()
            tables = {str(row[0]) for row in rows}
            missing = EXPECTED_TABLES - tables
            if missing:
                raise RuntimeError(f"restore drill missing tables: {sorted(missing)}")

            versions = {str(row[0]) for row in conn.execute("select version from schema_migrations").fetchall()}
            if versions != EXPECTED_VERSIONS:
                raise RuntimeError(f"restore drill migration registry mismatch: {sorted(versions)}")

            ref = conn.execute(
                "select status from experiments where experiment_key = 'V112_REFERENCE_V1'"
            ).fetchone()
            if ref != ("ACTIVE_REFERENCE",):
                raise RuntimeError("restore drill active reference not reconstructed")

            details = conn.execute(
                "select detail_kind, state, source_artifact_key, expected_sha256 "
                "from detail_import_registry where experiment_key = 'V112_REFERENCE_V1' "
                "order by detail_kind"
            ).fetchall()
            if len(details) != 3 or any(state != "NOT_IMPORTED" for _, state, _, _ in details):
                raise RuntimeError("restore drill detail evidence state mismatch")
            for kind, _, source_key, expected_sha in details:
                if source_key != EXPECTED_DETAIL_SOURCES[kind] or not expected_sha:
                    raise RuntimeError(f"restore drill detail source mismatch: {kind}")

            verified_sources = conn.execute(
                "select count(*) from source_artifacts where artifact_key = any(%s) "
                "and verification_status = 'VERIFIED' and expected_sha256 = observed_sha256",
                (list(EXPECTED_DETAIL_SOURCES.values()),),
            ).fetchone()[0]
            if verified_sources != 3:
                raise RuntimeError("restore drill reproduced source verification mismatch")

            evidence_rows = conn.execute("select count(*) from detail_evidence_rows").fetchone()[0]
            if evidence_rows != 0:
                raise RuntimeError("restore drill must start with zero imported detail evidence rows")

            telemetry_counts = {
                table: conn.execute(sql.SQL("select count(*) from {}").format(sql.Identifier(table))).fetchone()[0]
                for table in (
                    "mt5_shadow_heartbeats",
                    "mt5_shadow_bars",
                    "mt5_shadow_decisions",
                )
            }
            if any(telemetry_counts.values()):
                raise RuntimeError("restore drill telemetry tables must start empty")

            print(
                "Database restore drill OK | "
                f"schema={schema} | migrations={len(versions)} | tables={len(tables)} | "
                "active_reference=VERIFIED | detail_sources=3 VERIFIED | "
                "detail_rows=0 | telemetry_rows=0 | detail=NOT_IMPORTED"
            )
        finally:
            conn.execute("set search_path to public")
            conn.execute(sql.SQL("drop schema if exists {} cascade").format(sql.Identifier(schema)))


if __name__ == "__main__":
    main()
