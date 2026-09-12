# NextGen Dependency Isolation V1

Status: **BINDING ARCHITECTURE CONTRACT**  
Updated: **2026-09-12 — Step 2153**

Purpose: prevent the Greenfield/NextGen product core from drifting back into the historical flat `runtime`, CAND-001-specific, V11/V12, legacy-dataset or broker-specific ownership model while the strangler migration proceeds.

This contract implements the Step-2138 migration rule: legacy is evidence, compatibility input and adapter-side implementation detail — not the dependency direction of the new core.

## 1. Dependency direction

The protected NextGen core points inward toward stable domain/product abstractions. External and historical systems point inward through explicit adapters.

Allowed conceptual direction:

```text
legacy CAND-001 ----> compatibility adapter ----> canonical strategy/domain
MT5/read-only feed --> market-data adapter ------> canonical market/domain
filesystem ---------> state-store adapter -------> StateStorePort
research evidence --> promotion/conformance -----> canonical product identities

canonical domain/engine/data/state/operator -X-> runtime / CAND-001 / MT5 / legacy
```

The `-X->` direction is prohibited.

## 2. Protected canonical owners

The following current surfaces are canonical NextGen owners and must not import historical/runtime/Candidate/broker-adapter implementation owners:

- `src/daxlab/domain/*.py`;
- `src/daxlab/engine/*.py`;
- `src/daxlab/data/catalog/*.py`;
- `src/daxlab/state/*.py`;
- `src/daxlab/strategies/contracts.py` and `src/daxlab/strategies/__init__.py`;
- `src/daxlab/operator/read_model.py` and the canonical exports in `src/daxlab/operator/__init__.py`;
- `src/daxlab/research/promotion.py`;
- `src/daxlab/research/conformance.py`;
- generic adapter `src/daxlab/adapters/file_state_store.py`.

Forbidden dependencies from those owners include:

- `daxlab.runtime.*`;
- `daxlab.data.legacy_dataset`;
- `daxlab.strategies.cand001.*`;
- CAND-001-specific research owners;
- version-specific V11/V12 compatibility owners;
- concrete `daxlab.adapters.*` from the canonical core;
- direct `MetaTrader5` SDK imports.

## 3. Explicit compatibility edges

Direct imports from historical/runtime owners are currently allowed only at these audited strangler edges:

1. `src/daxlab/strategies/cand001/adapter.py`
   - maps canonical Candle/Strategy contracts to the unchanged CAND-001 runtime pipeline;
   - CAND-001 remains behavior owner until a separately proven migration retires that edge.

2. `src/daxlab/strategies/cand001/state_codec.py`
   - serializes the causal legacy `Cand001PipelineState` into the canonical restart/resume boundary;
   - this is a compatibility codec, not generic state ownership.

3. `src/daxlab/adapters/mt5_market_data.py`
   - consumes the already validated read-only runtime MT5 feed payload and maps it into canonical Candles;
   - no direct MetaTrader5 SDK dependency and no execution/order capability are permitted.

4. `src/daxlab/adapters/cand001_operator.py`
   - validates the current CAND-001 operator evidence surface and maps it into the generic read-only product view.

Adding another direct runtime/Candidate import to the NextGen side requires an explicit architecture decision and regression-contract update. It must never happen incidentally.

## 4. Historical mixed operator surfaces

`src/daxlab/operator/forward_monitoring_view.py` and `src/daxlab/operator/view_models.py` predate the canonical Product Operator V1 owner and consume research/reference models. They remain existing research/reference operator surfaces.

They are **not** exported by the canonical `daxlab.operator` package owner and must not be used as evidence that the generic Product Operator boundary may depend on research internals.

## 5. Transitional research provenance owner

`src/daxlab/research/promotion.py` currently reuses `daxlab.contracts.ExperimentManifest`, `CostModel` and `WalkForwardSpec` by deliberate Step-2144 KEEP/ADAPT decision.

This is allowed transitional provenance reuse because those primitives are generic research-governance contracts, not runtime/Candidate/broker implementations. A future move to a new package boundary may occur only when it is evidence-neutral and avoids duplicate registry ownership.

## 6. What this step does not do

This contract does **not**:

- delete or mass-move legacy files;
- rewrite CAND-001;
- alter REF-V11.2 or V12 historical evidence;
- change MT5 host behavior;
- authorize broker order submission;
- authorize PAPER or LIVE;
- require retirement of forensic compatibility owners.

The current safety boundary remains `execution_capability=NONE` / `order_execution_enabled=false` where applicable.

## 7. Enforcement

`tests/test_nextgen_dependency_isolation.py` is the executable boundary guard.

It must fail when:

- a protected canonical owner imports a forbidden historical/runtime/adapter owner;
- a new direct runtime import appears at a compatibility edge without being deliberately allowlisted;
- a direct MetaTrader5 SDK import enters the protected NextGen/compatibility surfaces.

The allowlist is intentionally small and explicit. Expanding it is an architecture change, not test maintenance.
