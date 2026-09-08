BEGIN;

CREATE TABLE IF NOT EXISTS detail_evidence_rows (
    id bigserial PRIMARY KEY,
    experiment_key text NOT NULL REFERENCES experiments(experiment_key) ON DELETE CASCADE,
    detail_kind text NOT NULL,
    source_artifact_key text NOT NULL REFERENCES source_artifacts(artifact_key),
    source_row_id text NOT NULL,
    payload_sha256 text NOT NULL,
    payload jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK (detail_kind IN ('WF_METRICS', 'SELECTED_VARIANTS', 'TRADES')),
    CHECK (length(source_row_id) = 64),
    CHECK (length(payload_sha256) = 64),
    UNIQUE (experiment_key, detail_kind, source_row_id)
);

CREATE INDEX IF NOT EXISTS idx_detail_evidence_rows_experiment_kind
ON detail_evidence_rows(experiment_key, detail_kind);

INSERT INTO schema_migrations(version)
VALUES ('0006_detail_evidence_rows')
ON CONFLICT (version) DO NOTHING;

COMMIT;
