# SHADOW / PAPER ACCEPTANCE CONTRACT V1

Status: IMPLEMENTED CONTRACT — SHADOW AUTHORIZED / CURRENT CANDIDATE HOST VERIFICATION WAITING_EXTERNAL / PAPER NOT READY / LIVE NOT ELIGIBLE
Updated: 2026-09-12

## Purpose
Define evidence and execution boundaries for SHADOW and any later PAPER stage. This contract records the current stage but does not itself create broker execution authority. Current authorization truth must be reconciled against the canonical Masterstand, current acceptance status, exact repository evidence and fresh runtime evidence.

## Shadow acceptance prerequisites
The original SHADOW acceptance prerequisites are preserved:
- frozen V11.2 active reference unchanged;
- historical session dataset identity HASH_VERIFIED;
- exact engine/oracle/config fingerprints verified;
- full 2014–2019 Clean Reference Replay reconciled against frozen reference evidence;
- deterministic rerun/restart/resume checks green;
- run and decision manifests enabled;
- data-quality/failure-injection gates green;
- database integrity green;
- no unresolved lookahead/same-bar causality finding.

Current project state: the no-order SHADOW stage is authorized and repository-side DAX-BOT 1.0-alpha / CAND-001 SHADOW integration is accepted. Existing real Forward SHADOW evidence is a verified milestone only and must not be reused as a fresh runtime-state claim. Fresh current-host claims require fresh runtime evidence.

Current-branch CAND-001 Windows/MT5 real-host verification remains a separate `WAITING_EXTERNAL` lane under `docs/CAND001_WINDOWS_SHADOW_DEPLOYMENT_RUNBOOK_V1.md`. Repository/CI verification alone does not convert that host-specific lane to VERIFIED.

Shadow characteristics:
- receives prospective market data;
- produces the same Decision Core output and full NO_TRADE logging;
- sends no broker orders;
- records signal timestamp, data age, spread observation and decision latency;
- compares prospective observed feature/state distributions with historical expectations;
- cannot promote a RESEARCH filter to DEPLOYABLE;
- preserves `execution_capability=NONE` and `order_execution_enabled=false` on the current host-facing product path.

## Paper acceptance prerequisites
Paper may be considered only after the required Shadow evidence plus:
- sufficient prospective Shadow observation to detect operational drift;
- no unexplained deterministic decision drift;
- execution adapter contract verified in isolation;
- paper fill model versioned and fingerprinted;
- broker order lifecycle evidence complete;
- one broker execution checkpoint/restart evidence path verified so lifecycle state and telemetry idempotency state cannot advance from different persistence boundaries;
- broker reconciliation evidence complete;
- execution-protection gates verified;
- order lifecycle telemetry complete;
- reconnect/restart/idempotency tests green;
- explicit max spread / stale feed / duplicate order / contradictory state blockers green;
- broker economics and broker-aware sizing/risk evidence sufficient for the intended PAPER venue;
- Paper readiness gate allowed;
- user STOP-GATE review completed before start.

Repository-only fixtures and CI prove software behavior but do not by themselves satisfy broker-facing lifecycle, checkpoint, reconciliation, protection, economics/risk or telemetry readiness booleans.

## Execution boundary
The strategy/Decision Core must not know broker-specific APIs.

Decision Core output -> ExecutionIntent -> ExecutionAdapter -> broker/paper venue

ExecutionAdapter responsibilities for any later authorized PAPER stage:
- translate intent to venue request;
- attach deterministic client/order identity;
- reject duplicate submissions;
- track ACK / REJECT / PARTIAL / FILLED / CANCELLED states;
- reconcile broker state after reconnect;
- expose execution failures back to health/telemetry;
- never modify strategy parameters or create a trade that the Decision Core did not request.

No broker submission adapter or order API is authorized by the current SHADOW stage.

## Paper fill model
Paper execution must not assume perfect fills. The fill model must version and record at least:
- requested price/time;
- observed bid/ask or spread proxy;
- modeled slippage;
- modeled commission;
- latency assumption;
- stop/target ordering rule for same-bar ambiguity;
- gap-through behavior;
- partial-fill policy if modeled;
- resulting fill price and R impact.

Historical research cost models remain separate evidence from prospective paper execution telemetry.

## Execution degradation telemetry
Record per intent/order in a later authorized PAPER stage:
- decision_id;
- run_manifest_fingerprint;
- order/client id;
- requested/accepted/filled/cancelled timestamps;
- requested and filled price;
- spread at decision and submission;
- slippage versus requested price;
- total modeled/observed cost;
- rejection/cancel reason;
- feed age and health state;
- reconnect/reconciliation events.

## Hard blockers
The following are not operator-overridable:
- DATA_UNSAFE;
- FEED_INTERRUPTION;
- EXTREME_SPREAD;
- CONTRADICTORY_STATE;
- dataset/engine/config/run-manifest mismatch;
- duplicate order identity;
- unresolved broker reconciliation state.

## Current decision
- SHADOW: **AUTHORIZED — NO BROKER ORDERS**. Repository-side CAND-001 SHADOW integration is accepted. Current-branch real Windows/MT5 CAND-001 host verification remains `WAITING_EXTERNAL` and must be completed before stronger current-host claims.
- PAPER/demo broker execution: **NOT READY / NOT AUTHORIZED**. Broker-facing evidence, venue economics/risk validation, readiness and the explicit user STOP-GATE remain required.
- LIVE: **NOT ELIGIBLE / NOT AUTHORIZED**.

When PAPER readiness becomes justified, STOP and present the complete evidence bundle to the user before any PAPER broker start. No historical/OOS result, SHADOW milestone, CI result or document update can auto-promote execution authority.