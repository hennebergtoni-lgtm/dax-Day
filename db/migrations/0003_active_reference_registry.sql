BEGIN;

INSERT INTO datasets (
    name, sha256, start_date, end_date, session_tz, session_start, session_end,
    candle_count, valid_day_count, metadata
)
VALUES (
    'dax_m5_2014_2019_audited_v1',
    'e51bba6cb2befe5e7eb0376318e43b096a3e2ecaae3f556019862975c60286a2',
    '2014-01-01', '2019-12-31', 'Europe/Berlin', '09:00', '17:30',
    172319, 1673,
    '{"audited_zip_sha256":"c46c09a391ee83a19a117fb43628cb75ab0a75703701ed7a84731d2963b24870","bars_per_session_day":103,"role":"ACTIVE_REFERENCE_DATASET"}'::jsonb
)
ON CONFLICT (name) DO UPDATE SET
    sha256 = EXCLUDED.sha256,
    candle_count = EXCLUDED.candle_count,
    valid_day_count = EXCLUDED.valid_day_count,
    metadata = EXCLUDED.metadata;

UPDATE engine_references
SET metadata = metadata || '{"execution_status":"ACTIVE_FROZEN_REFERENCE","candidate_source_sha256":"b3d62e0cad72420d36ade523857d024d4a334298be51a8313069e36614bda888","oracle_source_sha256":"62adde1ccd630d01e9500b20c0efa88a0a8bd277e74c1a2c932ec6fc6efd3a0f"}'::jsonb
WHERE name = 'V11.2 Exact Reference Engine';

INSERT INTO experiments (
    experiment_key, title, status, hypothesis, engine_reference_id, dataset_id,
    git_commit_sha, config, notes
)
SELECT
    'V112_REFERENCE_V1',
    'Frozen clean V11.2 active reference',
    'ACTIVE_REFERENCE',
    'Reproducible measurement of frozen V11.2; not a strategy promotion.',
    e.id,
    d.id,
    'a5661ffbd66c01a99c502daaaa1057555633cd76',
    '{"walk_forward":{"train_days":45,"oos_days":20,"step_days":20,"windows":81},"normal":{"oos_trades":856,"oos_return_r":-31.309210619787684,"positive_wfs":37,"negative_wfs":44,"median_wf_pf":0.905769310256018},"stress_1_5x":{"oos_trades":856,"oos_return_r":-40.921695023387514},"stress_2x":{"oos_trades":856,"oos_return_r":-48.424611963007294},"artifacts":{"wf_metrics_rows":243,"selected_variants_rows":81,"wf_metrics_sha256":"4f61f57c21f469685488c52481f779b87b17b599fbcda0da942b5a2ed713709a","selected_variants_sha256":"8b604de454b615a3d789577be3295765e04eab06448cbcd0844a995af9b0a41e"}}'::jsonb,
    'Aggregate active-reference registry only. Per-WF and trade rows are not fabricated; they remain absent until verified artifacts are explicitly imported.'
FROM engine_references e
JOIN datasets d ON d.name = 'dax_m5_2014_2019_audited_v1'
WHERE e.name = 'V11.2 Exact Reference Engine'
ON CONFLICT (experiment_key) DO UPDATE SET
    status = EXCLUDED.status,
    engine_reference_id = EXCLUDED.engine_reference_id,
    dataset_id = EXCLUDED.dataset_id,
    git_commit_sha = EXCLUDED.git_commit_sha,
    config = EXCLUDED.config,
    notes = EXCLUDED.notes,
    updated_at = now();

INSERT INTO schema_migrations(version)
VALUES ('0003_active_reference_registry')
ON CONFLICT (version) DO NOTHING;

COMMIT;
