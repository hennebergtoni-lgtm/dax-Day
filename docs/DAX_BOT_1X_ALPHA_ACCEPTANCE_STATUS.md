# DAX-BOT 1.x Alpha Acceptance Status

Status: REPOSITORY-INTEGRATED SHADOW RUNTIME VERIFIED / REAL WINDOWS HOST EVIDENCE WAITING_EXTERNAL / NO PAPER OR LIVE AUTHORIZATION
Updated: 2026-09-11
Repository branch: `nextgen-bot-line-v1`
Last fully verified integrated-runtime head: `a5b8429545d03bba1e1aade2bbd1e4ebc06560fe`

CI at that integrated-runtime head:
- `dax-bot-1x-ci` #85: GREEN
- `research-lab-ci` #869: GREEN

Newer Candidate-telemetry/static-web separation changes are IMPLEMENTED on the branch and remain subject to exact-head CI verification before being labelled VERIFIED.

This file maps the current implementation against `docs/DAX_BOT_1X_ALPHA_ACCEPTANCE_GATE.md`. It is a controllability/readiness checklist, not a profitability claim and not execution authorization.

## A. Product/config identity — VERIFIED

Evidence:
- explicit `DAX-BOT/1.0-alpha/CAND-001` identity;
- deterministic config fingerprint;
- deterministic same-code/config/bar replay;
- strategy-relevant config changes alter identity;
- forward-stream RunManifest binds broker symbol, canonical symbol/timeframe, broker-time contract, candidate config, sizing, ruleset/core and fill-model semantics.

## B. Decision-order visibility — VERIFIED

The existing `OperatorSnapshot` exposes the existing owners rather than inventing a second explanation model:
- REGIME;
- STRUCTURE;
- SETUP;
- signal direction/reason;
- admission result;
- final `TRADE` / `NO_TRADE`;
- blockers/risk result;
- proposed entry/stop/target/RR;
- origin decision identity for an active multi-bar virtual position.

## C. Historical/replay determinism — VERIFIED FOR CURRENT CAND-001 SHADOW RUNTIME

Evidence:
- repeated closed-bar sequence yields identical candidate outputs;
- candidate strategy state save/load/resume matches uninterrupted processing;
- session trade limit survives restart;
- virtual lifecycle OPEN save/load/resume matches uninterrupted lifecycle;
- duplicate lifecycle bar after restart is idempotent;
- restored CLOSED lifecycle rebuilds identical costed outcome;
- deterministic Intent and Outcome identities pass a durable publication-admission journal;
- atomic save/load/restart rejects duplicate Intent/Outcome publication;
- complete candidate SHADOW state is bound into one tamper-evident checkpoint envelope;
- sliding MT5-feed overlap is filtered against persisted candidate close-time;
- transport-only `received_at` no longer changes causal strategy identity;
- same market bar fetched at a later observation time retains the same signal/decision identity.

## D. Causality — VERIFIED FOR CURRENT CAND-001 SCOPE

Evidence:
- only closed bars mutate strategy state;
- breakout requires confirmed close outside completed OR15;
- decision time is closed-bar time;
- virtual trade effect cannot occur on the decision bar;
- first eligible virtual fill is on a causal later bar;
- an existing position is advanced on the current closed bar before the current bar's new strategy decision is evaluated;
- same-bar stop/target ambiguity reuses the frozen conservative stop-first resolver;
- gap-through handling is explicit and versioned;
- `received_at` is transport/observability metadata, not strategy identity input.

Research-definition parity remains required when a future runtime feature is adapted from a research/DataFrame definition.

## E. Virtual lifecycle / outcome integration — VERIFIED FOR SHADOW SIMULATION CHAIN

Verified chain:
- admitted TRADE -> existing `ExecutionIntent`;
- deterministic client identity;
- normalized simulation sizing with explicit non-broker semantics;
- stateful virtual SHADOW lifecycle;
- first-available-open gap semantics;
- conservative same-bar stop-first;
- explicit CAND-001 V1 cost application;
- costed R outcome -> existing `DatedShadowOutcome`;
- forward observation -> existing Forward SHADOW performance -> existing cash ledger;
- virtual lifecycle persistence/restart parity;
- restart-safe publication admission for Intent and Outcome;
- multi-bar orchestrator keeps current decision and origin trade decision separate.

Boundary remains unchanged:
- PAPER not authorized;
- LIVE not authorized;
- no broker order adapter/path introduced.

## F. Broker safety — VERIFIED IN REPOSITORY / REAL HOST RECHECK WAITING_EXTERNAL

Repository-side safety:
- `execution_capability=NONE` on host-facing and CAND-001 SHADOW surfaces;
- `order_execution_enabled=false`;
- no DAX-BOT alpha order submission path;
- CAND-001 runs only after the existing MT5 SHADOW gate allows the feed;
- missing/invalid single-instance host safety blocks Candidate processing;
- REF-V11.2 remains unchanged frozen reference evidence.

Real-host evidence still required after deployment of the current branch:
- run the prepared Windows/MT5 deployment verification on the real host;
- prove heartbeat GREEN with current code;
- prove Candidate checkpoint/operator snapshot files advance on real CLOSED-M5 data;
- prove no broker order path/capability is enabled.

Status for that dependency lane: `WAITING_EXTERNAL`, not a global project stop.

## G. Observability — FRESH RUNTIME SOURCE IMPLEMENTED / BROWSER DELIVERY OPEN

Implemented/tested operator surface:
- product/candidate/config identity;
- REGIME / STRUCTURE / SETUP;
- signal/admission/decision and blockers;
- proposed trade geometry;
- last closed-bar identity/time and freshness;
- candidate input health and duplicate/data-unsafe/out-of-order events;
- virtual lifecycle status/fill/exit;
- origin trade decision identity across later bars;
- gross-R/cost-R/net-R outcome;
- explicit safety flags;
- recovery/reconciliation fields.

Integrated runtime assembly:
- `candidate_mt5_feed.py` converts validated CLOSED-M5 feed bars into canonical Candidate candles;
- `candidate_shadow_orchestrator.py` coordinates decision -> intent -> lifecycle -> outcome -> publication -> operator snapshot;
- `candidate_shadow_feed_runtime.py` handles sliding-feed overlap/resume;
- `candidate_mt5_shadow_runtime.py` binds Candidate processing behind the existing MT5 safety gate;
- `candidate_shadow_checkpoint.py` persists the complete Candidate SHADOW state atomically;
- `candidate_shadow_host_cycle.py` provides a stable forward-stream RunManifest and one persistent host-cycle boundary;
- `scripts/mt5_shadow_supervisor.py` stages Candidate Intent/Outcome evidence before advancing Candidate checkpoint/operator snapshot, while preserving the existing supervisor/lock/probe owner.

Fresh runtime source now IMPLEMENTED on the branch:
- supervisor atomically writes `candidate_operator_snapshot.json` from canonical `OperatorSnapshot.as_dict()`;
- `candidate_operator_telemetry.py` validates credential-free/read-only safety semantics;
- `export_mt5_shadow_telemetry.py` can append Candidate snapshots to Neon without changing its legacy export contract;
- migration `0008` adds append-only `cand001_operator_snapshots` with deterministic `snapshot_fingerprint` idempotency and DB-level `NONE/false` checks;
- migration `0009` adds read-only latest view `cand001_operator_current`;
- `web/status.json` is being converted to an explicit static-evidence-only schema and must not represent current host health.

Remaining independent observability gap:
- an authenticated/safe backend/browser delivery endpoint for `cand001_operator_current` is not yet implemented;
- Neon credentials must never be exposed directly to the browser;
- Web V1 remains read-only; planned V2 controls remain disabled/research-only until their backend owners are separately verified.

## H. Existing-capability non-regression — VERIFIED AT LAST FULLY GREEN RUNTIME HEAD

At `a5b8429545d03bba1e1aade2bbd1e4ebc06560fe`:
- `dax-bot-1x-ci` #85 GREEN;
- `research-lab-ci` #869 GREEN;
- REF-V11.2 evidence remains frozen;
- research/evidence remains present;
- existing MT5 SHADOW read-only architecture remains independently operable and order-disabled;
- repository-only implementation/testing required no Windows user action.

Newer telemetry/web changes require their own exact-head CI result before this section advances.

## Current promotion decision

`DAX-BOT 1.0-alpha` is **VERIFIED for the repository-integrated, restart-safe, read-only CAND-001 SHADOW runtime architecture** at the last fully green runtime head.

It is **NOT YET VERIFIED on the user's real Windows/MT5 host with the current branch**, because that evidence requires external host execution. That lane is `WAITING_EXTERNAL`.

Do not promote to PAPER/demo broker-order execution merely because repository integration is green. Broker sizing/economics, demo execution/reconciliation and explicit PAPER authorization remain separate gates.

## Immediate ordered work lanes

1. `WAITING_EXTERNAL`: deploy/current-branch verification on the real Windows/MT5 host using `docs/CAND001_WINDOWS_SHADOW_DEPLOYMENT_RUNBOOK_V1.md`.
2. Continue independently: finish exact-head CI for Candidate operator telemetry and static/runtime web separation.
3. Continue independently: implement a safe backend/browser read endpoint over the fresh Candidate runtime source; never expose Neon credentials in the browser.
4. Continue independently: refresh PR/milestone documentation to current integrated-runtime truth.
5. Continue research independently: M1/FAST candidate, operator risk/exposure profiles and news/event awareness remain preregistered research only and cannot silently mutate CAND-001.

Performance/profitability research remains a separate gate. Demo/PAPER and LIVE authorization remain separate decisions after controllability, broker economics and execution/reconciliation safety are evidence-backed.
