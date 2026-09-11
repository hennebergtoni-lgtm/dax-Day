# DAX-BOT 1.0-alpha Closeout Report — DRAFT

Status: DRAFT / NOT FINAL / NO PROFITABILITY OR EXECUTION CLAIM
Updated: 2026-09-11
Product: `DAX-BOT/1.0-alpha/CAND-001`

This document is the working closeout required by the Step-2000 migration audit. It becomes FINAL only after exact-head CI is GREEN and the final alpha acceptance/non-regression audit is complete. Real Windows/MT5 deployment evidence remains a separate `WAITING_EXTERNAL` lane.

## 1. Architectural advantages versus the legacy/reference line

### Explicit product and candidate identity
- REF-V11.2 remains frozen reference evidence instead of being silently mutated into the new bot.
- DAX-BOT product version, Candidate ID, config fingerprint and forward RunManifest are explicit and deterministic.

### Causal closed-bar processing
- strategy state mutates only on closed bars;
- confirmed breakout uses completed OR15 and close confirmation;
- virtual trade effect begins only on a later causal bar;
- observation/transport time is separated from market-event identity.

### Small composable runtime instead of hidden coupling
- Candle -> Signal -> TradePlan -> Admission -> DecisionRecord -> ExecutionIntent -> virtual lifecycle -> outcome -> telemetry are separate owners;
- existing contracts are reused instead of creating parallel paper/order models;
- MT5 host safety remains a separate gate and strategy code has no broker-order API.

### Restart/recovery safety
- strategy state, active trade evidence, virtual lifecycle and publication state are persistable;
- one tamper-evident Candidate SHADOW checkpoint binds the complete runtime state;
- sliding MT5 window overlap is suppressed deterministically;
- deterministic IDs are combined with durable publication admission so restart cannot silently republish the same Intent/Outcome.

### Operator observability
- OperatorSnapshot V3 exposes product/candidate/config, REGIME/STRUCTURE/SETUP, decision/blockers, trade geometry, current virtual position, origin trade decision, outcome/R, health/freshness and runtime/recovery events;
- fresh Candidate runtime telemetry is separate from static versioned web evidence;
- static `web/status.json` is forbidden from pretending to be current host/runtime truth.

### Engineering memory / reuse
- solved non-obvious problems are recorded as Problem -> Root Cause -> Fix -> Regression -> Reuse rules;
- public-project architecture patterns are consulted before new platform code is added;
- session-resume governance requires integer-only steps and continuation across lane-local blockers.

## 2. Concrete defects / false assumptions discovered and corrected

### PSR-011 — lifecycle contracts existed but no stateful virtual position owner
A contract vocabulary, same-bar resolver and downstream outcome/ledger existed, but no component actually carried one virtual position across later bars. A minimal SHADOW-only lifecycle was added by reusing the existing owners.

### PSR-012 — first lifecycle integration did not apply the configured cost model
Spread/slippage/commission contracts existed but the first virtual lifecycle path would have produced optimistic outcomes if costs were silently omitted. Price-path and costed outcome semantics were separated and versioned.

### PSR-013 — deterministic ID was not sufficient for restart-safe publication
An in-memory deduplicator forgot prior publications after restart. Durable Intent/Outcome publication admission was added on top of deterministic IDs.

### PSR-014 — `M5` versus `5m` literal drift
Feed and lifecycle could each pass isolated tests while being incompatible when connected. `5m` is now the canonical CAND-001 runtime representation and the integration boundary is regression-tested.

### PSR-015 — `received_at` incorrectly changed causal strategy identity
The same already-closed market bar could receive a new Decision ID when re-fetched later because transport observation time was fingerprinted. `received_at` remains observability metadata but no longer changes causal strategy identity.

### Multi-bar OperatorSnapshot origin bug
The first snapshot runtime binding assumed the current bar decision and the open position's origin decision were the same. This is false once a trade remains open across later `NO_TRADE` bars. Snapshot V3 explicitly separates current decision from `origin_decision_id`.

### Web runtime truth drift
Historical pre-host/runtime fields remained embedded in static `web/status.json` and old V10/V11 tests enforced them. Web V2 now makes static evidence and fresh runtime truth separate contracts; stale tests/smokes are being migrated to the stronger invariant.

### Database/recovery migration-chain drift
Adding Candidate telemetry migrations exposed hard-coded `0001..0007` assumptions in recovery/DB gates. Canonical migration integrity and restore drills were extended to the new telemetry table/current view rather than weakening the checks.

### Process continuity defect
A Windows/host dependency was repeatedly treated as a global project stop. Governance now classifies host/user dependencies as lane-local `WAITING_EXTERNAL`; independent safe work must continue.

## 3. Measured runtime/performance evidence

Latest CI benchmark artifact currently captured for CAND-001:
- schema: `DAX_BOT_CAND001_BENCHMARK_V1`
- 50 synthetic sessions
- 103 bars/session
- 5,150 pipeline events per repeat
- 3 repeats
- median: `299658.745 ns/event` (~299.7 microseconds/event)
- P95: `301131.76 ns/event` (~301.1 microseconds/event)
- median throughput: `3337.129 events/second`
- platform: GitHub-hosted Linux/Azure, Python 3.11.16
- gate: `OBSERVATION_ONLY`, not a profitability or hard latency gate

Earlier CAND-001 observation was approximately 309 microseconds/event and ~3,232 events/second. The newer observation is modestly faster, but this is not treated as a rigorous before/after optimization claim because environment/head differences exist.

Research-efficiency improvements are architectural/process improvements (FAST screening, checkpoints/resume, smaller targeted candidate surfaces, separated feed/cache/runtime paths). No unsupported end-to-end speedup factor versus the historical multi-hour 14,400-test research runs is claimed here without a comparable benchmark.

## 4. Current safety/readiness

### SHADOW
Repository-integrated CAND-001 SHADOW architecture is implemented and has green evidence at prior exact heads. Latest-head CI must be GREEN before final closeout.

Real Windows/MT5 deployment evidence for the current branch is still `WAITING_EXTERNAL` and requires the prepared runbook.

### Demo / PAPER
NOT AUTHORIZED.

Progress made toward later demo readiness:
- broker symbol economics are now captured read-only;
- a fail-closed BrokerEconomicsReadiness gate exists;
- a research-only cash-risk -> broker-volume estimator exists;
- BASE/BOOST/HIGH research profiles use explicit cash-at-stop budgets under a hard cap and do not infer account percentages.

Still required before demo broker orders:
- current real DE40 demo-broker economics verified on host;
- broker-aware sizing policy promoted from research with explicit limits;
- execution adapter/order lifecycle ACK/REJECT/PARTIAL/FILLED/CANCELLED path;
- reconnect/reconciliation against broker state;
- max-spread/stale-feed/duplicate/contradictory-state blockers at execution boundary;
- explicit PAPER readiness gate and user authorization.

### LIVE / real money
NOT AUTHORIZED / NOT ELIGIBLE.

Software correctness is not profitability evidence. LIVE requires successful SHADOW and PAPER evidence, validated broker execution/reconciliation, risk controls, performance/robustness evidence and explicit later authorization.

## 5. Public-project patterns adopted

- QuantConnect LEAN: separation of alpha/decision, risk and execution responsibilities; lower-resolution data can be consolidated upward.
- NautilusTrader: same strategy semantics across simulation/forward; persistence and reconciliation are first-class.
- Freqtrade: dry/forward validation separate from backtest and independent protections such as drawdown/cooldown gates.
- vectorbt: causal event simulation and no hidden same-bar execution.

Only engineering/methodology patterns are adopted. No public strategy is copied into CAND-001.

## 6. Scope deliberately kept out of 1.0-alpha blocking gate

The following remain 1.x research/product enhancements and must not delay the minimal controllable alpha:
- FAST/M1 candidate;
- authenticated browser/API delivery of fresh runtime telemetry;
- active operator Risk/Exposure UI control;
- active News/Event reaction modes;
- broker order execution.

Their contracts/research may exist, but they do not silently mutate CAND-001.

## 7. Finalization checklist

Before changing this file from DRAFT to FINAL:
1. exact latest PR head pinned;
2. `dax-bot-1x-ci` GREEN on that head;
3. `research-lab-ci` GREEN on that head;
4. final A-H alpha acceptance review against current code/evidence;
5. REF-V11.2 hashes/evidence unchanged;
6. PR/milestone documentation updated to current truth;
7. outstanding Windows/MT5 evidence explicitly labelled `WAITING_EXTERNAL` if not yet completed;
8. no PAPER/LIVE authorization implied;
9. final report explicitly states that controllability/correctness do not prove profitability.
