# SHADOW / PAPER ACCEPTANCE CONTRACT V1

Status: IMPLEMENTED CONTRACT — NOT STARTED

## Purpose
Define evidence and execution boundaries before any prospective mode starts. This document does not authorize Shadow, Paper or Live execution.

## Shadow acceptance prerequisites
Shadow may be considered only after all of the following are true:
- frozen V11.2 active reference unchanged;
- historical session dataset identity HASH_VERIFIED;
- exact engine/oracle/config fingerprints verified;
- full 2014–2019 Clean Reference Replay reconciled against frozen reference evidence;
- deterministic rerun/restart/resume checks green;
- run and decision manifests enabled;
- data-quality/failure-injection gates green;
- database integrity green;
- no unresolved lookahead/same-bar causality finding.

Shadow characteristics:
- receives prospective market data;
- produces the same Decision Core output and full NO_TRADE logging;
- sends no broker orders;
- records signal timestamp, data age, spread observation and decision latency;
- compares prospective observed feature/state distributions with historical expectations;
- cannot promote a RESEARCH filter to DEPLOYABLE.

## Paper acceptance prerequisites
Paper may be considered only after Shadow acceptance plus:
- sufficient prospective Shadow observation to detect operational drift;
- no unexplained deterministic decision drift;
- execution adapter contract verified in isolation;
- paper fill model versioned and fingerprinted;
- order lifecycle telemetry complete;
- reconnect/restart/idempotency tests green;
- explicit max spread / stale feed / duplicate order / contradictory state blockers green;
- Paper readiness gate allowed;
- user STOP-GATE review completed before start.

## Execution boundary
The strategy/Decision Core must not know broker-specific APIs.

Decision Core output -> ExecutionIntent -> ExecutionAdapter -> broker/paper venue

ExecutionAdapter responsibilities:
- translate intent to venue request;
- attach deterministic client/order identity;
- reject duplicate submissions;
- track ACK / REJECT / PARTIAL / FILLED / CANCELLED states;
- reconcile broker state after reconnect;
- expose execution failures back to health/telemetry;
- never modify strategy parameters or create a trade that the Decision Core did not request.

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
Record per intent/order:
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
Shadow: NOT STARTED.
Paper: NOT READY.
Live: NOT ELIGIBLE.

When Paper readiness becomes justified, STOP and present the complete evidence bundle to the user before any Paper/Bot start.
