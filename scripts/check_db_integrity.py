"""Read-only database integrity gate for the research store."""
from __future__ import annotations

import os

import psycopg

EXPECTED_MIGRATIONS = {
    "0001_research_core",
    "0002_reference_provenance",
    "0003_active_reference_registry",
    "0004_detail_evidence_registry",
}
EXPECTED_ENGINE_SHA = "9561b9089c57c543798dc587ce240a729b7995230dd5d665a1bdd029f3990887"
EXPECTED_DATASET_SHA = "e51bba6cb2befe5e7eb0376318e43b096a3e2ecaae3f556019862975c60286a2"
EXPECTED_CANDIDATE_ENGINE_SHA = (
    "b3d62e0cad72420d36ade523857d024d4a334298be51a8313069e36614bda888"
)


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
            "select sha256, frozen from engine_references where name = %s",
            ("V11.2 Exact Reference Engine",),
        )
        engine = cursor.fetchone()
        if engine != (EXPECTED_ENGINE_SHA, True):
            raise SystemExit("database integrity failed: V11.2 engine reference drift")

        cursor.execute(
            "select sha256, candle_count, valid_day_count from datasets where name = %s",
            ("dax_m5_2014_2019_audited_v1",),
        )
        dataset = cursor.fetchone()
        if dataset != (EXPECTED_DATASET_SHA, 172319, 1673):
            raise SystemExit("database integrity failed: active dataset reference drift")

        cursor.execute(
            "select status, git_commit_sha, config from experiments where experiment_key = %s",
            ("V112_REFERENCE_V1",),
        )
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
            "dataset_sha256, engine_sha256 from detail_import_registry "
            "where experiment_key = %s order by detail_kind",
            ("V112_REFERENCE_V1",),
        )
        detail_rows = cursor.fetchall()
        if len(detail_rows) != 3:
            raise SystemExit("database integrity failed: V11.2 detail registry incomplete")

        expected_counts = {"WF_METRICS": 243, "SELECTED_VARIANTS": 81, "TRADES": 856}
        for kind, evidence_class, detail_state, expected_rows, expected_hash, data_sha, engine_sha in detail_rows:
            if evidence_class != "CLEAN_REFERENCE" or detail_state != "NOT_IMPORTED":
                raise SystemExit("database integrity failed: V11.2 detail evidence state drift")
            if expected_rows != expected_counts[kind]:
                raise SystemExit("database integrity failed: V11.2 detail expected-row drift")
            if data_sha != EXPECTED_DATASET_SHA or engine_sha != EXPECTED_CANDIDATE_ENGINE_SHA:
                raise SystemExit("database integrity failed: V11.2 detail provenance drift")
            if kind == "TRADES" and expected_hash is not None:
                raise SystemExit("database integrity failed: unrecovered trade hash was fabricated")

        cursor.execute("select count(*) from walk_forward_results")
        wf_rows = cursor.fetchone()[0]
        cursor.execute("select count(*) from trades")
        trade_rows = cursor.fetchone()[0]

    print(
        "Database integrity OK | "
        f"migrations={len(migrations)} | active_reference=VERIFIED | "
        f"detail_registry=NOT_IMPORTED | wf_rows={wf_rows} | trades={trade_rows} | "
        f"detailed_rows={'PRESENT' if wf_rows else 'NOT_IMPORTED'}"
    )


if __name__ == "__main__":
    main()
