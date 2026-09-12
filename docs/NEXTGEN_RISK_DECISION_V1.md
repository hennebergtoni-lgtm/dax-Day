# NextGen Canonical Risk Decision V1

Status: **STEP-2155 PRODUCT CONTRACT**  
Date: **2026-09-12**  
Branch: `nextgen-bot-line-v1`

## Purpose

Define the first broker-neutral pre-trade risk/sizing boundary between canonical `TradePlan` and later `ExecutionIntent` construction.

## Contract

`TradePlan` remains strategy-only and contains no quantity. `RiskRequest` binds one strategy decision and plan to canonical instrument economics plus a maximum cash-loss budget. `evaluate_fixed_cash_risk()` returns deterministic `ALLOW` or `DENY`.

Canonical instrument inputs are:

- instrument identity;
- minimum quantity;
- quantity step;
- maximum quantity;
- cash loss per one price unit per one quantity;
- currency.

Sizing uses stop distance × canonical cash-loss economics. Quantity is floored to the permitted quantity step and capped at the canonical maximum. If the resulting quantity is below the minimum, the decision is `DENY` and quantity is absent.

Currency mismatch also denies fail-closed. Invalid, non-finite, non-positive or non-step-aligned contract inputs are rejected before a decision can be produced.

## Deterministic identity

`RiskRequest.request_id` fingerprints strategy-decision identity, price plan, risk budget and all canonical instrument sizing inputs. `RiskDecision.decision_id` fingerprints request identity, ALLOW/DENY action, reason codes and approved quantity when present.

Equivalent normalized inputs therefore produce equivalent identities.

## Safety boundary

This contract does **not**:

- submit an order;
- import or depend on MT5;
- grant broker capability;
- authorize PAPER;
- authorize LIVE;
- set `order_execution_enabled=true`;
- adopt legacy BASE/BOOST/HIGH research sizing profiles as product policy;
- change CAND-001 strategy semantics or frozen V11.2 evidence.

An `ALLOW` risk decision means only that a quantity passed this deterministic pre-trade sizing contract. A later separately governed step must map that approved decision into `ExecutionIntent`; broker submission remains a different capability and authorization boundary.
