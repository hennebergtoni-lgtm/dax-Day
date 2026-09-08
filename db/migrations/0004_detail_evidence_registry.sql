BEGIN;

CREATE TABLE IF NOT EXISTS detail_import_registry (
    id bigserial PRIMARY KEY,
    experiment_key text NOT NULL REFERENCES experiments(experiment_key) ON DELETE CASCADE,
    detail_kind text NOT NULL,
    evidence_class text NOT NULL,
    state text NOT NULL DEFAULT 'NOT_IMPORTED',
    expected_rows integer NOT NULL CHECK (expected_rows >= 0),
    observed_rows integer,
    expected_sha256 text,
    observed_sha256 text,
    dataset_sha256 text NOT NULL,
    engine_sha256 text NOT NULL,
    schema_version text NOT NULL,
    source_artifact_key text REFERENCES source_artifacts(artifact_key),
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    verified_at timestamptz,
    UNIQUE (experiment_key, detail_kind),
    CHECK (detail_kind IN ('WF_METRICS', 'SELECTED_VARIANTS', 'TRADES')),
    CHECK (evidence_class IN ('CLEAN_REFERENCE', 'LEGACY', 'RESEARCH')),
    CHECK (state IN ('NOT_IMPORTED', 'PARTIAL', 'VERIFIED')),
    CHECK (observed_rows IS NULL OR observed_rows >= 0),
    CHECK (
        state <> 'VERIFIED'
        OR (
            evidence_class = 'CLEAN_REFERENCE'
            AND observed_rows = expected_rows
            AND expected_sha256 IS NOT NULL
            AND observed_sha256 = expected_sha256
            AND source_artifact_key IS NOT NULL
            AND verified_at IS NOT NULL
        )
    )
);

INSERT INTO detail_import_registry (
    experiment_key,
    detail_kind,
    evidence_class,
    state,
    expected_rows,
    expected_sha256,
    dataset_sha256,
    engine_sha256,
    schema_version,
    metadata
)
VALUES
    (
        'V112_REFERENCE_V1',
        'WF_METRICS',
        'CLEAN_REFERENCE',
        'NOT_IMPORTED',
        243,
        '4f61f57c21f469685488c52481f779b87b17b599fbcda0da942b5a2ed713709a',
        'e51bba6cb2befe5e7eb0376318e43b096a3e2ecaae3f556019862975c60286a2',
        'b3d62e0cad72420d36ade523857d024d4a334298be51a8313069e36614bda888',
        'V1',
        '{"role":"clean_reference_detail","synthetic_rows_forbidden":true}'::jsonb
    ),
    (
        'V112_REFERENCE_V1',
        'SELECTED_VARIANTS',
        'CLEAN_REFERENCE',
        'NOT_IMPORTED',
        81,
        '8b604de454b615a3d789577be3295765e04eab06448cbcd0844a995af9b0a41e',
        'e51bba6cb2befe5e7eb0376318e43b096a3e2ecaae3f556019862975c60286a2',
        'b3d62e0cad72420d36ade523857d024d4a334298be51a8313069e36614bda888',
        'V1',
        '{"role":"clean_reference_detail","synthetic_rows_forbidden":true}'::jsonb
    ),
    (
        'V112_REFERENCE_V1',
        'TRADES',
        'CLEAN_REFERENCE',
        'NOT_IMPORTED',
        856,
        NULL,
        'e51bba6cb2befe5e7eb0376318e43b096a3e2ecaae3f556019862975c60286a2',
        'b3d62e0cad72420d36ade523857d024d4a334298be51a8313069e36614bda888',
        'V1',
        '{"role":"clean_reference_detail","source_trade_hash_not_recovered":true,"verification_blocked_until_expected_hash_known":true}'::jsonb
    )
ON CONFLICT (experiment_key, detail_kind) DO NOTHING;

INSERT INTO schema_migrations(version)
VALUES ('0004_detail_evidence_registry')
ON CONFLICT (version) DO NOTHING;

COMMIT;
