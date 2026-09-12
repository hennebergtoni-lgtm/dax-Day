BEGIN;

CREATE OR REPLACE VIEW cand001_operator_current AS
SELECT
    id,
    generated_at,
    schema_version,
    core_version,
    candidate_id,
    config_fingerprint,
    decision_action,
    decision_id,
    last_bar_id,
    last_bar_close_time,
    freshness_seconds,
    health_state,
    virtual_status,
    outcome_id,
    outcome_net_r,
    snapshot_fingerprint,
    execution_capability,
    order_execution_enabled,
    payload_sha256,
    payload,
    created_at
FROM cand001_operator_snapshots
ORDER BY generated_at DESC, id DESC
LIMIT 1;

INSERT INTO schema_migrations(version)
VALUES ('0009_cand001_operator_current_view')
ON CONFLICT (version) DO NOTHING;

COMMIT;
