# DAX-BOT 1.x Alpha Acceptance Gate

Status: PLANNED TEST GOVERNANCE / NO EXECUTION AUTHORIZATION

Purpose: define what must be proven before any DAX-BOT 1.0-alpha strategy path may be treated as a controllable bot rather than merely new code.

## 1. Principle

The existing test estate is the protection layer. DAX-BOT 1.x extends it; it does not replace it wholesale.

A first alpha succeeds on correctness, controllability, observability and restart safety before profitability is considered.

## 2. Existing protections to retain

The current repository already contains protection for:
- runtime contracts, quality and safety gates;
- closed-bar identity, duplicate suppression and chronological replay;
- no-lookahead properties for multiple research features;
- filter registry, activation, readiness, overlap, efficiency and ablation;
- DecisionRecord identity/audit behavior;
- paper ExecutionIntent identity, side, entry/stop/target binding, cost model, same-bar/gap/partial-fill policy and telemetry;
- static proof that paper/runtime paths contain no broker order methods;
- simulation-only capability boundaries;
- replay parity and checkpoints;
- restart/reconciliation;
- MT5 read-only feed, broker time/session, watchdog, supervisor, cross-cycle integrity and recovery drills;
- Windows task/code-parity safety;
- V11.2 frozen-reference protection;
- research registry/hypothesis/evidence integrity;
- web/evidence integrity, noting that the current pre-host operational assertions are STALE/FIX_REQUIRED after the real SHADOW milestone.

These protections remain in force unless a later LEAN/CLEANUP audit proves a particular test obsolete or redundant while preserving its invariant elsewhere.

## 3. New end-to-end tests that DAX-BOT 1.0-alpha must add

Only missing connection-level behavior should be added initially.

### A. Product/config identity
- emitted state identifies `DAX-BOT 1.0-alpha` and one explicit candidate ID;
- complete promoted config snapshot has deterministic fingerprint;
- same code + same config + same closed bars yields same fingerprint and decisions;
- changing a strategy-relevant parameter changes config identity.

### B. Decision-order visibility
For every processed closed bar, the operator-facing decision state can explain:
1. REGIME state;
2. STRUCTURE state;
3. ENTRY/setup state;
4. final `TRADE` or `NO_TRADE` result;
5. reason/blocker codes.

A trade decision additionally exposes deterministic LONG/SHORT, planned entry, stop, target and RR.

### C. Historical/replay determinism
- processing the same persisted bar sequence twice produces byte/field-equivalent canonical decisions;
- checkpoint/restart at arbitrary safe boundaries produces the same final state and decisions as uninterrupted replay;
- duplicate bars do not duplicate decisions, intents or outcomes.

### D. Causality
- only closed bars can affect strategy state;
- future bars cannot affect current REGIME/STRUCTURE/ENTRY output;
- trade intent may not use a bar that was not yet known at decision time;
- virtual lifecycle progresses on later closed bars only, except for an explicitly versioned conservative same-bar policy already covered by the paper contract;
- runtime incremental implementations must parity-test against causal research definitions when adapted from them.

### E. Paper lifecycle integration
- `TRADE` maps into the existing ExecutionIntent contract rather than a second simulator contract;
- Decision ID binds deterministically to intent/client identity;
- side, entry, stop, target, quantity/config and time are identity inputs as already required by paper contracts;
- restart/replay cannot create duplicate virtual orders;
- closed virtual outcome is deterministic under the selected fill/cost policy;
- paper telemetry remains `SIMULATION_ONLY` and never implies broker capability.

### F. Broker safety
- no DAX-BOT alpha module imports or calls MT5 `order_send` or equivalent order APIs;
- host-facing execution remains `execution_capability=NONE` and `order_execution_enabled=false`;
- existing static no-order tests remain green;
- product version changes do not silently change Windows host tasks or execution permissions.

### G. Observability
A safe operator representation exposes at minimum:
- product version;
- candidate/config ID + fingerprint;
- health/freshness;
- last processed bar identity/time;
- REGIME / STRUCTURE / setup;
- final action and reasons/blockers;
- virtual position state, if any;
- planned entry/stop/target/RR;
- outcome/R once closed;
- duplicate/recovery/reconciliation/safety events.

Stable research evidence and fresh runtime status must be separate sources/contracts. The UI must not present stale static operational state as current runtime truth.

### H. Existing-capability non-regression
Before merge of any alpha runtime change:
- full pre-existing CI stays green unless a deliberately stale test is replaced together with an equivalent or stronger invariant;
- REF-V11.2 hashes/evidence remain unchanged;
- research registry/evidence remains accessible;
- existing MT5 SHADOW read-only behavior remains independently operable until explicit migration;
- Windows user action is not required for repository-only development or CI verification.

## 4. Performance gate is separate

This acceptance gate does not claim that the candidate is profitable.

After controllability/correctness are proven, candidate performance must still pass the separate research/OOS/WF/robustness/forward process before any stronger readiness claim.

## 5. Promotion rule

`DAX-BOT 1.0-alpha` remains PLANNED or IMPLEMENTED until the applicable tests above are evidence-backed GREEN.

No single successful smoke test, attractive backtest, or real-time observation is sufficient to mark the product VERIFIED.