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

INSERT INTO source_artifacts (
    artifact_key,
    filename,
    artifact_kind,
    provider,
    expected_sha256,
    observed_sha256,
    verification_status,
    private_locator_present,
    metadata,
    verified_at
)
VALUES
    (
        'v112_clean_wf_metrics_20260908',
        'wf_metrics.csv',
        'clean_reference_detail',
        'clean_reference_reproduction',
        '4f61f57c21f469685488c52481f779b87b17b599fbcda0da942b5a2ed713709a',
        '4f61f57c21f469685488c52481f779b87b17b599fbcda0da942b5a2ed713709a',
        'VERIFIED',
        true,
        '{"identity":"HISTORICAL_HASH_MATCH","rows":243,"evidence_bundle":"V112_CLEAN_REFERENCE_EVIDENCE_2026_09_08.zip"}'::jsonb,
        now()
    ),
    (
        'v112_clean_selected_variants_20260908',
        'selected_variants.csv',
        'clean_reference_detail',
        'clean_reference_reproduction',
        '8b604de454b615a3d789577be3295765e04eab06448cbcd0844a995af9b0a41e',
        '8b604de454b615a3d789577be3295765e04eab06448cbcd0844a995af9b0a41e',
        'VERIFIED',
        true,
        '{"identity":"HISTORICAL_HASH_MATCH","rows":81,"evidence_bundle":"V112_CLEAN_REFERENCE_EVIDENCE_2026_09_08.zip"}'::jsonb,
        now()
    ),
    (
        'v112_reproduced_trades_20260908',
        'trades_normal.csv',
        'clean_reference_detail',
        'clean_reference_reproduction',
        NULL,
        'f60bb5fc15b5e620a37ca44bdb5bdcea20381261c06d40cb78aba34387f56023',
        'VERIFIED',
        true,
        '{"identity":"NEW_REPRODUCIBLE_CLEAN_EVIDENCE_NOT_HISTORICAL_FILE_IDENTITY","rows":856,"historical_expected_hash":null,"evidence_bundle":"V112_CLEAN_REFERENCE_EVIDENCE_2026_09_08.zip"}'::jsonb,
        now()
    )
ON CONFLICT (artifact_key) DO NOTHING;

UPDATE detail_import_registry
SET source_artifact_key = CASE detail_kind
        WHEN 'WF_METRICS' THEN 'v112_clean_wf_metrics_20260908'
        WHEN 'SELECTED_VARIANTS' THEN 'v112_clean_selected_variants_20260908'
        WHEN 'TRADES' THEN 'v112_reproduced_trades_20260908'
    END,
    updated_at = now()
WHERE experiment_key = 'V112_REFERENCE_V1'
  AND detail_kind IN ('WF_METRICS', 'SELECTED_VARIANTS', 'TRADES')
  AND source_artifact_key IS NULL;

INSERT INTO schema_migrations(version)
VALUES ('0005_detail_evidence_rows')
ON CONFLICT (version) DO NOTHING;

COMMIT;
