BEGIN;

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
        'v112_reproduced_wf_metrics_20260908',
        'wf_metrics.csv',
        'clean_reference_detail',
        'reproduced_clean_evidence',
        '4f61f57c21f469685488c52481f779b87b17b599fbcda0da942b5a2ed713709a',
        '4f61f57c21f469685488c52481f779b87b17b599fbcda0da942b5a2ed713709a',
        'VERIFIED',
        true,
        '{"experiment_key":"V112_REFERENCE_V1","rows":243,"identity_semantics":"FROZEN_HASH_REPRODUCED_EXACT","bundle_file_id":"1-9B98eX6FBKXJ5WyvY8cpwIuof1v4Lcq"}'::jsonb,
        now()
    ),
    (
        'v112_reproduced_selected_variants_20260908',
        'selected_variants.csv',
        'clean_reference_detail',
        'reproduced_clean_evidence',
        '8b604de454b615a3d789577be3295765e04eab06448cbcd0844a995af9b0a41e',
        '8b604de454b615a3d789577be3295765e04eab06448cbcd0844a995af9b0a41e',
        'VERIFIED',
        true,
        '{"experiment_key":"V112_REFERENCE_V1","rows":81,"identity_semantics":"FROZEN_HASH_REPRODUCED_EXACT","bundle_file_id":"1-9B98eX6FBKXJ5WyvY8cpwIuof1v4Lcq"}'::jsonb,
        now()
    ),
    (
        'v112_reproduced_trades_normal_20260908',
        'trades_normal.csv',
        'clean_reference_detail',
        'reproduced_clean_evidence',
        'f60bb5fc15b5e620a37ca44bdb5bdcea20381261c06d40cb78aba34387f56023',
        'f60bb5fc15b5e620a37ca44bdb5bdcea20381261c06d40cb78aba34387f56023',
        'VERIFIED',
        true,
        '{"experiment_key":"V112_REFERENCE_V1","rows":856,"identity_semantics":"NEWLY_REPRODUCED_NO_HISTORICAL_FROZEN_HASH","historical_file_identity":false,"bundle_file_id":"1-9B98eX6FBKXJ5WyvY8cpwIuof1v4Lcq"}'::jsonb,
        now()
    )
ON CONFLICT (artifact_key) DO NOTHING;

UPDATE detail_import_registry
SET source_artifact_key = 'v112_reproduced_wf_metrics_20260908',
    updated_at = now(),
    metadata = metadata || '{"source_registered":true,"identity_semantics":"FROZEN_HASH_REPRODUCED_EXACT"}'::jsonb
WHERE experiment_key = 'V112_REFERENCE_V1' AND detail_kind = 'WF_METRICS';

UPDATE detail_import_registry
SET source_artifact_key = 'v112_reproduced_selected_variants_20260908',
    updated_at = now(),
    metadata = metadata || '{"source_registered":true,"identity_semantics":"FROZEN_HASH_REPRODUCED_EXACT"}'::jsonb
WHERE experiment_key = 'V112_REFERENCE_V1' AND detail_kind = 'SELECTED_VARIANTS';

UPDATE detail_import_registry
SET expected_sha256 = 'f60bb5fc15b5e620a37ca44bdb5bdcea20381261c06d40cb78aba34387f56023',
    source_artifact_key = 'v112_reproduced_trades_normal_20260908',
    updated_at = now(),
    metadata = (metadata - 'verification_blocked_until_expected_hash_known') ||
        '{"source_registered":true,"identity_semantics":"NEWLY_REPRODUCED_NO_HISTORICAL_FROZEN_HASH","historical_file_identity":false}'::jsonb
WHERE experiment_key = 'V112_REFERENCE_V1' AND detail_kind = 'TRADES';

INSERT INTO schema_migrations(version)
VALUES ('0005_reproduced_detail_sources')
ON CONFLICT (version) DO NOTHING;

COMMIT;
