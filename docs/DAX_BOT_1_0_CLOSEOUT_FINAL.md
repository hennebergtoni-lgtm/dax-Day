# DAX-BOT 1.0-alpha Closeout Report — FINAL

Status: FINAL REPOSITORY-SIDE ALPHA CLOSEOUT / NO PROFITABILITY OR EXECUTION CLAIM
Updated: 2026-09-11
Product: `DAX-BOT/1.0-alpha/CAND-001`
Verified code/evidence head: `2df6e20893144f87f04511823bc7b72699ad7cce`
Verification:
- `dax-bot-1x-ci` #144: GREEN
- `research-lab-ci` #928: GREEN

This report closes the repository-side DAX-BOT 1.0-alpha controllability, determinism, observability and restart-safety milestone. It does not authorize demo/PAPER broker orders or LIVE trading and does not claim profitability. Real Windows/MT5 deployment evidence for the current Candidate-integrated branch remains a separate `WAITING_EXTERNAL` lane.

## 1. What improved versus the legacy/reference line

### Explicit identity and versioning
- REF-V11.2 remains frozen reference evidence and was not silently mutated into the new product.
- DAX-BOT version, Candidate ID, config fingerprint and forward RunManifest are explicit and deterministic.
- Research candidates and product runtime are separated rather than conflated.

### Causal closed-bar runtime
- only CLOSED bars mutate strategy state;
- OR15 breakout requires confirmed close outside the completed opening range;
- virtual trade effect begins only on a later causal bar;
- transport observation time is separated from market-event identity.

### Composable architecture
The runtime is separated into existing/small owners instead of a monolith:
`Candle -> Signal -> TradePlan -> Admission -> DecisionRecord -> ExecutionIntent -> virtual lifecycle -> outcome -> telemetry`.

Existing paper, same-bar, outcome, ledger, host-safety and recovery owners are reused. Strategy code has no broker order API.

### Restart and duplicate safety
- strategy state, active-trade evidence, virtual lifecycle and publication state are persistable;
- one tamper-evident Candidate SHADOW checkpoint binds the complete runtime state;
- sliding MT5 window overlap is suppressed deterministically;
- deterministic IDs plus a durable publication-admission journal prevent restart duplicate Intent/Outcome publication.

### Operator visibility
OperatorSnapshot V3 exposes product/candidate/config, REGIME/STRUCTURE/SETUP, signal/admission/decision/blockers, trade geometry, current virtual position, origin trade decision, outcome/R, health/freshness and runtime/recovery events.

Fresh Candidate runtime telemetry is separate from static versioned web evidence. `web/status.json` is forbidden from pretending to be current host/runtime truth.

### Durable engineering memory
Solved non-obvious failures are recorded as `Problem -> Root Cause -> Fix -> Regression -> Reuse rule`, public-project patterns are consulted before building new infrastructure, and resume governance requires integer-only steps and continuation across lane-local blockers.

## 2. Important defects and false assumptions found and corrected

### PSR-011 — lifecycle vocabulary existed, but no stateful virtual position owner
Contracts, same-bar resolution and downstream outcome/ledger existed, but nothing carried a virtual position across later bars. A minimal SHADOW-only lifecycle was added by reusing the existing owners.

### PSR-012 — first lifecycle integration omitted configured costs
Spread/slippage/commission contracts existed, but the first virtual path would have produced optimistic results if costs remained silent. Price-path and costed-outcome semantics are now explicitly separated and versioned.

### PSR-013 — deterministic IDs were not restart-safe publication by themselves
The old process-local deduplicator forgot previous publications after restart. Durable Intent/Outcome publication admission was added on top of deterministic IDs.

### PSR-014 — `M5` versus `5m` literal drift
Feed and lifecycle could each pass isolated tests while being incompatible together. `5m` is the canonical CAND-001 runtime representation and the integration boundary is regression-tested.

### PSR-015 — `received_at` incorrectly changed causal strategy identity
The same already-closed market bar could receive a new Decision ID when fetched later because transport time was fingerprinted. `received_at` remains observability metadata but no longer changes strategy identity.

### Multi-bar OperatorSnapshot origin bug
The first runtime binding assumed current-bar Decision ID and the open position's origin Decision ID were identical. This fails once a position survives later `NO_TRADE` bars. Snapshot V3 explicitly separates current decision and `origin_decision_id`.

### Static web/runtime truth drift
Historical pre-host/runtime fields remained in static `web/status.json`, and old V10/V11 tests enforced them. Web V2 now separates static evidence from fresh runtime truth; stale tests and the old pre-host smoke were migrated to the stronger invariant.

### Database/recovery migration-chain drift
Candidate telemetry migrations exposed hard-coded assumptions ending at migration `0007`. Recovery, DB-integrity and restore gates were extended to `0008/0009` rather than weakened.

### Process-continuity defect
A Windows/host dependency was repeatedly mistaken for a global project stop. Governance now classifies external dependencies as lane-local `WAITING_EXTERNAL`; independent safe work must continue.

## 3. Measured performance evidence

Latest captured CAND-001 CI benchmark evidence:
- schema `DAX_BOT_CAND001_BENCHMARK_V1`;
- 50 synthetic sessions;
- 103 bars/session;
- 5,150 pipeline events/repeat;
- 3 repeats;
- median `299658.745 ns/event` (~299.7 microseconds/event);
- P95 `301131.76 ns/event` (~301.1 microseconds/event);
- median throughput `3337.129 events/second`;
- GitHub-hosted Linux/Azure, Python 3.11.16;
- observation-only, not a hard latency or profitability gate.

An earlier CAND-001 observation was approximately 309 microseconds/event and ~3,232 events/second. The newer result is modestly faster, but no rigorous end-to-end speedup percentage is claimed because environment/head differences exist.

Research efficiency improved structurally through FAST screening, targeted candidate surfaces, checkpoints/resume and separated cache/feed/runtime paths. No unsupported speedup factor versus historical multi-hour 14,400-test runs is claimed without a comparable benchmark.

## 4. Final alpha acceptance / hard invariants

At verified head `2df6e20893144f87f04511823bc7b72699ad7cce`:
- both required CI gates are GREEN;
- the full PR changed-file set contains no file under `research/V112_REFERENCE_V1/`;
- REF-V11.2 remains frozen;
- no `mt5.order_send` path is introduced by PR #109;
- no `order_execution_enabled=True` safety inversion was found in the PR change line;
- Candidate telemetry additionally enforces `execution_capability='NONE'` and `order_execution_enabled=false` at database level;
- PAPER/demo broker execution remains unauthorized;
- LIVE remains unauthorized.

Therefore the repository-side A-H alpha acceptance gate is passed for DAX-BOT 1.0-alpha.

## 5. Readiness by stage

### SHADOW
Repository-integrated CAND-001 SHADOW architecture: **1.0-alpha repository-side ACCEPTED**.

Still separate:
- current real Windows/MT5 host deployment verification: `WAITING_EXTERNAL`;
- stronger claims about current real-host Candidate operation require that evidence.

### Demo / PAPER
**NOT AUTHORIZED.**

Progress toward later demo readiness:
- broker symbol economics are captured read-only;
- fail-closed `BrokerEconomicsReadiness` exists;
- research-only cash-risk -> broker-volume sizing exists;
- BASE/BOOST/HIGH research profiles use explicit cash-at-stop budgets under a hard cap and do not infer account percentages.

Still required before demo broker orders:
- verify current DE40 demo-broker economics on the real host;
- promote a broker-aware sizing policy only after those economics are validated;
- implement and verify broker execution lifecycle ACK/REJECT/PARTIAL/FILLED/CANCELLED;
- reconnect/reconciliation against broker state;
- execution-boundary spread/stale-feed/duplicate/contradictory-state blockers;
- explicit PAPER readiness gate and user authorization.

### LIVE / real money
**NOT AUTHORIZED / NOT ELIGIBLE.**

Software correctness does not prove profitability. LIVE requires successful SHADOW and PAPER evidence, validated broker execution/reconciliation, hard risk controls, performance/robustness evidence and explicit later authorization.

## 6. Public-project engineering patterns adopted

- QuantConnect LEAN: separation of decision/alpha, risk and execution responsibilities; lower-resolution input can be consolidated upward.
- NautilusTrader: persistence/reconciliation and consistent simulation/forward semantics as first-class concerns.
- Freqtrade: dry/forward validation separate from backtest and independent protection layers such as drawdown/cooldown gates.
- vectorbt: causal event simulation and no hidden same-bar execution.

Only engineering/methodology patterns were adopted. No public strategy was copied into CAND-001.

## 7. Deliberately post-alpha 1.x scope

These do not block the minimal controllable 1.0-alpha:
- FAST/M1 candidate;
- authenticated browser/API delivery of fresh runtime telemetry;
- active Risk/Exposure UI controls;
- active News/Event reaction modes;
- broker order execution.

Their contracts/research may progress independently, but none may silently mutate CAND-001.

## 8. Bottom line

DAX-BOT 1.0-alpha is now a versioned, causal, deterministic, restart-safe, duplicate-safe, observable and explicitly order-disabled SHADOW product line in the repository. This is a software/control milestone, not a profitability milestone.

The next stronger operational milestone is current-host CAND-001 SHADOW evidence. Demo/PAPER and LIVE remain later, separately authorized stages.
