# Step2237 — final IG M5 original-evidence review

Status: **IMPLEMENTED / REAL WINDOWS CLOSEOUT WAITING_EXTERNAL**  
Historical Attempt03 evidence head: `2a99f96e06f7ce1f311c767dec43d236bb63eedd`  
Original export runtime head: `7728453c3c4f8fcd2cf6f8189b0f94562ccfa04f`  
Execution: `NONE / order_execution_enabled=false`; no order was submitted.

## Final classification

**INTERVAL_START — VERIFIED for the operational normalization contract.**

This is a new V2 review. It does not edit or relabel the historical
`DAX_IG_RAW_REVIEW_V1` record, which remains
`OTHER_UNKNOWN / CROSS_BOUNDARY_MUTATIONS_ALONE_DO_NOT_IDENTIFY_INTERVAL_SEMANTICS`
inside the original bundle.

The promotion does not rest on one changed field or on provider documentation:

| Evidence link | First observation | Next-boundary observation | Structural result |
| --- | --- | --- | --- |
| A→B, raw 15:25 | about 15:26, row39/tail, volume57 | about 15:31, row38, volume1003 | same raw identity; open fixed; high/low/close/volume accumulate; row shifts exactly after15:30 |
| B→C, raw 15:30 | about 15:31, row39/tail, volume210 | about 15:36, row38, volume1379 | same coupled pattern reproduced at the next consecutive M5 boundary |

The discriminating fact is the coupled behavior, not mutation alone. On two
consecutive raw timestamps, the row labelled T behaves as an actively accumulating
candle throughout T..T+5 and becomes the previous row when T+5 opens. An
interval-end interpretation would require two consecutive supposedly closed bars
to reopen immediately after T, accumulate most of their volume and range for the
entire following M5 period, and shift only at T+5. That model no longer represents
a close at T; operationally it is the interval-start mapping. Therefore:

- `event_time = snapshotTimeUTC`
- `close_time = snapshotTimeUTC + 5 minutes`
- raw15:25 covers `15:25 <= t < 15:30`
- raw15:30 covers `15:30 <= t < 15:35`
- a row cannot be closed or Candidate-finalized before its true close.

This classification does **not** claim a measured provider revision bound after
true close. Attempt03 provides no independent post-close revision SLA.
`POST_CLOSE_REVISION_BOUND_NOT_ESTABLISHED` remains explicit and
`STATE_CHANGED_OVERLAP` remains exact and fail-closed.

## Canonical owner and migration

`src/daxlab/adapters/ig_market_data.py` is the one owner for raw semantics,
event/close normalization, closure, Candidate finalization, freshness, revision
state and provenance. REST/session code returns raw provider data; the probe and
Candidate lane consume the owner; the RAW diagnostic retains labelled historical
hypotheses only and is not a normalization owner.

| Contract item | Final value |
| --- | --- |
| Market-data schema | `DAXLAB_IG_M5_MARKET_DATA_CONTRACT_V2` |
| Timestamp contract | `IG_MINUTE_5_SNAPSHOT_UTC_INTERVAL_START_V2` |
| Candidate finalization | true close at request-start clock |
| Extra60-second grace | **RETIRED** as superseded interval-end workaround |
| Freshness | observation time minus true close;600-second maximum |
| Candidate envelope | `DAX_IG_CAND001_REAL_HOST_SHADOW_E2E_V3` |
| State contract | `DAX_IG_CAND001_STATE_INTERVAL_START_V3` |
| New state namespace | `.runtime/ig_cand001_shadow_e2e_2237_interval_start_v3` |

The RunManifest dataset fingerprint includes the complete canonical contract and
retired-grace contract. V1/V2 interval-end envelopes, the old grace contract and
old manifests are deterministically rejected with
`STATE_FINALIZATION_CONTRACT_MIGRATION_REQUIRED` or
`STATE_MANIFEST_DRIFT`. There is no silent migration or reset. Historical
runtime/evidence namespaces remain untouched.

## Repository verification and external closeout

Repository tests cover interval-start mapping, true close, active-tail exclusion,
first completed inclusion, true-close freshness, retired grace, legacy rejection,
strict overlap, exact resume anchor, no future/open Candidate row, Operator current
bar, credential-free failure output, NONE/false and the unchanged LIVE boundary.

Step2233 is not marked complete until the final published head succeeds on the
real Windows host for fresh start, next-true-close resume and Operator read. The
single runner is:

`scripts/run_ig_m5_contract_2237.ps1`

It deploys the exact published head, owns one authenticated read-only session,
performs both cycles, preserves `FRESH_START.json`, `RESUME.json`,
`OPERATOR.json` and `SUMMARY.json`, never calls a dealing endpoint, never
relogs/retries, and emits one fixed credential-free error code on every
fail-closed path.

M01 advances because the market-data contract is repository-owned and locally
verified. It remains incomplete pending final-head runtime/account/clock,
inventory/history/economics/stops/risk/reconciliation/restart evidence. The
27-gate set is not all VERIFIED, so no `DEMO_ONLY` promotion and no DEMO order
occurred. Conditional bounded IG DEMO authorization remains recorded; LIVE
remains prohibited.
