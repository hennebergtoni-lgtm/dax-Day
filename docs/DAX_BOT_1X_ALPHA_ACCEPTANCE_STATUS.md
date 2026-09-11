# DAX-BOT 1.x Alpha Acceptance Status

Status: REPOSITORY-SIDE 1.0-ALPHA ACCEPTED / REAL WINDOWS HOST EVIDENCE WAITING_EXTERNAL / PAPER AND LIVE NOT AUTHORIZED
Updated: 2026-09-11
Repository branch: `nextgen-bot-line-v1`
Verified acceptance head: `2df6e20893144f87f04511823bc7b72699ad7cce`

Exact-head verification:
- `dax-bot-1x-ci` #144: GREEN
- `research-lab-ci` #928: GREEN

This file maps the current product against `docs/DAX_BOT_1X_ALPHA_ACCEPTANCE_GATE.md`. Acceptance here is a controllability/determinism/observability/restart-safety milestone. It is not a profitability claim and does not authorize demo/PAPER broker orders or LIVE trading.

## A. Product/config identity — VERIFIED

- explicit `DAX-BOT/1.0-alpha/CAND-001` identity;
- deterministic config fingerprint;
- strategy-relevant config changes alter identity;
- forward RunManifest binds Candidate/config/runtime/fill-model provenance.

## B. Decision-order visibility — VERIFIED

Canonical OperatorSnapshot exposes:
- REGIME / STRUCTURE / SETUP;
- signal and admission;
- final TRADE / NO_TRADE plus blockers;
- entry/stop/target/RR;
- current virtual position and its origin decision.

## C. Determinism/restart — VERIFIED

- repeated closed-bar sequence is deterministic;
- strategy state save/load/resume matches uninterrupted processing;
- session trade limit survives restart;
- virtual lifecycle save/load/resume is deterministic;
- duplicate bars are idempotent;
- restored CLOSED lifecycle rebuilds the same costed outcome;
- deterministic Intent/Outcome IDs are protected by durable publication admission;
- complete Candidate SHADOW state is atomically checkpointed;
- sliding MT5 overlap is suppressed from persisted close-time;
- transport-only `received_at` does not alter causal strategy identity.

## D. Causality — VERIFIED

- only CLOSED bars mutate strategy state;
- OR15 breakout requires confirmed close outside completed opening range;
- virtual trade effect cannot occur on the decision bar;
- first virtual fill is causal on a later bar;
- existing positions advance before the current bar's new strategy decision;
- same-bar stop/target ambiguity reuses conservative stop-first policy;
- gap behavior is explicit/versioned.

## E. Virtual lifecycle / outcome integration — VERIFIED

Verified chain:
`Decision -> ExecutionIntent -> virtual lifecycle -> costed outcome -> DatedShadowOutcome -> ForwardPerformance / cash ledger`.

Also verified:
- multi-bar position ownership;
- restart parity;
- duplicate-safe publication;
- gross/cost/net-R observability.

This remains SHADOW simulation only.

## F. Broker safety — VERIFIED IN REPOSITORY / CURRENT REAL-HOST RECHECK WAITING_EXTERNAL

Repository-side invariants:
- `execution_capability=NONE`;
- `order_execution_enabled=false`;
- no DAX-BOT alpha `mt5.order_send` path introduced;
- CAND-001 only processes data after the existing MT5 SHADOW host gate allows it;
- invalid/missing single-instance safety blocks Candidate processing;
- REF-V11.2 is unchanged frozen evidence.

PR #109 hard-invariant audit at accepted head:
- complete changed-file list contains no path under `research/V112_REFERENCE_V1/`;
- PR patch contains no `mt5.order_send` call;
- no `order_execution_enabled=True` safety inversion was found;
- Candidate telemetry DB schema additionally constrains `execution_capability='NONE'` and `order_execution_enabled=false`.

Real Windows/MT5 deployment verification of the current Candidate-integrated branch remains `WAITING_EXTERNAL`. It is required before stronger current-host operational claims, but it is not a repository-side alpha blocker.

## G. Observability — VERIFIED FOR ALPHA SCOPE

Implemented/tested representation includes:
- product/candidate/config identity;
- strategy context and final decision;
- bar identity/time/freshness;
- input health and runtime events;
- virtual fill/position/exit;
- origin decision identity;
- gross/cost/net R;
- safety and recovery/reconciliation fields.

Fresh runtime chain:
- local `candidate_operator_snapshot.json`;
- credential-free Candidate telemetry validation;
- append-only Neon `cand001_operator_snapshots`;
- read-only `cand001_operator_current` view;
- validated server/operator read adapter.

Static `web/status.json` is `DAXLAB_WEB_STATIC_STATUS_V2` and explicitly excludes current runtime truth.

Authenticated browser/API delivery is POST-ALPHA 1.x scope, not an alpha blocker. Neon credentials must never be exposed to the browser.

## H. Existing-capability non-regression — VERIFIED

At accepted head `2df6e20893144f87f04511823bc7b72699ad7cce`:
- full Candidate CI is GREEN (#144);
- full research/non-regression CI is GREEN (#928);
- stale V10/V11 static-web tests and pre-host smoke were migrated to the stronger Web V2 static/runtime separation invariant rather than weakening safety;
- recovery, DB migration-integrity and restore checks are green;
- REF-V11.2 frozen evidence remains untouched.

## Promotion decision

**DAX-BOT 1.0-alpha repository-side acceptance: PASSED.**

Canonical closeout:
`docs/DAX_BOT_1_0_CLOSEOUT_FINAL.md`

This means the new product line has reached the intended software/control alpha milestone: versioned, causal, deterministic, restart-safe, duplicate-safe, observable and explicitly order-disabled.

It does **not** mean:
- profitability proven;
- current real Windows Candidate deployment verified;
- demo/PAPER broker execution authorized;
- LIVE trading authorized.

## Next independent lanes

1. `WAITING_EXTERNAL`: current-branch Windows/MT5 SHADOW deployment verification using `docs/CAND001_WINDOWS_SHADOW_DEPLOYMENT_RUNBOOK_V1.md`.
2. Demo/PAPER preparation: verify real broker economics, promote a separately validated sizing/risk owner, build/verify broker execution lifecycle and reconciliation, then pass a later PAPER readiness/user authorization gate.
3. Post-alpha 1.x product work: authenticated fresh-runtime browser delivery.
4. Independent research: FAST/M1 candidate, bounded Risk/Exposure profiles, News/Event awareness.

Performance/profitability remains a separate research and forward-evidence problem. LIVE remains a later, independently gated stage.
