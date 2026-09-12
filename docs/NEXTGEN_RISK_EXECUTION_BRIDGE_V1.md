# NextGen Risk-to-ExecutionIntent Bridge V1

Status: **STEP-2156 PRODUCT CONTRACT / STEP-2164 ADMISSION HARDENING**  
Date: **2026-09-12**  
Branch: `nextgen-bot-line-v1`

## Purpose

Define the canonical broker-neutral bridge from approved Risk V1 plus approved Loss/Exposure Admission into the existing NextGen `ExecutionIntent` contract.

## Consumer audit

The existing CAND-001 SHADOW path remains separate and continues to use its existing runtime execution-intent contracts. It is not migrated or modified by this bridge hardening.

The canonical NextGen `daxlab.domain.execution.ExecutionIntent` remains a broker-neutral product intent; it is not an order submission contract.

## Provenance identity

For causal compatibility, canonical `ExecutionIntent.decision_id` continues to carry the originating strategy decision ID. `provenance_fingerprint` now binds:

- strategy decision ID;
- risk request ID;
- risk decision ID;
- loss/exposure policy fingerprint;
- loss/exposure observation fingerprint;
- loss/exposure admission decision fingerprint;
- schema identity `DAXLAB_RISK_ADMISSION_TO_EXECUTION_PROVENANCE_V1`.

## Bridge rules

`build_execution_intent_from_risk()`:

1. reconstructs and verifies the canonical `RiskRequest` identity;
2. re-evaluates Risk V1 and requires the supplied `RiskDecision` to equal the canonical result;
3. requires Risk V1 `ALLOW` with a quantity;
4. re-evaluates canonical Loss/Exposure Admission from the supplied policy and observation;
5. requires the supplied admission decision to equal the canonical result;
6. requires Loss/Exposure Admission `ALLOW`;
7. maps LONG → BUY and SHORT → SELL;
8. carries exactly the risk-approved quantity and canonical trade-plan prices;
9. produces deterministic provenance and intent identity for equivalent inputs.

This design fails closed if risk or admission evidence is blocked, stale/mismatched or tampered after canonical construction.

## Separation of ownership

The bridge does not duplicate either algorithm:

- quantity sizing remains owned by canonical Risk V1;
- daily/weekly loss, consecutive-loss and open-position admission remains owned by canonical Loss/Exposure Admission.

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

An `ExecutionIntent` remains a deterministic product-domain intent only. Broker execution and environment authorization require later, separately governed evidence and authorization.
