BEGIN;

CREATE TABLE IF NOT EXISTS schema_migrations (
    version text PRIMARY KEY,
    applied_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS datasets (
    id bigserial PRIMARY KEY,
    name text NOT NULL UNIQUE,
    source_uri text,
    sha256 text NOT NULL,
    start_date date,
    end_date date,
    session_tz text NOT NULL DEFAULT 'Europe/Berlin',
    session_start time,
    session_end time,
    candle_count bigint,
    valid_day_count integer,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS engine_references (
    id bigserial PRIMARY KEY,
    name text NOT NULL UNIQUE,
    version text NOT NULL,
    sha256 text NOT NULL,
    frozen boolean NOT NULL DEFAULT false,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS experiments (
    id bigserial PRIMARY KEY,
    experiment_key text NOT NULL UNIQUE,
    title text NOT NULL,
    status text NOT NULL,
    hypothesis text,
    engine_reference_id bigint REFERENCES engine_references(id),
    dataset_id bigint REFERENCES datasets(id),
    git_commit_sha text,
    config jsonb NOT NULL DEFAULT '{}'::jsonb,
    notes text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS walk_forward_results (
    id bigserial PRIMARY KEY,
    experiment_id bigint NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    wf_id integer NOT NULL,
    train_start date,
    train_end date,
    oos_start date,
    oos_end date,
    cost_model text NOT NULL,
    variant_key text NOT NULL,
    trades integer NOT NULL,
    return_r double precision NOT NULL,
    pf double precision,
    avg_r double precision,
    max_dd_r double precision,
    winrate double precision,
    metrics jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (experiment_id, wf_id, cost_model, variant_key)
);

CREATE TABLE IF NOT EXISTS trades (
    id bigserial PRIMARY KEY,
    experiment_id bigint NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    wf_id integer,
    trade_date date NOT NULL,
    entry_time timestamptz,
    exit_time timestamptz,
    side text,
    entry double precision,
    exit double precision,
    r double precision NOT NULL,
    mfe_r double precision,
    mae_r double precision,
    reason text,
    parameters jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_wf_experiment ON walk_forward_results(experiment_id);
CREATE INDEX IF NOT EXISTS idx_trades_experiment ON trades(experiment_id);
CREATE INDEX IF NOT EXISTS idx_trades_date ON trades(trade_date);

INSERT INTO schema_migrations(version)
VALUES ('0001_research_core')
ON CONFLICT (version) DO NOTHING;

COMMIT;
