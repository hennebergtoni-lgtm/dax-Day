# NextGen Broker Lifecycle Conformance V1

Status: **STEP-2157 PRODUCT / COMPATIBILITY CONTRACT**  
Date: **2026-09-12**  
Branch: `nextgen-bot-line-v1`

## Purpose

Reuse the repository's existing broker-neutral order lifecycle, reconciliation and execution-protection semantics behind canonical NextGen `ExecutionIntent` without inventing a second lifecycle vocabulary or adding venue submission capability.

## Audit result

| Existing owner | Decision | Reason |
| --- | --- | --- |
| `runtime.paper_contracts.PaperLifecycleState` vocabulary | `REUSE` | ACK / REJECT / PARTIAL / FILLED / CANCELLED are already the binding shared states. |
| `runtime.broker_order_lifecycle` | `REUSE` | Existing deterministic state machine, terminal-state rules, fill accounting, tamper-evident persistence and execution-disabled evidence are suitable. |
| `runtime.broker_reconciliation` | `REUSE` | Existing normalized venue observation and exact fail-closed reconciliation are adapter-neutral. |
| `runtime.broker_execution_protection` | `REUSE` | Existing protection verdict combines host/feed/spread/reconciliation/duplicate/sizing/risk/session evidence and explicitly is not execution authorization. |

No second lifecycle, reconciliation or protection vocabulary is created.

## Canonical entry adaptation

`runtime.nextgen_broker_lifecycle.begin_nextgen_order_lifecycle()` is the only new compatibility entry surface in this step.

It:

- accepts canonical `daxlab.domain.execution.ExecutionIntent`;
- preserves canonical `intent_id` exactly as lifecycle `client_order_id`;
- fingerprints the full canonical intent as lifecycle intent provenance;
- creates only the existing `REQUESTED` lifecycle/event evidence;
- delegates all later ACK/REJECT/PARTIAL/FILLED/CANCELLED/EXPIRED transitions to the existing lifecycle owner;
- imports no venue SDK and has no submission function.

## Synthetic conformance proof

Tests run the canonical chain:

`TradePlan -> RiskRequest/RiskDecision -> canonical ExecutionIntent -> existing BrokerOrderLifecycle -> VenueOrderObservation -> reconciliation -> execution-protection evidence`

The proof covers:

- deterministic canonical-intent lifecycle start;
- canonical `intent_id` -> `client_order_id` identity preservation;
- ACK -> PARTIAL -> FILLED reuse;
- consistent normalized venue reconciliation;
- contradictory venue truth failing closed;
- existing protection owner producing only `ALLOW_EVIDENCE`, never execution authorization;
- static absence of MT5 / venue submission dependencies in the new bridge.

## Safety boundary

This step does **not**:

- connect to a broker;
- submit, modify or cancel an order;
- add an MT5 execution adapter;
- authorize PAPER/demo broker execution;
- authorize LIVE;
- change `order_execution_enabled=false`;
- change CAND-001 strategy semantics;
- change frozen V11.2 evidence.

`ALLOW_EVIDENCE` is evidence completeness only. It is not permission to submit an order.
