# DAX-BOT NextGen Greenfield Architecture V1

Status: **ARCHITECTURE BASELINE / IMPLEMENTATION NOT IMPLIED**  
Date: 2026-09-12  
Branch: `nextgen-bot-line-v1`

## 1. Purpose

This document defines the target architecture for the NextGen DAX Daytrading Bot from first principles.

Binding design rule:

> **Legacy is evidence, provenance and compatibility input — not the chassis of the NextGen system.**

The frozen V11.2 baseline, recovered 2014–2019 CSV surface, Google Drive materialization path, Colab workflows, CAND-001, MT5 and historical version-specific modules remain valuable where they prove behavior or provide adapters. None of them is allowed to define the architecture merely because it already exists.

This is deliberately not a rewrite-everything mandate. Existing components are retained when they already satisfy the target boundaries and invariants.

## 2. Goals

The system must support a disciplined progression:

`RESEARCH -> historical validation/OOS/WF -> SHADOW -> PAPER -> LIVE`

with explicit authorization gates between stages. PAPER and LIVE are not authorized by this document. `order_execution_enabled=false` remains binding until a separate authorized change proves otherwise.

The architecture must optimize for:

1. deterministic behavior and replayability;
2. backtest/forward/product semantic parity;
3. fast research iteration without weakening production semantics;
4. explicit data/time/session provenance;
5. broker independence in the core;
6. restart/recovery/reconciliation as first-class behavior;
7. fail-closed risk and authorization boundaries;
8. inspectable operator telemetry and evidence;
9. reproducibility of historical conclusions without preserving accidental legacy layouts;
10. incremental migration with regression evidence rather than a big-bang rewrite.

## 3. Non-goals

This document does not:

- claim profitability;
- promote CAND-001 or any research hypothesis;
- authorize PAPER or LIVE trading;
- authorize order submission;
- redefine the frozen V11.2 baseline;
- require a specific third-party framework;
- require Rust, DuckDB, Polars, Arrow or Parquet everywhere simply because other projects use them;
- delete historical evidence required for reproducibility.

## 4. Primary architecture decision: two speeds, shared semantics

NextGen intentionally has two execution speeds.

### 4.1 Research plane — throughput optimized

Research may use vectorized/compiled/batch techniques to screen large hypothesis spaces quickly. It may evaluate many parameters, features, regimes and time slices in parallel or columnar form.

Research acceleration is not allowed to create a second definition of strategy semantics. A promoted candidate must compile or map into the canonical product contracts and pass conformance tests against deterministic replay.

### 4.2 Product plane — determinism optimized

Historical deterministic replay, SHADOW, PAPER and eventually LIVE use the same domain model and strategy/risk/execution semantics. Environment-specific differences are expressed through ports/adapters, clocks, fill/execution models and authorization — not duplicated strategy logic.

The product plane is event-oriented and processes a defined sequence of canonical market/execution events. Exact internal implementation may evolve, but event ordering and state transitions must be reproducible.

## 5. Target logical planes

### 5.1 Domain and deterministic engine

The domain layer owns broker-neutral, storage-neutral types and rules, including eventually:

- instrument identity;
- market event identity;
- `Candle`, `Tick` and data-quality semantics;
- event time, receipt time and canonical timezone rules;
- session/calendar identity;
- strategy state and transition contract;
- signal and decision records;
- trade/execution intent;
- order lifecycle and fills;
- position/portfolio state;
- risk decision;
- deterministic event sequencing;
- explicit ambiguity/fill policies.

The domain/engine layer MUST NOT import MT5, Google Drive, CSV loaders, operator views or candidate-specific host code.

### 5.2 Data plane

The canonical data plane is independent from the recovered legacy CSV layout.

Target responsibilities:

- immutable/raw ingest layer;
- normalization into canonical typed schemas;
- explicit source, instrument, event time, receipt time, timezone/session metadata;
- validation and quality state;
- deterministic dataset manifests/fingerprints;
- columnar historical catalog, with **Parquet/Arrow as the preferred V1 direction** unless implementation evidence proves a better fit;
- partition/query strategy suitable for DAX intraday research and replay;
- reproducible conversion from legacy CSV/Drive data through adapters;
- query access that does not require rereading 1,673 individual CSV files merely because V11.2 did so.

DuckDB, Polars or equivalent tools are implementation options for efficient catalog access. They are not domain contracts.

### 5.3 Research plane

Research is split by responsibility rather than by historical version name.

Target responsibilities:

- experiment specification and registry;
- feature/hypothesis library;
- fast screening engine;
- walk-forward/OOS evaluation;
- cost/slippage stress;
- multiple-testing controls;
- DSR/PBO/SPA and related robustness methods where appropriate;
- filter ablation/overlap/Pareto analysis;
- failure and no-trade diagnostics;
- trial chronology/provenance;
- candidate promotion package.

Strategy-specific features such as ATR, Bollinger, Fibonacci, gap, momentum or market-structure logic should be plugins/configured hypothesis components where practical, not separate orchestration architectures.

### 5.4 Strategy/candidate layer

A strategy candidate is a replaceable plugin over canonical domain inputs and outputs.

A candidate must not own:

- broker connectivity;
- persistence implementation;
- operator UI;
- host scheduling;
- authorization to execute orders.

A candidate may own deterministic strategy state, feature state, signal rules, trade-plan construction and candidate-specific configuration.

CAND-001 becomes one implementation of this contract, not the definition of the contract.

### 5.5 Risk, portfolio and execution domain

Risk and execution are explicit product components rather than research afterthoughts.

Target responsibilities include:

- pre-trade risk decisions;
- sizing contract;
- daily/session loss controls;
- order intent identity and idempotency;
- order lifecycle state machine;
- fill/execution modeling for simulation;
- broker reconciliation;
- protection/stop ownership;
- position and exposure state;
- explicit capability/authorization state.

Research-derived sizing proposals do not automatically become product authorization.

### 5.6 Ports and adapters

External systems live behind explicit interfaces.

Initial port families:

- `MarketDataPort`;
- `HistoricalDataPort`;
- `BrokerExecutionPort`;
- `BrokerStatePort`;
- `Clock`;
- `StateStore`;
- optional telemetry/event sinks.

MT5 is an adapter implementing relevant ports. Legacy CSV/Google Drive import is an adapter. Future broker or data providers must be addable without modifying strategy semantics.

### 5.7 State, recovery and evidence

Restart safety is a first-class architecture property.

Target responsibilities:

- append-only material event/evidence journal where appropriate;
- snapshots/checkpoints;
- deterministic resume identity;
- idempotent replay;
- broker reconciliation before trusting local state;
- dataset/engine/config/source-commit fingerprints;
- tamper/drift detection;
- fail-closed recovery when identity cannot be proven.

A file-backed implementation may remain acceptable for local SHADOW or evidence bundles. The contract must not require files as the only future state backend.

### 5.8 Operator and observability plane

Operator surfaces consume product state; they do not define it.

Target responsibilities:

- health states and blockers;
- freshness/clock/data quality;
- last processed event/bar;
- strategy/risk decision visibility;
- order/reconciliation/protection state when applicable;
- restart/recovery status;
- performance and degradation monitoring;
- iPhone-friendly summaries;
- alerts and runbook evidence.

### 5.9 Operations and governance

Host automation, Windows Scheduled Tasks, CI, preflights, parity checks, deployment scripts and repository governance remain outside the domain core.

These may be platform-specific. Their job is to prove and operate the product safely, not to leak platform assumptions into strategy logic.

## 6. Target dependency direction

Dependencies point inward toward stable domain contracts.

```text
                    +----------------------+
                    |   Operator / Ops     |
                    +----------+-----------+
                               |
            +------------------+------------------+
            |                                     |
+-----------v-----------+             +-----------v-----------+
| Broker/Data Adapters  |             | Research / Promotion  |
| MT5, legacy import... |             | fast screening        |
+-----------+-----------+             +-----------+-----------+
            |                                     |
            +------------------+------------------+
                               |
                    +----------v-----------+
                    | Product Engine       |
                    | replay/shadow/paper  |
                    +----------+-----------+
                               |
          +--------------------+--------------------+
          |                    |                    |
+---------v--------+  +--------v---------+  +-------v---------+
| Strategy Plugin |  | Risk / Execution |  | State / Evidence|
+---------+--------+  +--------+---------+  +-------+---------+
          |                    |                    |
          +--------------------+--------------------+
                               |
                    +----------v-----------+
                    | Canonical Domain     |
                    | types + invariants   |
                    +----------+-----------+
                               |
                    +----------v-----------+
                    | Canonical Data Plane |
                    | schema/catalog       |
                    +----------------------+
```

The diagram expresses logical dependency ownership, not a requirement that every box be a separate process.

## 7. Current-repository classification

Classification is by capability group. Individual files may move after dependency analysis.

### 7.1 KEEP — preserve the principle and, where clean, implementation

- timezone-aware canonical market-data validation and data-quality invariants;
- pure deterministic strategy-transition style demonstrated by the current CAND-001 pipeline;
- conservative no-hindsight OHLC ambiguity policy;
- broker-neutral order-lifecycle state-machine semantics;
- deterministic identities/fingerprints;
- fail-closed safety checks and explicit execution-capability fields;
- run/dataset/engine/config provenance;
- replay/resume compatibility checks;
- experiment registry principle: experiments are explicit records, never hidden notebook state;
- multiple-testing/robustness research methods where their statistical contracts remain valid;
- operator/health separation;
- CI, integrity checks, parity checks and visible runbook evidence.

`KEEP` does not require retaining the current file path or module name.

### 7.2 ADAPT — strong component, wrong boundary or excessive coupling

Representative current surfaces:

- `runtime/contracts.py` -> canonical domain market-data contracts;
- `runtime/paper_contracts.py` -> split generic `ExecutionIntent`/execution types from PAPER simulation configuration;
- `runtime/broker_order_lifecycle.py` -> execution-domain lifecycle independent of `paper_contracts` naming;
- `runtime/manifests.py`, `checkpoint.py`, recovery owners -> generic run/evidence/state contracts;
- `runtime/candidate_pipeline.py` -> strategy-plugin/product-engine boundary; preserve purity but remove candidate-specific architecture ownership;
- `runtime/mt5_*` -> broker/data adapter package behind ports;
- operator views -> consume generic product telemetry/event contracts;
- research robustness methods -> organize as reusable methods rather than strategy/version orchestration;
- file-backed recovery/state -> backend implementation behind generic state contracts.

### 7.3 ISOLATE-LEGACY — preserve for evidence/reproducibility, never drive new design

- `data/legacy_dataset.py` and its exact 1,673-file/288-row/103-session-bar V11.2 contract;
- `runtime/v112_bridge.py`;
- version-specific `v12_*` research modules;
- historical Drive/CSV materialization workflow;
- Colab-specific transport assumptions;
- CAND-001 historical OOS evidence readers/exporters/replay paths that exist to reproduce existing evidence;
- legacy recovery compatibility owners already classified as forensic compatibility.

These surfaces may remain indefinitely if required to reproduce verified historical results. They must be accessed through compatibility boundaries.

### 7.4 REPLACE — current concept is insufficient for the target

- recovered CSV directory layout as the primary historical-data architecture;
- flat `runtime` package as the main architectural boundary;
- candidate/version names as owners of generic platform capabilities;
- implicit or one-off orchestration for moving a research idea toward a product candidate;
- any future design that duplicates strategy semantics separately for backtest, SHADOW, PAPER and LIVE;
- any direct MT5 dependency from the canonical strategy/domain core.

### 7.5 RETIRE — only after migration and evidence sealing

Candidates for eventual retirement:

- duplicate domain/contract definitions after one canonical owner exists;
- compatibility wrappers that no longer have active or forensic consumers;
- superseded one-off scripts once their outputs and provenance are reproducible through canonical workflows;
- version-specific orchestration with no remaining evidence purpose.

Nothing required to reproduce a VERIFIED historical claim may be retired merely for cleanliness.

## 8. Package direction

The exact names may evolve, but new work should move toward boundaries similar to:

```text
src/daxlab/
  domain/                 # stable broker/storage-neutral types + invariants
  engine/                 # deterministic event loop / replay / product orchestration
  data/
    schema/               # canonical market-data schemas
    catalog/              # historical columnar catalog + manifests
    ingest/               # normalization/validation pipeline
    adapters/legacy/      # old CSV/Drive compatibility
  research/
    methods/              # WF, multiple testing, DSR/PBO/SPA, diagnostics
    features/             # reusable feature/hypothesis implementations
    experiments/          # specs, registries, trial provenance
    promotion/            # research candidate -> canonical candidate artifact
  strategies/
    cand001/              # one strategy implementation, not platform architecture
  risk/                   # product risk decisions and sizing contracts
  execution/              # intents, lifecycle, fills, reconciliation/protection
  adapters/
    brokers/mt5/          # MT5-specific host/execution implementation
    marketdata/mt5/       # MT5-specific market-data implementation where useful
  state/                  # journal/snapshot/checkpoint/store interfaces
  operator/               # health/telemetry/views
```

A migration may temporarily maintain compatibility imports. New generic code should not be added to legacy paths merely to avoid moving boundaries.

## 9. Canonical data V1 direction

The first new historical catalog should be deliberately small and provable.

Minimum canonical bar fields should include, subject to implementation review:

- canonical instrument ID;
- source/venue/broker provenance;
- timeframe;
- event/open time;
- close time;
- OHLC;
- volume when available;
- receipt/ingest timestamp where meaningful;
- quality state;
- source record identity/fingerprint;
- schema version.

Time is stored canonically in UTC. Exchange/broker/session timezone is explicit metadata/configuration and is never inferred silently from a timestamp that merely looks plausible.

Legacy Berlin-session slicing remains a reproducibility transform, not the canonical storage definition.

## 10. Research-to-product promotion contract

A research result cannot become a product candidate merely because a backtest metric is attractive.

A promotable candidate bundle must eventually bind at least:

- hypothesis/strategy identity and version;
- exact strategy configuration fingerprint;
- feature definitions and parameters;
- dataset/catalog manifest fingerprint;
- train/OOS/WF split contract;
- cost/fill assumptions;
- robustness/multiple-testing evidence references;
- deterministic product-strategy artifact/hash;
- source commit;
- known limitations;
- promotion state.

Promotion changes artifact status, not order authorization.

The product engine must be able to replay the promoted artifact over the same canonical events and pass conformance checks against the research semantics within declared tolerances/policies.

## 11. Backtest -> SHADOW -> PAPER -> LIVE parity rule

The canonical strategy, risk and state-transition semantics are shared.

Environment-specific substitutions are limited to explicit components such as:

- historical vs real-time clock;
- historical catalog vs live market-data adapter;
- simulation fill model vs broker execution adapter;
- synthetic account state vs broker reconciliation;
- authorization/capability gate.

Any mode-specific strategy branch requires explicit justification and test evidence. Silent mode-specific behavior is prohibited.

Backtest assumptions such as same-bar ordering, gap fills, latency, spread, slippage and commission must be explicit and fingerprinted.

## 12. Performance rule

Correctness is the first invariant; performance is then optimized at the appropriate layer.

- research may vectorize/compile aggressively;
- catalog queries should avoid repeated full CSV scans;
- deterministic product processing should favor stable event ordering and measurable latency;
- native/Rust acceleration is permitted only where profiling proves Python is a material bottleneck;
- architecture must not be complicated in advance merely to imitate larger frameworks.

## 13. Migration strategy — strangler, not big-bang rewrite

Migration proceeds beside the working system.

1. define canonical domain contracts and ports;
2. add conformance tests against currently trusted pure components;
3. build canonical historical data catalog V1 and import one legacy slice through an adapter;
4. prove catalog fingerprints/round-trip/UTC/session semantics;
5. create generic strategy plugin contract and adapt CAND-001 without changing its strategy behavior;
6. create deterministic product-engine vertical slice over the canonical catalog;
7. create fast research experiment contract and promotion artifact;
8. prove research-to-product conformance on frozen fixtures;
9. move MT5 behind explicit adapters while preserving current read-only SHADOW safety;
10. migrate state/recovery/operator consumers incrementally;
11. isolate legacy imports and stop adding new generic behavior to them;
12. retire only proven-redundant compatibility paths after evidence audit.

At every stage the previous verified path remains available until the replacement is proven.

## 14. Hard acceptance criteria for the architecture migration

A NextGen slice is not accepted merely because it runs.

It must prove, where applicable:

- deterministic replay from the same canonical event sequence;
- no lookahead/future-data access;
- explicit time/session semantics;
- dataset/config/engine/source provenance;
- idempotent restart/resume;
- fail-closed behavior on corrupt/missing identity;
- broker-neutral core dependencies;
- no order capability introduced by research/SHADOW code;
- conformance between research candidate and product strategy semantics;
- tests on Windows/host-specific behavior before marking host claims VERIFIED;
- measurable runtime where performance is a stated objective.

## 15. Immediate implementation priority after Step 2138

**Step 2139 should build the smallest canonical domain/port foundation, not migrate strategy logic or historical bulk data.**

Recommended Step-2139 scope:

- create canonical broker/storage-neutral market-data and execution domain contracts;
- define minimal port protocols/interfaces for historical/live market data and state/execution boundaries;
- preserve existing imports through compatibility adapters where needed;
- add dependency/conformance tests proving the new foundation has no MT5/legacy-dataset/CAND-001 dependency;
- do not alter strategy behavior, execution authorization, V11.2 or current SHADOW runtime behavior.

The next data-catalog step should then consume those canonical contracts rather than inventing a second schema.

## 16. Current architecture verdict

The repository is not a failed prototype. It already contains several strong safety, provenance, recovery and deterministic-transition components.

The main issue is **boundary placement**:

- too much generic product capability accumulated in `runtime`;
- generic execution concepts are partly named as PAPER concepts;
- strategy/candidate/broker/legacy concerns share package boundaries;
- the historical data layer is still compatibility-oriented rather than a modern canonical catalog;
- research contains strong methods but mixes methods, features, candidates, forward analytics and version-specific history.

Therefore the NextGen task is neither “continue the old structure” nor “throw everything away.” It is to **extract the good invariants into a clean Greenfield architecture and force legacy to connect through adapters.**

## 17. External architecture references used for design sanity-check

These are reference patterns, not dependencies or copied strategy logic:

- NautilusTrader Architecture: https://nautilustrader.io/docs/latest/concepts/architecture/
- NautilusTrader Data / Parquet Data Catalog: https://nautilustrader.io/docs/latest/concepts/data/
- QuantConnect LEAN algorithm engine / streaming model: https://www.quantconnect.com/docs/v2/writing-algorithms/key-concepts/algorithm-engine
- VectorBT: https://vectorbt.dev/
- DuckDB Parquet guide: https://duckdb.org/docs/current/guides/file_formats/query_parquet
- DuckDB SQL on Arrow: https://duckdb.org/docs/current/guides/python/sql_on_arrow

The project remains responsible for validating every adopted pattern against its own requirements, data and host behavior.
