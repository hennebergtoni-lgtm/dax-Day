# NextGen Risk-to-ExecutionIntent Bridge V1

Status: **STEP-2156 PRODUCT CONTRACT**  
Date: **2026-09-12**  
Branch: `nextgen-bot-line-v1`

## Purpose

Define the first canonical broker-neutral bridge from an approved Risk V1 decision into the existing NextGen `ExecutionIntent` contract.

## Consumer audit

The existing CAND-001 SHADOW path remains separate and continues to use `daxlab.runtime.paper_contracts.ExecutionIntent`. It is not migrated or modified by this step.

The canonical NextGen `daxlab.domain.execution.ExecutionIntent` remains a broker-neutral product intent consumed through `ExecutionIntentSinkPort`; it is not an order submission contract.

For backward-compatible causal identity, canonical `ExecutionIntent.decision_id` continues to carry the originating strategy decision ID. The Risk V1 chain is bound into `provenance_fingerprint` using:

- strategy decision ID;
- risk request ID;
- risk decision ID;
- schema identity `DAXLAB_RISK_TO_EXECUTION_PROVENANCE_V1`.

## Bridge rules

`build_execution_intent_from_risk()`:

1. reconstructs and verifies the canonical `RiskRequest` identity;
2. re-evaluates Risk V1 and requires the supplied `RiskDecision` to equal the canonical result;
3. refuses `DENY` or missing quantity;
4. maps LONG → BUY and SHORT → SELL;
5. carries exactly the risk-approved quantity;
6. carries the canonical trade-plan instrument, entry, stop and target unchanged;
7. produces deterministic provenance and intent identity for equivalent inputs.

This design fails closed if a request ID, decision, quantity, instrument economics or risk budget is tampered after canonical construction.

## Safety boundary

The bridge does **not**:

- import MT5 or any broker SDK;
- call `order_send`;
- create a broker execution adapter;
- authorize PAPER;
- authorize LIVE;
- set `order_execution_enabled=true`;
- change CAND-001 SHADOW behavior;
- change frozen V11.2 evidence.

An `ExecutionIntent` remains a deterministic product-domain intent only. Broker execution and environment authorization require later, separately governed steps.
