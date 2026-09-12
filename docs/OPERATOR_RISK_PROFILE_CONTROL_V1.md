# Operator Risk / Exposure Profile Control V1

Status: RESEARCH / PLANNED — NO BROKER SIZING AUTHORIZATION
Updated: 2026-09-11

## Purpose

Capture the operator requirement for a simple web control that can deliberately increase capital allocation when the operator accepts more risk, without confusing capital allocation, leverage, margin, position notional and actual loss-at-stop.

## 1. Critical semantic separation

The following quantities are not interchangeable:

- account equity;
- capital allocation / capital-at-work;
- broker margin;
- leveraged notional exposure;
- quantity / lots / contracts;
- risk distance to stop;
- cash loss if the stop is reached;
- daily drawdown.

The operator idea of using e.g. EUR 500 or EUR 1,000 from a EUR 2,000 account is recorded as a future capital-allocation preference. It is NOT permission to risk EUR 500 or EUR 1,000 of loss on one trade.

## 2. Current product truth

Current CAND-001 sizing is `NORMALIZED_SIMULATION_UNIT` only. It intentionally does not claim DE40 broker-volume, margin, contract-size or account-risk semantics.

Therefore no web switch may currently alter real position size. PAPER and LIVE remain unauthorized and `execution_capability=NONE` / `order_execution_enabled=false` remain binding.

## 3. Proposed future UI concept

Web label: `Risk / Exposure profile`

Conceptual profiles:

- `BASE` — default validated profile.
- `BOOST` — higher validated allocation/exposure.
- `HIGH` — highest separately validated allocation/exposure; visually prominent and time-limited.

Operator-requested allocation reference points for later research:

- approximately EUR 500 capital allocation;
- approximately EUR 1,000 capital allocation from a EUR 2,000 account as the extreme requested setting.

These are requirements to model, not approved max-loss values or production sizing.

## 4. Mandatory risk owner before activation

A future broker-aware sizing/risk module must be the single owner of:

- account equity snapshot;
- exact DE40 contract/lot economics;
- broker margin/leverage semantics;
- entry/stop distance;
- cash risk at stop;
- total open notional exposure;
- max loss per trade;
- daily loss cap;
- weekly drawdown cap;
- consecutive-loss cooldown;
- max concurrent positions;
- profile expiry/reversion.

The web control may request a profile. It must not calculate broker quantity itself.

## 5. Hard safety properties

Even a future `HIGH` profile must remain inside separately validated hard caps.

- Increasing allocation must never disable a stop.
- Increasing allocation must never bypass admission, health, news/event or drawdown gates.
- Profile changes must be versioned/auditable operator events.
- A profile must map to deterministic sizing inputs and leave evidence in the OperatorSnapshot/RunManifest lineage.
- Profile changes must not alter strategy signal semantics.
- The highest profile should expire automatically at a defined boundary (for example session end) unless explicitly renewed in a later authorized product stage.
- Failures or stale account/broker economics fail closed to the lower/default profile or no new trade, never upward.

## 6. Required validation before broker-aware use

1. Verify DE40 demo-broker quantity/contract/margin semantics.
2. Implement one deterministic broker-economics translation from stop distance to cash risk.
3. Backtest/forward-test each discrete profile separately.
4. Stress spread/slippage/gaps and losing streaks.
5. Model drawdown and risk-of-ruin sensitivity.
6. Verify restart persistence of selected profile and automatic expiry.
7. Add operator UI only as a request layer over the validated risk owner.
8. PAPER still requires explicit later authorization.
9. LIVE remains independently blocked until later authorization.

## 7. Reuse / public-system principle

Reuse the project’s existing admission, lifecycle, health and recovery gates. Add protections as independent gates rather than embedding risk escalation inside strategy entry logic. Mature bot systems similarly separate position sizing from drawdown/cooldown protections.

## 8. Acceptance rule

No implementation is allowed to interpret `HIGH` as "risk 50% of account equity on one stop" merely because 50% of account capital may be allocated. Actual max-loss semantics must be explicit, independently capped and verified first.
