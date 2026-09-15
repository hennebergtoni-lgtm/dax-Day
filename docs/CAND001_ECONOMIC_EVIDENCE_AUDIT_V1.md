# CAND-001 Economic Evidence Audit V1

Status: BINDING EVIDENCE AUDIT — ECONOMIC PERFORMANCE UNVERIFIED
Updated: 2026-09-11
Product: `DAX-BOT/1.0-alpha/CAND-001`

## Decision

CAND-001 currently has strong repository evidence for software correctness, causality, determinism, restart/duplicate safety, SHADOW lifecycle semantics, costed virtual outcome calculation and performance-report plumbing.

It does **not** currently have reproducible CAND-001-specific historical full-sample, OOS or walk-forward economic evidence in the repository.

Therefore:

- CAND-001 profitability is `UNVERIFIED`;
- CAND-001 robustness is `UNVERIFIED`;
- CAND-001 historical PF / net-R / drawdown / win-rate are `UNVERIFIED`;
- no REF-V11.2 or V12 research metric may be relabeled, inherited or cited as CAND-001 performance;
- technical pipeline throughput/latency is not economic performance.

This is an evidence-boundary finding, not a negative profitability result.

## Exact-head audit findings

Audit head: `658c0a8493b907acf64da2259553005f4937d125`.

### Scripts

The exact `scripts/` tree contains `scripts/benchmark_cand001_pipeline.py`, which measures technical event-processing performance. It does not run historical economic replay, OOS evaluation or walk-forward evaluation for CAND-001.

No CAND-001-specific historical / OOS / walk-forward runner was present in the exact `scripts/` tree at the audit head.

### Research artifacts

The exact `research/` root contains the frozen `V112_REFERENCE_V1` evidence and V12/family research lines, but no CAND-001 economic-results directory or CAND-001 OOS/WF result artifact.

Those legacy/reference/research-family results are separate evidence domains and may not be borrowed by CAND-001.

### Forward evidence

`docs/evidence/2026-09-11_forward_shadow_real_data_milestone.md` is real broker-feed SHADOW evidence, but it explicitly binds the observed decisions to `V112_REFERENCE_V1`, states `Profitability: NOT PROVEN`, and does not establish CAND-001 economics.

### Candidate reporting code

`candidate_forward_observation.py` can map terminal CAND-001 outcomes into the existing `forward_shadow_performance.py` contract. That proves a reporting path exists.

`tests/test_candidate_forward_observation.py` uses synthetic signal/bar fixtures and proves mapping, R aggregation and cash-ledger plumbing. Synthetic regression fixtures are not historical market performance evidence.

### Alpha closeout

`docs/DAX_BOT_1_0_CLOSEOUT_FINAL.md` explicitly closes controllability/determinism/observability/restart safety and states that the milestone is not a profitability claim.

## Minimum next measurement harness

The next safe research unit is a deterministic **CAND-001 historical descriptive replay**. It must measure the existing candidate, not optimize it.

Required inputs and invariants:

1. Use the audited historical DAX M5 session dataset identity already preserved by the project.
2. Reuse the exact CAND-001 runtime semantics/config identity; do not create a second strategy interpretation in a DataFrame-only backtester.
3. Process bars chronologically and causally; only CLOSED bars may mutate state.
4. Reuse Candidate admission, virtual lifecycle, same-bar/gap semantics and costed virtual outcome owners.
5. Bind every run to dataset, product/candidate/config, core/ruleset and cost-model fingerprints.
6. Emit deterministic machine-readable per-trade records plus one summary artifact.
7. Preserve `execution_capability=NONE` / `order_execution_enabled=false`.
8. Do not tune thresholds, filters, RR or entry/exit semantics during the descriptive run.

Minimum descriptive outputs:

- processed sessions/bars;
- directional signals;
- admitted trades;
- blocked signals and reasons;
- completed trades;
- long/short counts;
- wins/losses/flats;
- gross R;
- modeled cost R;
- net R;
- average and median net R;
- profit factor from positive/negative net-R legs;
- maximum drawdown in R;
- win rate;
- session/day distribution;
- deterministic run/report/trade fingerprints.

## Evidence classification

A full 2014–2019 descriptive replay is **DESCRIPTIVE / IN-SAMPLE MEASUREMENT** for CAND-001 because the product definition already exists before this measurement, but the same historical period has been extensively used during broader project research. It must not be called an independent edge proof.

It may answer: “What does frozen CAND-001 do on the audited historical surface under its current semantics?”

It may not answer: “Is CAND-001 robustly profitable out of sample?”

## Later gates

After the descriptive harness itself is parity-/determinism-tested:

1. define a separately versioned CAND-001 OOS / walk-forward evaluation contract;
2. keep selection/tuning frozen during OOS measurement;
3. apply cost stress and robustness diagnostics;
4. only then discuss economic promotion evidence.

No full-sample result, however attractive, may bypass OOS/WF and prospective SHADOW/PAPER evidence.

## Reuse rule

Do not borrow REF-V11.2 metrics to fill missing CAND-001 fields. Missing CAND-001 economics must remain explicitly `UNVERIFIED` until measured by a CAND-001-bound run.
