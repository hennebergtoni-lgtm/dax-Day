# Step 2153 Implementation Note — NextGen Dependency Isolation

Status: **IMPLEMENTED / CI VERIFIED / FORMAL POINTER CLOSEOUT PENDING**  
Date: **2026-09-12**  
Branch: `nextgen-bot-line-v1`

## Objective

Audit and enforce the NextGen legacy-dependency isolation boundary before further feature expansion.

The binding architecture contract is `docs/NEXTGEN_DEPENDENCY_ISOLATION_V1.md`.

## Implemented guard

`tests/test_nextgen_dependency_isolation.py` adds an AST-based import-boundary regression guard.

It protects the canonical NextGen owners defined by the architecture contract:

- `src/daxlab/domain/*.py`;
- `src/daxlab/engine/*.py`;
- `src/daxlab/data/catalog/*.py`;
- `src/daxlab/state/*.py`;
- canonical strategy contracts/exports;
- canonical operator read model/exports;
- research promotion/conformance owners;
- generic file-state adapter.

The guard fails on canonical backflow into:

- `daxlab.runtime.*`;
- `daxlab.data.legacy_dataset`;
- `daxlab.strategies.cand001.*`;
- concrete `daxlab.adapters.*`;
- CAND-001-specific research modules;
- reference/version-specific V11/V12 compatibility owners;
- direct `MetaTrader5` SDK imports.

Relative imports are resolved through the AST as well as absolute imports, so changing import syntax cannot bypass the architectural boundary.

## Explicit compatibility allowlist

Only the four documented strangler edges may import the audited runtime owners, and each edge has an explicit module-level allowlist:

1. `src/daxlab/strategies/cand001/adapter.py`;
2. `src/daxlab/strategies/cand001/state_codec.py`;
3. `src/daxlab/adapters/mt5_market_data.py`;
4. `src/daxlab/adapters/cand001_operator.py`.

A new runtime import on any of these edges fails the regression guard until an explicit architecture decision changes the allowlist. Direct `MetaTrader5` SDK imports remain forbidden even on compatibility edges.

## Audit result

The executable guard passed against the current repository without requiring any production-code correction. Therefore the existing audited canonical owners already respect the declared dependency direction at this head.

No strategy rule, CAND-001 behavior, MT5 host behavior, V11.2 evidence, broker submission path, risk sizing, PAPER authorization or LIVE authorization changed in this step.

Safety remains:

- `execution_capability=NONE` where applicable;
- `order_execution_enabled=false`;
- no broker order submission authorization;
- `NO_STRATEGY_AUTO_PROMOTION` unchanged.

## Verification

Implementation commit:

- `c91404a4ed2a9565181cfa720c4f285f0e293396` — `test: enforce NextGen dependency isolation`

Exact-head CI for that implementation commit:

- `dax-bot-1x-ci` #424 — **GREEN**;
- `research-lab-ci` #1208 — **GREEN**.

The broad CI run included Ruff, the complete pytest suite, recovery reconstruction preflight, research/hypothesis/web integrity checks, static read-only runtime safety smoke, V11.2 engine probe, guarded V11.2 replay smoke and offline SHADOW soak smoke.

## Closeout rule

Step 2153 is technically implemented and CI-verified. It is not considered formally closed for workflow numbering until `docs/CURRENT_WORK_STEP.md` is updated so that 2153 is recorded completed and exactly one new active marker, Step 2154, is opened. Step 2154 must not begin before that pointer update.
