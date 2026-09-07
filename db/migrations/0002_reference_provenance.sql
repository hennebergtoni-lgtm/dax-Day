BEGIN;

CREATE TABLE IF NOT EXISTS source_artifacts (
    id bigserial PRIMARY KEY,
    artifact_key text NOT NULL UNIQUE,
    filename text NOT NULL,
    artifact_kind text NOT NULL,
    provider text NOT NULL,
    expected_sha256 text,
    observed_sha256 text,
    verification_status text NOT NULL DEFAULT 'PENDING',
    legacy_relative_path text,
    private_locator_present boolean NOT NULL DEFAULT false,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    verified_at timestamptz,
    CHECK (verification_status IN ('PENDING', 'VERIFIED', 'FAILED', 'MISSING'))
);

INSERT INTO source_artifacts (
    artifact_key,
    filename,
    artifact_kind,
    provider,
    expected_sha256,
    legacy_relative_path,
    metadata
)
VALUES
    (
        'v11_2_exact_engine',
        'NEXT_ENGINE_V3_5_4_FIX2_EXACT_ENGINE_PARITY_GATE.ipynb',
        'engine_notebook',
        'legacy_drive',
        '9561b9089c57c543798dc587ce240a729b7995230dd5d665a1bdd029f3990887',
        NULL,
        '{"gate":"Gate 1","frozen_reference":true}'::jsonb
    ),
    (
        'v2_8_18_fast_runner',
        'DAX_V11_2_V2_8_18_FAST_FULL_RESEARCH_ONE_CLICK.ipynb',
        'runner_notebook',
        'legacy_drive',
        NULL,
        NULL,
        '{"role":"proven FAST research runner","auto_promote":false}'::jsonb
    ),
    (
        'v11_2_full_wf_summary',
        'FULL_WF_SUMMARY.csv',
        'research_result',
        'legacy_drive',
        NULL,
        'V11_2_FULL_WF_SESSION_DAY_V4_FIX1/FULL_WF_SUMMARY.csv',
        '{"expected_rows":81,"reference_only":true}'::jsonb
    )
ON CONFLICT (artifact_key) DO NOTHING;

INSERT INTO engine_references (name, version, sha256, frozen, metadata)
VALUES (
    'V11.2 Exact Reference Engine',
    'V11.2',
    '9561b9089c57c543798dc587ce240a729b7995230dd5d665a1bdd029f3990887',
    true,
    '{"execution_status":"PENDING_ARTIFACT_MIGRATION","variants":144,"walk_forwards":81,"train_days":45,"oos_days":20,"step_days":20}'::jsonb
)
ON CONFLICT (name) DO NOTHING;

INSERT INTO schema_migrations(version)
VALUES ('0002_reference_provenance')
ON CONFLICT (version) DO NOTHING;

COMMIT;
