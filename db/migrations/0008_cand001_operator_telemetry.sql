BEGIN;

CREATE TABLE IF NOT EXISTS cand001_operator_snapshots (
    id bigserial PRIMARY KEY,
    generated_at timestamptz NOT NULL,
    schema_version text NOT NULL,
    core_version text NOT NULL,
    candidate_id text NOT NULL,
    config_fingerprint text NOT NULL,
    decision_action text NOT NULL,
    decision_id text NOT NULL,
    last_bar_id text,
    last_bar_close_time timestamptz,
    freshness_seconds double precision,
    health_state text,
    virtual_status text,
    outcome_id text,
    outcome_net_r double precision,
    snapshot_fingerprint text NOT NULL,
    execution_capability text NOT NULL,
    order_execution_enabled boolean NOT NULL,
    payload_sha256 text NOT NULL,
    payload jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK (schema_version = 'DAX_BOT_OPERATOR_SNAPSHOT_V3'),
    CHECK (length(config_fingerprint) = 64),
    CHECK (length(decision_id) = 64),
    CHECK (last_bar_id IS NULL OR length(last_bar_id) = 64),
    CHECK (outcome_id IS NULL OR length(outcome_id) = 64),
    CHECK (length(snapshot_fingerprint) = 64),
    CHECK (length(payload_sha256) = 64),
    CHECK (freshness_seconds IS NULL OR freshness_seconds >= 0),
    CHECK (execution_capability = 'NONE'),
    CHECK (order_execution_enabled = false),
    UNIQUE (snapshot_fingerprint)
);

CREATE INDEX IF NOT EXISTS idx_cand001_operator_snapshots_generated_at
ON cand001_operator_snapshots(generated_at DESC);

CREATE INDEX IF NOT EXISTS idx_cand001_operator_snapshots_candidate_time
ON cand001_operator_snapshots(candidate_id, generated_at DESC);

INSERT INTO schema_migrations(version)
VALUES ('0008_cand001_operator_telemetry')
ON CONFLICT (version) DO NOTHING;

COMMIT;
