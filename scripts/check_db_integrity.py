"""Read-only database integrity gate for the research store."""
from __future__ import annotations

import os

import psycopg

EXPECTED_MIGRATIONS = {
    "0001_research_core",
    "0002_reference_provenance",
    "0003_active_reference_registry",
    "0004_detail_evidence_registry",
    "0005_reproduced_detail_sources",
    "0006_detail_evidence_rows",
    "0007_mt5_shadow_telemetry",
}
EXPECTED_TELEMETRY_TABLES = {
    "mt5_shadow_heartbeats",
    "mt5_shadow_bars",
    "mt5_shadow_decisions",
}
EXPECTED_ENGINE_SHA = "9561b9089c57c543798dc587ce240a729b7995230dd5d665a1bdd029f3990887"
EXPECTED_DATASET_SHA = "e51bba6cb2befe5e7eb0376318e43b096a3e2ecaae3f556019862975c60286a2"
EXPECTED_CANDIDATE_ENGINE_SHA = (
    "b3d62e0cad72420d36ade523857d024d4a334298be51a8313069e36614bda888"
)
EXPECTED_DETAIL_HASHES = {
    "WF_METRICS": "4f61f57c21f469685488c52481f779b87b17b599fbcda0da942b5a2ed713709a",
    "SELECTED_VARIANTS": "8b604de454b615a3d789577be3295765e04eab06448cbcd0844a995af9b0a41e",
    "TRADES": "f60bb5fc15b5e620a37ca44bdb5bdcea20381261c06d40cb78aba34387f56023",
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

    with psycopg.connect(database_url, connect_timeout=15) as connection, connection.cursor() as cursor:
        cursor.execute("select version from schema_migrations")
        migrations = {row[0] for row in cursor.fetchall()}
        missing = EXPECTED_MIGRATIONS - migrations
        if missing:
            raise SystemExit(f"database integrity failed: missing migrations {sorted(missing)}")

        cursor.execute(
            "select table_name from information_schema.tables where table_schema = current_schema()"
        )
        tables = {row[0] for row in cursor.fetchall()}
        missing_telemetry = EXPECTED_TELEMETRY_TABLES - tables
        if missing_telemetry:
            raise SystemExit(
                f"database integrity failed: missing telemetry tables {sorted(missing_telemetry)}"
            )

        cursor.execute("select sha256, frozen from engine_references where name = %s", ("V11.2 Exact Reference Engine",))
        if cursor.fetchone() != (EXPECTED_ENGINE_SHA, True):
            raise SystemExit("database integrity failed: V11.2 engine reference drift")

        cursor.execute("select sha256, candle_count, valid_day_count from datasets where name = %s", ("dax_m5_2014_2019_audited_v1",))
        if cursor.fetchone() != (EXPECTED_DATASET_SHA, 172319, 1673):
            raise SystemExit("database integrity failed: active dataset reference drift")

        cursor.execute("select status, git_commit_sha, config from experiments where experiment_key = %s", ("V112_REFERENCE_V1",))
        experiment = cursor.fetchone()
        if experiment is None:
            raise SystemExit("database integrity failed: active V11.2 experiment missing")
        status, git_sha, config = experiment
        normal = config.get("normal", {}) if isinstance(config, dict) else {}
        if status != "ACTIVE_REFERENCE" or git_sha != "a5661ffbd66c01a99c502daaaa1057555633cd76":
            raise SystemExit("database integrity failed: active V11.2 registry drift")
        if normal.get("oos_trades") != 856 or normal.get("positive_wfs") != 37:
            raise SystemExit("database integrity failed: active V11.2 aggregate drift")

        cursor.execute(
            "select detail_kind, evidence_class, state, expected_rows, expected_sha256, "
            "dataset_sha256, engine_sha256, source_artifact_key, metadata "
            "from detail_import_registry where experiment_key = %s order by detail_kind",
            ("V112_REFERENCE_V1",),
        )
        detail_rows = cursor.fetchall()
        if len(detail_rows) != 3:
            raise SystemExit("database integrity failed: V11.2 detail registry incomplete")
        expected_counts = {"WF_METRICS": 243, "SELECTED_VARIANTS": 81, "TRADES": 856}
        for kind, evidence_class, detail_state, expected_rows, expected_hash, data_sha, engine_sha, source_key, metadata in detail_rows:
            if evidence_class != "CLEAN_REFERENCE" or detail_state != "NOT_IMPORTED":
                raise SystemExit("database integrity failed: V11.2 detail evidence state drift")
            if expected_rows != expected_counts[kind] or expected_hash != EXPECTED_DETAIL_HASHES[kind]:
                raise SystemExit(f"database integrity failed: {kind} evidence contract drift")
            if data_sha != EXPECTED_DATASET_SHA or engine_sha != EXPECTED_CANDIDATE_ENGINE_SHA:
                raise SystemExit("database integrity failed: V11.2 detail provenance drift")
            if source_key != EXPECTED_DETAIL_SOURCES[kind]:
                raise SystemExit(f"database integrity failed: {kind} source-artifact drift")
            if kind == "TRADES":
                if not isinstance(metadata, dict) or metadata.get("identity_semantics") != "NEWLY_REPRODUCED_NO_HISTORICAL_FROZEN_HASH":
                    raise SystemExit("database integrity failed: trade hash semantics drift")
                if metadata.get("historical_file_identity") is not False:
                    raise SystemExit("database integrity failed: reproduced trade hash mislabeled historical")

        cursor.execute(
            "select artifact_key, verification_status, expected_sha256, observed_sha256, metadata "
            "from source_artifacts where artifact_key = any(%s)",
            (list(EXPECTED_DETAIL_SOURCES.values()),),
        )
        sources = {row[0]: row[1:] for row in cursor.fetchall()}
        if set(sources) != set(EXPECTED_DETAIL_SOURCES.values()):
            raise SystemExit("database integrity failed: reproduced detail source registry incomplete")
        for key, (verification, expected_sha, observed_sha, metadata) in sources.items():
            if verification != "VERIFIED" or expected_sha != observed_sha:
                raise SystemExit(f"database integrity failed: unverified detail source {key}")
            if key == EXPECTED_DETAIL_SOURCES["TRADES"] and metadata.get("historical_file_identity") is not False:
                raise SystemExit("database integrity failed: trade source historical identity drift")

        cursor.execute("select count(*) from detail_evidence_rows")
        evidence_rows = cursor.fetchone()[0]
        if evidence_rows != 0:
            raise SystemExit("database integrity failed: detail evidence rows imported without authorization")
        cursor.execute("select count(*) from walk_forward_results")
        wf_rows = cursor.fetchone()[0]
        cursor.execute("select count(*) from trades")
        trade_rows = cursor.fetchone()[0]

        telemetry_counts = {}
        for table in sorted(EXPECTED_TELEMETRY_TABLES):
            cursor.execute(f"select count(*) from {table}")
            telemetry_counts[table] = cursor.fetchone()[0]

    print(
        "Database integrity OK | "
        f"migrations={len(migrations)} | active_reference=VERIFIED | detail_sources=VERIFIED | "
        f"detail_registry=NOT_IMPORTED | evidence_rows={evidence_rows} | "
        f"wf_rows={wf_rows} | trades={trade_rows} | telemetry={telemetry_counts} | "
        "detailed_rows=NOT_IMPORTED"
    )


if __name__ == "__main__":
    main()
