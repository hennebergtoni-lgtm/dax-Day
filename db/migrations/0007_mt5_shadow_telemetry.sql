BEGIN;

CREATE TABLE IF NOT EXISTS mt5_shadow_heartbeats (
    id bigserial PRIMARY KEY,
    observed_at_utc timestamptz NOT NULL,
    schema_version text NOT NULL,
    status text NOT NULL,
    symbol text,
    bundle_sha256 text,
    closed_m5_bars integer NOT NULL,
    latest_closed_bar_age_seconds double precision,
    single_instance_lock_held boolean NOT NULL,
    processed_total bigint,
    new_decisions integer NOT NULL,
    duplicates_suppressed integer NOT NULL,
    evidence_state text,
    cross_cycle_status text NOT NULL,
    cross_cycle_overlapping_bars integer NOT NULL,
    cross_cycle_identical_overlaps integer NOT NULL,
    cross_cycle_mutated_overlaps integer NOT NULL,
    blockers jsonb NOT NULL DEFAULT '[]'::jsonb,
    history_archive_status text,
    execution_capability text NOT NULL,
    order_execution_enabled boolean NOT NULL,
    payload_sha256 text NOT NULL,
    payload jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK (status IN ('GREEN', 'BLOCKED', 'ERROR', 'STOPPED')),
    CHECK (execution_capability = 'NONE'),
    CHECK (order_execution_enabled = false),
    CHECK (closed_m5_bars >= 0),
    CHECK (new_decisions >= 0),
    CHECK (duplicates_suppressed >= 0),
    CHECK (cross_cycle_overlapping_bars >= 0),
    CHECK (cross_cycle_identical_overlaps >= 0),
    CHECK (cross_cycle_mutated_overlaps >= 0),
    CHECK (bundle_sha256 IS NULL OR length(bundle_sha256) = 64),
    CHECK (length(payload_sha256) = 64),
    UNIQUE (payload_sha256)
);

CREATE INDEX IF NOT EXISTS idx_mt5_shadow_heartbeats_observed_at
ON mt5_shadow_heartbeats(observed_at_utc DESC);

CREATE TABLE IF NOT EXISTS mt5_shadow_bars (
    id bigserial PRIMARY KEY,
    symbol text NOT NULL,
    open_time timestamptz NOT NULL,
    open double precision NOT NULL,
    high double precision NOT NULL,
    low double precision NOT NULL,
    close double precision NOT NULL,
    bar_fingerprint text NOT NULL,
    bundle_sha256 text NOT NULL,
    broker_timezone text,
    timestamp_interpretation text,
    execution_capability text NOT NULL,
    order_execution_enabled boolean NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK (high >= GREATEST(open, close, low)),
    CHECK (low <= LEAST(open, close, high)),
    CHECK (length(bar_fingerprint) = 64),
    CHECK (length(bundle_sha256) = 64),
    CHECK (execution_capability = 'NONE'),
    CHECK (order_execution_enabled = false),
    UNIQUE (symbol, bar_fingerprint)
);

CREATE INDEX IF NOT EXISTS idx_mt5_shadow_bars_symbol_time
ON mt5_shadow_bars(symbol, open_time DESC);

CREATE TABLE IF NOT EXISTS mt5_shadow_decisions (
    id bigserial PRIMARY KEY,
    decision_id text NOT NULL,
    observed_at timestamptz NOT NULL,
    symbol text NOT NULL,
    closed_bar_fingerprint text NOT NULL,
    action text NOT NULL,
    reason_codes jsonb NOT NULL,
    reference_experiment_id text NOT NULL,
    reference_engine_sha256 text NOT NULL,
    execution_capability text NOT NULL,
    order_execution_enabled boolean NOT NULL,
    payload_sha256 text NOT NULL,
    payload jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK (length(decision_id) = 64),
    CHECK (length(closed_bar_fingerprint) = 64),
    CHECK (length(reference_engine_sha256) = 64),
    CHECK (length(payload_sha256) = 64),
    CHECK (action = 'NO_ORDER'),
    CHECK (execution_capability = 'NONE'),
    CHECK (order_execution_enabled = false),
    UNIQUE (decision_id)
);

CREATE INDEX IF NOT EXISTS idx_mt5_shadow_decisions_symbol_time
ON mt5_shadow_decisions(symbol, observed_at DESC);

INSERT INTO schema_migrations(version)
VALUES ('0007_mt5_shadow_telemetry')
ON CONFLICT (version) DO NOTHING;

COMMIT;
