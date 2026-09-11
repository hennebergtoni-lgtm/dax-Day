# DAX-BOT 1.x Alpha Acceptance Status

Status: CURRENT GATE STATUS / NO PAPER OR LIVE AUTHORIZATION
Updated: 2026-09-11
Repository branch: `nextgen-bot-line-v1`
Verified head for this snapshot: `de20765b77eed66fecd65bcea519e8e7f4dafd62`

CI at verified head:
- `dax-bot-1x-ci` #38: GREEN
- `research-lab-ci` #822: GREEN

This file maps the current implementation against `docs/DAX_BOT_1X_ALPHA_ACCEPTANCE_GATE.md`. It is a controllability/readiness checklist, not a profitability claim and not execution authorization.

## A. Product/config identity — VERIFIED

Evidence already exists for:
- explicit `DAX-BOT/1.0-alpha/CAND-001` identity;
- deterministic config fingerprint;
- deterministic same-code/config/bar replay;
- strategy-relevant config changes alter identity.

Primary owners/tests:
- `src/daxlab/runtime/product_identity.py`
- `src/daxlab/runtime/candidate_config.py`
- `tests/test_candidate_config.py`
- candidate replay/determinism tests.

## B. Decision-order visibility — PARTIAL / FIX REQUIRED

Implemented:
- signal direction/reason;
- admission result;
- final `TRADE` / `NO_TRADE`;
- blocker/risk result;
- proposed entry/stop/target/RR.

Gap:
- `DecisionRecord` already owns explicit `regime`, `structure`, `setup`, but `OperatorSnapshot` does not yet expose these fields directly.

Required next action:
- reuse `DecisionRecord.regime/structure/setup` in the existing operator snapshot; do not create a parallel strategy explanation model.

## C. Historical/replay determinism — IMPLEMENTED / STRONG, FINAL DUPLICATE-OUTCOME GATE STILL TO CLOSE

Implemented/evidence:
- repeated closed-bar sequence yields identical candidate outputs;
- candidate strategy state save/load/resume matches uninterrupted processing;
- session trade limit survives restart;
- virtual lifecycle OPEN save/load/resume matches uninterrupted lifecycle;
- duplicate lifecycle bar after restart is idempotent;
- restored CLOSED lifecycle rebuilds identical costed outcome.

Remaining gate item:
- prove one end-to-end restart/replay cannot publish duplicate intent/outcome records at the outer integration boundary.

## D. Causality — VERIFIED FOR CURRENT CAND-001 SCOPE

Evidence:
- only closed bars mutate strategy state;
- breakout requires confirmed close outside completed OR15;
- decision time is closed-bar time;
- virtual trade effect cannot occur on the decision bar;
- first eligible virtual fill is on a causal later M5 bar;
- same-bar stop/target ambiguity reuses the frozen conservative stop-first resolver;
- gap-through handling is explicit and versioned.

Research-definition parity remains required only when a future runtime feature is adapted from a research/DataFrame definition.

## E. Paper lifecycle integration — IMPLEMENTED / SHADOW ONLY

Implemented:
- admitted TRADE -> existing `ExecutionIntent`;
- deterministic client identity;
- normalized simulation sizing with explicit non-broker semantics;
- stateful virtual SHADOW lifecycle;
- first-available-open gap semantics;
- conservative same-bar stop-first;
- explicit CAND-001 V1 cost application;
- costed R outcome -> existing `DatedShadowOutcome`;
- forward observation -> existing Forward SHADOW performance -> existing cash ledger;
- virtual lifecycle persistence/restart parity.

Boundary remains:
- PAPER not authorized;
- LIVE not authorized;
- no broker adapter/order path introduced.

## F. Broker safety — VERIFIED

Current safety remains:
- `execution_capability=NONE` on current host-facing and CAND-001 SHADOW paths;
- `order_execution_enabled=false`;
- no DAX-BOT alpha order submission path;
- current full CI GREEN;
- REF-V11.2 remains unchanged frozen reference evidence.

## G. Observability — PARTIAL / FIX REQUIRED

Implemented:
- product/candidate/config identity;
- signal/admission/decision and blockers;
- proposed trade geometry;
- virtual lifecycle status/fill/exit;
- gross-R/cost-R/net-R outcome;
- explicit safety flags.

Current gaps:
1. explicit REGIME / STRUCTURE / SETUP fields in operator payload;
2. health/freshness;
3. last processed closed-bar identity and close time;
4. duplicate/recovery/reconciliation event visibility;
5. fresh runtime source must remain separate from stale static evidence/web truth.

Existing owners to reuse:
- `src/daxlab/runtime/decision.py` for regime/structure/setup;
- `src/daxlab/runtime/bar_identity.py` for closed-bar identity;
- `src/daxlab/runtime/health.py` and current MT5 host/shadow status for health;
- existing restart/reconcile and SHADOW resume owners for recovery/reconciliation semantics.

## H. Existing-capability non-regression — VERIFIED AT SNAPSHOT HEAD

At `de20765b77eed66fecd65bcea519e8e7f4dafd62`:
- `dax-bot-1x-ci` #38 GREEN;
- `research-lab-ci` #822 GREEN;
- REF-V11.2 evidence remains frozen;
- existing research/evidence remains present;
- MT5 SHADOW read-only architecture remains separate and order-disabled;
- no Windows user action was needed for repository-only work.

## Immediate ordered gaps

1. Complete operator decision-order visibility (`regime/structure/setup`).
2. Add last-bar identity/time + freshness to the same operator snapshot.
3. Bridge existing host health/reconcile evidence into operator runtime context without coupling the pure strategy core to MT5.
4. Prove end-to-end duplicate-safe intent/outcome publication across restart/replay.
5. Re-evaluate this gate and only then decide whether `1.0-alpha` controllability can be promoted from IMPLEMENTED to VERIFIED.

Performance/profitability research remains a separate later gate. Demo/PAPER and LIVE authorization remain separate decisions after controllability and broker-economics evidence are ready.
