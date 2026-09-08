# V6 Common Research Result Schema

Status: BINDING RESEARCH CONTRACT

Every material research-family result must expose the same minimum evidence surface so isolated tools and later interactions remain comparable.

## Identity
- family_id
- hypothesis_id
- definition_version
- provenance_class
- dataset_fingerprint
- engine_fingerprint
- config_fingerprint
- code_commit_sha
- run_id
- parent_run_id when resumed or derived

## Causality
- causal_contract_version
- causality_state
- lookahead_failures
- feature_state_time_rule

## Sample / WF coverage
- train_days
- oos_days
- step_days
- wf_windows_total
- wf_windows_active
- trade_count
- no_trade_count when applicable
- active_days
- first_oos_date
- last_oos_date

## Performance per cost model
The following must be reported for each of `normal`, `stress_1_5x`, `stress_2x`:
- trade_count
- return_r
- avg_r
- profit_factor
- max_drawdown_r
- win_rate when meaningful
- positive_wf
- negative_wf
- median_wf_pf

## Stability
- broad-era breakdown
- minimum-trade warning
- concentration warning
- neighbourhood robustness where parameters exist
- parameter-edge sensitivity
- regime dependence notes

## Selection / evidence integrity
- hypothesis_predeclared
- train_only_parameters
- diagnostic_derived_parameters
- oos_reused_for_tuning
- untouched_holdout_used
- prospective_evidence_state

## Negative findings
Every run records:
- rejected_conditions
- neutral_conditions
- instability_reasons
- known_retest_blockers

## Interaction metadata
- isolated_evidence_state for each component
- interaction_predeclared
- interaction_parameter_count
- incremental_trade_count
- incremental_return_r
- incremental_pf
- no_trade_delta

## Status
Allowed terminal interpretations for a result artifact are:
- `DESCRIPTIVE_ONLY`
- `RESEARCH_SIGNAL`
- `RETAIN`
- `REJECT`
- `NEEDS_FRESH_VALIDATION`
- `PROSPECTIVE_CANDIDATE`

None of these statuses automatically changes V11.2 or grants Paper/Live readiness.
