# PAPER Readiness Gap Matrix V1

Status: BINDING PLANNING / EVIDENCE MATRIX — PAPER NOT AUTHORIZED
Updated: 2026-09-11
Branch: `nextgen-bot-line-v1`

Purpose: turn the coarse goal "get to real demo/PAPER quickly" into explicit evidence lanes without creating broker-order capability prematurely. This matrix maps directly to `ReadinessSnapshot` / `RunKind.PAPER` and to `docs/SHADOW_PAPER_ACCEPTANCE_V1.md`.

## Binding safety boundary

- SHADOW is the only currently authorized prospective mode.
- PAPER/demo broker execution is **not authorized**.
- LIVE is **not authorized**.
- `execution_capability=NONE` / `order_execution_enabled=false` remain binding on the current product runtime.
- No item marked IMPLEMENTABLE_BEFORE_PAPER may introduce `mt5.order_send`, a broker-order submission path or an execution-capability inversion.
- Explicit user authorization remains an independent final STOP-gate even after all technical evidence is green.

## Evidence matrix

| Readiness / capability | Current owner/evidence | Current state | Next evidence required | Lane |
| --- | --- | --- | --- | --- |
| CI / engine / DB / technical replay | existing CI, reference/replay/database gates | VERIFIED for repository alpha | maintain exact-head GREEN | REUSE |
| Dataset identity | frozen audited V11.2/reference evidence | HASH_VERIFIED | preserve unchanged | REUSE |
| Audited bundle / full reference replay | frozen/reproduced reference evidence | VERIFIED for current repository milestone | preserve provenance | REUSE |
| Legacy execution boundary | `paper_contracts.py`, Decision→ExecutionIntent separation | IMPLEMENTED / CONTRACT-VERIFIED | retain as coarse compatibility gate only | REUSE |
| ExecutionIntent + deterministic client identity | `paper_contracts.py`, `candidate_execution_intent.py` | IMPLEMENTED / SHADOW-SAFE | later bind to broker-neutral order-request envelope; do not duplicate | REUSE |
| Fill/same-bar/gap model vocabulary | `paper_contracts.py`, `core/execution.py`, Candidate virtual lifecycle | IMPLEMENTED for simulation | broker execution telemetry must record observed fill/slippage separately | REUSE |
| Stateful virtual lifecycle | `candidate_virtual_lifecycle.py` | VERIFIED for SHADOW simulation | does not satisfy broker order-lifecycle evidence | REUSE AS MODEL ONLY |
| Restart/publication idempotency | Candidate checkpoint/publication journal | VERIFIED for SHADOW | reuse identity/persistence patterns; broker order state needs its own reconciliation evidence | REUSE PATTERN |
| Current Windows/MT5 read-only health | existing host gate/supervisor + deployment runbook | repository integration VERIFIED; current-branch real host proof pending | run current branch on real Windows/MT5 and capture GREEN evidence | WAITING_EXTERNAL |
| Real DE40 broker economics | extended read-only MT5 symbol probe | collector IMPLEMENTED; current values not yet verified | observe/verify volume/tick/contract/currency/margin metadata on real demo broker | WAITING_EXTERNAL |
| Broker-risk sizing translation | `broker_risk_sizing.py`, `broker_economics_readiness.py` | algorithm/research tests IMPLEMENTED | bind to verified real DE40 economics and validate rounding/cash-at-stop semantics | PARTIAL / WAITING_EXTERNAL |
| BASE/BOOST/HIGH risk profile | `risk_profile_sizing.py` | research policy + lineage IMPLEMENTED | promote explicit validated cash-risk budgets/hard cap; never infer from account-allocation percentages | PARTIAL |
| Loss-cap policy | `loss_cap_gate.py` | research gate IMPLEMENTED | promote validated thresholds and prove interaction with sizing/admission | PARTIAL |
| Broker order lifecycle | only enum/vocabulary exists in `PaperLifecycleState`; no broker-facing state owner | NOT IMPLEMENTED | broker-neutral deterministic lifecycle ledger for REQUESTED/ACK/REJECT/PARTIAL/FILLED/CANCELLED with identity and transition validation | IMPLEMENTABLE_BEFORE_PAPER |
| Broker reconciliation | existing `restart_reconcile.py` is replay/SHADOW freshness only, not broker order reconciliation | NOT IMPLEMENTED | broker-neutral reconciliation contract comparing local expected orders/positions with venue observations; contradictory/unknown state fails closed | IMPLEMENTABLE_BEFORE_PAPER |
| Execution protection gates | SHADOW has stale/data/duplicate/health protections; broker-facing submission protections are not one verified owner | PARTIAL | broker-neutral verdict for stale feed, extreme spread, duplicate identity, contradictory reconciliation, unsafe sizing and session/health blocks | IMPLEMENTABLE_BEFORE_PAPER |
| Order lifecycle telemetry | `PaperTelemetry` vocabulary exists | CONTRACT ONLY | append-only broker-neutral telemetry records covering request/ACK/reject/partial/fill/cancel/reconcile events | IMPLEMENTABLE_BEFORE_PAPER |
| Demo broker adapter / order submission | intentionally absent | NOT IMPLEMENTED / NOT AUTHORIZED | only after preceding evidence owners exist and current readiness remains fail-closed; creation still requires explicit PAPER authorization boundary | AUTHORIZATION-GATED |
| User PAPER authorization | `paper_user_authorized` readiness gate | FALSE by default / fail-closed | explicit user STOP-gate review after complete evidence bundle | USER_STOP_GATE |
| LIVE | no authorization/path | BLOCKED | independent future gate after PAPER evidence; not part of current plan | DEFERRED |

## Key conclusion

The fastest safe route to realistic demo trading is to finish the **broker-neutral execution evidence layer first**, because that work is independent of the unavailable Windows host and does not require order capability. The real Windows/MT5 and DE40-economics lanes remain `WAITING_EXTERNAL` in parallel.

The three immediate repository work owners are therefore:

1. **Broker order lifecycle ledger** — deterministic state machine and immutable event records; no API calls.
2. **Broker reconciliation contract** — expected-local vs observed-venue comparison with contradiction/unknown fail-closed; venue observations are plain data, not fetched here.
3. **Execution protection verdict** — a single fail-closed pre-submission evidence object over health/freshness/spread/duplicate/reconciliation/sizing/session inputs; it cannot submit anything.

Only after those are independently regression-tested should a future separately authorized demo adapter translate an already-approved `ExecutionIntent` into an MT5 demo request.

## What does not count as broker evidence

The following must never set `broker_order_lifecycle_verified`, `broker_reconciliation_verified` or `execution_protection_gates_verified` to true by themselves:

- the existence of enum names or dataclasses;
- successful SHADOW virtual fills;
- historical backtest/replay results;
- deterministic client IDs alone;
- a green read-only MT5 feed;
- synthetic/mock broker fixtures alone;
- CI success without the specific evidence required by the gate;
- user authorization by itself.

## Promotion rule

A future evidence bundle may set a PAPER readiness boolean true only when the corresponding owner has a named version/fingerprint, regression proof, and — where the gate is broker-specific — real demo-broker evidence. Readiness booleans are summaries of evidence, not substitutes for evidence.
