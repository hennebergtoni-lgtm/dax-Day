# NextGen Compatibility / Retirement Audit V1

Status: **BINDING STEP-2154 AUDIT EVIDENCE**  
Date: **2026-09-12**  
Branch: `nextgen-bot-line-v1`  
Audit base head: `0af66af8c4b54e6b1252844fd4de2afcf1f77904`

## Purpose

Classify the remaining documented NextGen compatibility and historical surfaces before any retirement action.

This audit follows `docs/NEXTGEN_DEPENDENCY_ISOLATION_V1.md`. Classification is evidence-based and does not authorize deletion, mass moves, strategy changes, broker execution, PAPER, or LIVE.

Allowed classifications:

- `RETAIN_WITH_REASON` — an active consumer, parity/restart requirement, research/reference function, forensic/provenance obligation, or deliberate architecture boundary still exists.
- `RETIRE_CANDIDATE` — no material active/forensic consumer remains and equivalent replacement/parity evidence exists. A candidate still requires a separate retirement step before deletion.

## Result

**7 / 7 audited surfaces = `RETAIN_WITH_REASON`.**  
**0 / 7 = `RETIRE_CANDIDATE`.**

There is therefore no evidence-neutral deletion action to perform at this head.

| Surface | Current role / evidence | Classification | Retirement precondition |
| --- | --- | --- | --- |
| `src/daxlab/strategies/cand001/adapter.py` | Active CAND-001 → canonical `StrategyPlugin` strangler edge. `tests/test_nextgen_cand001_strategy_adapter.py` proves old-pipeline-vs-plugin semantic parity and 1:1 admitted trade-plan mapping while the existing CAND-001 pipeline remains behavior owner. | `RETAIN_WITH_REASON` | Replace legacy pipeline/state ownership with a canonical strategy owner and prove behavior/evidence parity independently. |
| `src/daxlab/strategies/cand001/state_codec.py` | Active compatibility codec for legacy `Cand001PipelineState` at the canonical resume boundary. `tests/test_nextgen_cand001_resume.py` and finite-value coverage prove exact canonical round-trip and real Candidate restart parity across interruption points. | `RETAIN_WITH_REASON` | Canonicalize Candidate state ownership/codec and prove old checkpoint/state compatibility is no longer required for restart or forensic evidence. |
| `src/daxlab/adapters/mt5_market_data.py` | Intentional read-only isolation layer from validated runtime `ClosedM5Feed` into canonical `CandleSourcePort`. `tests/test_nextgen_mt5_market_data_adapter.py` proves OHLC/time parity and fail-closed behavior. It imports neither the MetaTrader5 SDK nor order/execution capability. | `RETAIN_WITH_REASON` | A replacement market-data adapter must satisfy the same canonical port and preserve equivalent feed/provenance/fail-closed evidence. No such redundant replacement exists at this head. |
| `src/daxlab/adapters/cand001_operator.py` | Active adapter from Candidate-specific operator evidence into generic `ProductOperatorViewV1`. `tests/test_nextgen_operator_read_model.py` verifies health/freshness/recovery/reconciliation mapping while keeping Candidate regime/signal/trade-plan/virtual-position internals out of the generic schema. | `RETAIN_WITH_REASON` | Candidate operator production itself becomes canonical/product-neutral, or this mapping is proven unused and evidence-equivalent replacement exists. |
| `src/daxlab/operator/forward_monitoring_view.py` | Historical Research/Reference operator surface, deliberately not exported by canonical `daxlab.operator`. `tests/test_forward_monitoring_operator_view.py` still actively verifies deterministic read-only SHADOW degradation evidence, `execution_capability=NONE`, no composite score and no automatic promotion. The generic Product Operator V1 does not replace this research-specific semantic surface. | `RETAIN_WITH_REASON` | Research/Reference degradation monitoring is migrated to an evidence-equivalent owner and the historical schema/provenance is no longer required. Mere existence of `ProductOperatorViewV1` is insufficient. |
| `src/daxlab/operator/view_models.py` | Historical Research/Reference operator surface, deliberately not exported by canonical `daxlab.operator`. `tests/test_operator_view_models.py` still verifies visible-but-disabled research filters and V11.2 reference-health blockers. The generic Product Operator V1 intentionally does not own those research/reference semantics. | `RETAIN_WITH_REASON` | Migrate filter-registry/reference-health semantics to an evidence-equivalent research/reference owner and prove no active or forensic consumer depends on the current schema. |
| `src/daxlab/research/promotion.py` → `daxlab.contracts.{ExperimentManifest, CostModel, WalkForwardSpec}` | Deliberate Step-2144 KEEP/ADAPT reuse of generic research-governance contracts. `tests/test_nextgen_research_promotion.py` uses the same owners to bind experiment, 45/20/20 WF, normal/1.5x/2x cost and provenance identities while keeping order/PAPER/LIVE authorization false. This is not runtime/Candidate/broker backflow. | `RETAIN_WITH_REASON` | Move only when a single canonical research-contract owner can replace these primitives evidence-neutrally without duplicate registry/identity ownership or fingerprint drift. |

## Operator isolation finding

`src/daxlab/operator/__init__.py` exports only the canonical Product Operator V1 owner from `read_model.py`. It does not re-export `forward_monitoring_view.py` or `view_models.py`.

Therefore the two historical operator modules are retained as isolated Research/Reference surfaces, not as dependencies or public ownership of the canonical Product Operator boundary.

## Research provenance finding

`src/daxlab/research/promotion.py` imports only `CostModel`, `ExperimentManifest`, and `WalkForwardSpec` from the shared `daxlab.contracts` owner for this transition. These types are generic research-governance primitives and have no broker/order/runtime/Candidate behavior.

Duplicating them inside a new NextGen package now would create competing provenance/fingerprint ownership without evidence benefit.

## Decision

No audited surface qualifies as `RETIRE_CANDIDATE` at this head.

The correct architecture action is **retain + isolate + keep retirement preconditions explicit**, not delete for cosmetic cleanup.

Future retirement must be a separate numbered work unit and must prove all of the following before physical deletion:

1. zero active production/research/test consumer that still owns unique semantics;
2. no unresolved forensic/provenance requirement;
3. evidence-equivalent replacement where applicable;
4. deterministic parity or compatibility proof where applicable;
5. no V11.2/CAND-001/SHADOW evidence drift;
6. no relaxation of the Step-2153 dependency isolation gate.

## Safety / non-change statement

Step 2154 changes no strategy rule, CAND-001 behavior, historical V11.2/V12 evidence, MT5 host behavior, risk sizing, execution capability or authorization.

Safety remains:

- `execution_capability=NONE` where applicable;
- `order_execution_enabled=false`;
- no broker order submission authorization;
- PAPER not authorized;
- LIVE not authorized;
- `NO_STRATEGY_AUTO_PROMOTION` unchanged.
