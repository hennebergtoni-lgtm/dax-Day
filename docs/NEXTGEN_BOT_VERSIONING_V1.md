# DAX-BOT Next-Generation Versioning & Architecture V1

Status: PLANNED ARCHITECTURE / NO EXECUTION AUTHORIZATION

## Purpose

Create a clean product lineage for the actual DAX bot without rewriting or rebranding the frozen V11.2 research reference as if it were a proven production strategy.

The project has learned that historical evidence, research tooling, runtime infrastructure and the actual bot product must not share one ambiguous version number.

## 1. REF-V11.2 is a reference, not the target bot

`REF-V11.2` is the frozen negative comparison baseline.

It remains immutable evidence for:
- audited historical data and reproducibility;
- engine/parity checks;
- research comparisons;
- regression detection;
- proving that future changes are genuinely different.

It is NOT evidence that V11.2 is a good or profitable bot and it is not the architectural center of the next-generation bot.

## 2. New product lineage

The actual bot product is versioned independently:

- `DAX-BOT 1.0-alpha` — first intentional next-generation bot core under construction;
- `DAX-BOT 1.0-beta` — only after deterministic historical/replay parity and controlled forward PAPER_SIM evidence;
- `DAX-BOT 1.0` — only after explicitly defined validation gates are passed.

A version label never overrides status classification. PLANNED / IMPLEMENTED / VERIFIED remain separate evidence states.

Do not continue the old notebook/research numbering as `V13`, `V14`, etc. for product releases.

## 3. Candidate strategy IDs

Research hypotheses and candidate strategies do not receive bot release numbers.

Use stable candidate IDs such as `CAND-001`, `CAND-002`, `CAND-003`.

A candidate becomes part of a DAX-BOT release only through the promotion pipeline and explicit evidence.

Historical research IDs such as ADX001, BODY001, COMP001, STALE001 and TWAP001 remain research evidence and are not automatically product features.

## 4. First success criterion: controllability, not profit

The first DAX-BOT 1.0-alpha milestone is successful when the bot is operationally trustworthy even before profitability is established.

Required qualities:
- deterministic closed-bar processing;
- clear REGIME -> STRUCTURE -> ENTRY decision order;
- explicit LONG / SHORT / NO_TRADE output;
- visible planned entry, stop, target and RR when a trade is proposed;
- human-readable reason/setup codes;
- stable parameter snapshot and config fingerprint;
- deterministic decision identity;
- restart-safe state handling;
- duplicate-safe processing;
- observable health/heartbeat and last-decision state;
- replayability from persisted inputs;
- simple experiment hooks without changing runtime semantics;
- no hidden self-optimization;
- no broker order path in alpha.

## 5. Minimal hot path

Keep the actual bot path intentionally small:

`CLOSED M5 DATA -> DATA QUALITY -> STRATEGY CORE -> DECISION -> ORDER_INTENT -> PAPER OUTCOME -> TELEMETRY`

Research databases, experiment ranking, walk-forward analysis and model-selection tooling remain outside this hot path.

The bot should consume promoted, explicit configuration rather than query research infrastructure continuously.

## 6. Reuse what already works

Reuse proven project components where semantics match:
- canonical Candle/data-quality contracts;
- Europe/Berlin closed-bar causality;
- decision audit contracts;
- runtime safety gates;
- deterministic IDs/fingerprints;
- SHADOW observability and Neon telemetry patterns;
- existing paper execution-intent / outcome / ledger contracts;
- restart/recovery and reconciliation principles;
- historical/OOS evidence and multiple-testing governance.

Do not preserve complexity merely because it already exists. Every reused component must justify its place in the DAX-BOT 1.0-alpha hot path.

## 7. Deliberate simplification

DAX-BOT 1.0-alpha should prefer:
- one canonical strategy interface;
- one canonical runtime decision object;
- one paper lifecycle;
- one telemetry path;
- one persisted runtime state model;
- explicit config files/objects instead of repeated database lookups;
- shallow module boundaries where possible;
- adapters at external boundaries, not duplicate business logic.

Avoid:
- a second strategy engine;
- strategy logic duplicated between backtest and forward;
- repeated research-database queries on each bar;
- multiple competing recovery implementations in the hot path;
- notebook-specific runtime logic;
- hidden parameter selection at runtime;
- auto-promotion from research to runtime.

## 8. Public-project learning policy

Study mature public systems for engineering patterns, not for a supposedly profitable strategy.

Useful patterns may be adapted from projects such as NautilusTrader, Freqtrade, QuantConnect LEAN and vectorbt, particularly around:
- one strategy interface across simulation/forward modes;
- event-driven or deterministic processing;
- state persistence and restart behavior;
- reconciliation;
- dry-run/paper separation;
- observability;
- configuration/version isolation;
- performance testing.

The DAX strategy logic remains our own research product. Public source does not define our edge.

## 9. Alpha safety boundary

Until separately approved and verified:
- `execution_capability=NONE`;
- `order_execution_enabled=false`;
- no MT5 `order_send`;
- no real broker order;
- only read-only market data plus deterministic PAPER_SIM / virtual outcomes;
- no claim of profitability, paper readiness or live readiness.

## 10. Immediate next engineering target

Build the smallest end-to-end DAX-BOT 1.0-alpha vertical slice:

1. ingest one closed, quality-approved DE40 M5 bar;
2. update a deterministic strategy state;
3. emit an auditable `TRADE` or `NO_TRADE` decision;
4. for `TRADE`, emit deterministic side/entry/stop/target/RR and reason codes;
5. progress the virtual trade only on later closed bars;
6. persist the decision/outcome and expose health/status;
7. replay the identical input and prove identical output;
8. keep broker execution impossible by construction.

Only after this vertical slice is stable do we expand strategy sophistication or optimize performance.