# DAX-BOT 1.x Alpha Acceptance Status

Status: COMPONENT CONTROLLABILITY VERIFIED / REAL CANDIDATE SHADOW ORCHESTRATION STILL REQUIRED / NO PAPER OR LIVE AUTHORIZATION
Updated: 2026-09-11
Repository branch: `nextgen-bot-line-v1`
Verified runtime-code head: `d689f49d3c7d3ddee97b2489960c1f1b2e694346`
Governance head before this status update: `aa46ebdb24c2d74c171a3ebfc6a069a67d25f93e`

CI at the verified runtime-code head:
- `dax-bot-1x-ci` #50: GREEN
- `research-lab-ci` #834: GREEN

This file maps the current implementation against `docs/DAX_BOT_1X_ALPHA_ACCEPTANCE_GATE.md`. It is a controllability/readiness checklist, not a profitability claim and not execution authorization.

## A. Product/config identity — VERIFIED

Evidence:
- explicit `DAX-BOT/1.0-alpha/CAND-001` identity;
- deterministic config fingerprint;
- deterministic same-code/config/bar replay;
- strategy-relevant config changes alter identity.

## B. Decision-order visibility — VERIFIED

The existing `OperatorSnapshot` now exposes the existing owners rather than inventing a second explanation model:
- REGIME;
- STRUCTURE;
- SETUP;
- signal direction/reason;
- admission result;
- final `TRADE` / `NO_TRADE`;
- blockers/risk result;
- proposed entry/stop/target/RR.

## C. Historical/replay determinism — VERIFIED FOR CURRENT CAND-001 SHADOW COMPONENTS

Evidence:
- repeated closed-bar sequence yields identical candidate outputs;
- candidate strategy state save/load/resume matches uninterrupted processing;
- session trade limit survives restart;
- virtual lifecycle OPEN save/load/resume matches uninterrupted lifecycle;
- duplicate lifecycle bar after restart is idempotent;
- restored CLOSED lifecycle rebuilds identical costed outcome;
- deterministic Intent and Outcome identities now pass a durable publication-admission journal;
- after atomic save/load/restart the same Intent or Outcome is rejected from duplicate publication;
- tampered publication state fails closed.

Primary new evidence:
- `src/daxlab/runtime/candidate_publication_state.py`;
- `tests/test_candidate_publication_state.py`;
- PSR-013.

## D. Causality — VERIFIED FOR CURRENT CAND-001 SCOPE

Evidence:
- only closed bars mutate strategy state;
- breakout requires confirmed close outside completed OR15;
- decision time is closed-bar time;
- virtual trade effect cannot occur on the decision bar;
- first eligible virtual fill is on a causal later M5 bar;
- same-bar stop/target ambiguity reuses the frozen conservative stop-first resolver;
- gap-through handling is explicit and versioned.

Research-definition parity remains required when a future runtime feature is adapted from a research/DataFrame definition.

## E. Virtual lifecycle / outcome integration — VERIFIED FOR SHADOW SIMULATION COMPONENT CHAIN

Verified component chain:
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
- restart-safe publication admission for Intent and Outcome.

Boundary remains unchanged:
- PAPER not authorized;
- LIVE not authorized;
- no broker order adapter/path introduced.

## F. Broker safety — VERIFIED

Current safety remains:
- `execution_capability=NONE` on host-facing and CAND-001 SHADOW surfaces;
- `order_execution_enabled=false`;
- no DAX-BOT alpha order submission path;
- REF-V11.2 remains unchanged frozen reference evidence.

## G. Observability — COMPONENTS VERIFIED / REAL RUNTIME ASSEMBLY FIX REQUIRED

Implemented and tested in the existing operator surface:
- product/candidate/config identity;
- REGIME / STRUCTURE / SETUP;
- signal/admission/decision and blockers;
- proposed trade geometry;
- last closed-bar identity/time and freshness;
- candidate input health and duplicate/data-unsafe/out-of-order events;
- virtual lifecycle status/fill/exit;
- gross-R/cost-R/net-R outcome;
- explicit safety flags;
- generic recovery/reconciliation fields.

Implemented host bridge:
- `operator_runtime_bridge.py` translates existing `HostShadowStatus`, resume telemetry and `RestartReconcileResult` into generic operator health/recovery/reconciliation context;
- it remains MT5-read-only and cannot authorize execution.

Remaining real gap:
- the exact runtime tree contains no dedicated CAND-001 forward/SHADOW orchestrator that combines these components on the real MT5 CLOSED-M5 feed across cycles;
- current real MT5 SHADOW integration remains the legacy NO_ORDER observation/soak owner;
- therefore CAND-001 has verified components but has not yet been proven as one restart-safe real-feed SHADOW runtime;
- fresh runtime web/operator publication remains separate from stale static `web/status.json` and must not be faked by versioned GitHub state.

## H. Existing-capability non-regression — VERIFIED AT RUNTIME-CODE HEAD

At `d689f49d3c7d3ddee97b2489960c1f1b2e694346`:
- `dax-bot-1x-ci` #50 GREEN;
- `research-lab-ci` #834 GREEN;
- REF-V11.2 evidence remains frozen;
- research/evidence remains present;
- existing MT5 SHADOW read-only architecture remains independently operable and order-disabled;
- no Windows user action was required for repository-only implementation/testing.

The later `aa46ebdb...` change only updated the durable Problem/Solution Registry and did not modify runtime code.

## Current promotion decision

`DAX-BOT 1.0-alpha` is now **VERIFIED at the component-controllability level**, but **NOT YET VERIFIED as a real-feed integrated CAND-001 SHADOW runtime**.

Do not promote to PAPER/demo execution merely because the component gate is green.

## Immediate ordered gaps

1. Reuse the existing validated MT5 `ClosedM5Feed`/`Mt5Bar` owner and define one explicit conversion into the canonical runtime `Candle` contract, preserving broker timestamp semantics and closed-bar causality.
2. Build one thin CAND-001 SHADOW orchestrator over existing owners: candidate state -> decision -> optional Intent -> virtual lifecycle -> outcome -> publication state -> operator snapshot. Do not create a second host, broker or recovery platform.
3. Bind the orchestrator to the existing MT5 SHADOW gate/resume/single-instance evidence in observation-only mode and prove continuous-vs-restart identity on real-feed-shaped fixtures.
4. Produce a fresh operator-runtime payload/source separately from stable static web evidence.
5. Re-evaluate this gate. Only after the integrated real-feed CAND-001 SHADOW path is GREEN should PAPER/demo broker-order preparation become the next authorization discussion.

Performance/profitability research remains a separate gate. Demo/PAPER and LIVE authorization remain separate decisions after controllability, broker economics and broker execution/reconciliation safety are evidence-backed.
