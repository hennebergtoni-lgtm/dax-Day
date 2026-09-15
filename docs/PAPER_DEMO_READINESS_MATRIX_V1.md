# Demo / PAPER Readiness Matrix V1

Status: BINDING READINESS MAP / PAPER NOT AUTHORIZED
Updated: 2026-09-11

Purpose: separate what already exists as reusable software/contracts from what still requires broker-facing demo evidence. This document does not authorize orders.

## Current truth

- DAX-BOT 1.0-alpha repository-side acceptance: PASSED.
- SHADOW: authorized.
- Demo/PAPER broker execution: NOT authorized.
- LIVE: NOT authorized.
- `execution_capability=NONE` and `order_execution_enabled=false` remain binding.
- Explicit later user STOP-GATE is mandatory before PAPER/demo starts.

## Evidence matrix

| Capability / evidence | Current owner | Current state | PAPER interpretation |
|---|---|---|---|
| Deterministic ExecutionIntent identity | `runtime/paper_contracts.py`, Candidate intent bridge | IMPLEMENTED / TESTED in SHADOW scope | REUSE |
| Lifecycle vocabulary (submitted/ack/partial/filled/rejected/cancelled) | `runtime/paper_contracts.py` | CONTRACT EXISTS | NOT broker lifecycle evidence |
| Fill / same-bar / gap / partial-fill policy vocabulary | `runtime/paper_contracts.py`, `core/execution.py` | IMPLEMENTED contracts; SHADOW resolver exists | REUSE, but broker execution evidence still required |
| Stateful virtual position lifecycle | `runtime/candidate_virtual_lifecycle.py` | VERIFIED for SHADOW simulation | NOT broker lifecycle evidence |
| Costed virtual outcome | `runtime/candidate_virtual_outcome.py` | VERIFIED for SHADOW simulation | calibration/reference only |
| PaperTelemetry schema | `runtime/paper_contracts.py` | CONTRACT EXISTS | REUSE |
| Durable SHADOW publication idempotency | Candidate publication/checkpoint owners | VERIFIED for SHADOW | useful pattern, not broker submission proof |
| MT5 read-only host/data health | existing MT5 SHADOW gate | repository owner VERIFIED; current branch real-host recheck WAITING_EXTERNAL | required PAPER evidence |
| Broker symbol/economics observation | read-only MT5 probe + `broker_economics_readiness.py` | IMPLEMENTED; current real DE40 values WAITING_EXTERNAL | required before broker-aware sizing |
| Cash-risk -> broker-volume research translation | `research/broker_risk_sizing.py` | RESEARCH / TESTED | not promoted sizing policy |
| BASE/BOOST/HIGH cash-risk profiles | `research/risk_profile_sizing.py` | RESEARCH / TESTED | not active operator sizing |
| Loss/drawdown caps | `research/loss_cap_gate.py` | RESEARCH owner exists | requires promotion/evidence |
| Broker order lifecycle ingestion/state machine | none authorized | MISSING / NOT VERIFIED | hard PAPER blocker |
| Broker ACK/REJECT/PARTIAL/FILLED/CANCELLED evidence | none | MISSING | hard PAPER blocker |
| Broker reconnect/reconciliation | none authorized | MISSING / NOT VERIFIED | hard PAPER blocker |
| Execution-boundary protections (spread/stale/duplicate/contradictory state) with broker evidence | contracts/gates partially exist | NOT VERIFIED AS BROKER EXECUTION BOUNDARY | hard PAPER blocker |
| Explicit PAPER user authorization | `ReadinessSnapshot.paper_user_authorized` | FALSE by default | hard final blocker |

## Canonical PAPER readiness gates

`RunReadiness.PAPER` must remain blocked unless all required evidence is true. In addition to historical/data/host/risk prerequisites, the execution boundary now requires all of:

- legacy coarse `execution_boundary_verified` evidence;
- `broker_order_lifecycle_verified`;
- `broker_reconciliation_verified`;
- `execution_protection_gates_verified`;
- `paper_user_authorized`.

The coarse execution-boundary flag is retained for compatibility/provenance but can never substitute for the three explicit broker-facing evidence gates.

## Reuse rule

Do not build a second paper contract, second lifecycle vocabulary or second telemetry schema. A future demo broker adapter must translate existing `ExecutionIntent` into venue requests, feed broker states into the existing lifecycle/telemetry vocabulary, reconcile after reconnect, and remain downstream of strategy/risk/health gates.

## Next safe engineering work

Without authorizing orders, engineering may continue on:
- broker-lifecycle state/reconciliation contract tests using synthetic adapter events;
- execution protection decision gates;
- explicit evidence bundles and restart/reconciliation simulation;
- read-only broker economics collection and validation.

Actual broker order submission remains blocked until a separate later authorization step.
