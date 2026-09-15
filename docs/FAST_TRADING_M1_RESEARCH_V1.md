# DAX-BOT Fast Trading / M1 Research V1

Status: RESEARCH / PLANNED — NOT AN AUTHORIZED RUNTIME MODE
Updated: 2026-09-11

## Purpose

Capture the operator idea of a deliberately faster short-horizon mode without mutating the verified semantics of CAND-001 or silently promoting one-minute trading into the product.

The intended operator experience may later expose a simple tempo control in the web interface, but the control must select a separately validated candidate/profile rather than changing the timeframe of an already-running strategy in place.

## 1. Binding separation

- `CAND-001` remains the current DAX-BOT 1.0-alpha candidate on closed `5m` bars.
- A one-minute strategy is a new research candidate, provisionally named `FAST-M1` until a normal Candidate ID is preregistered.
- Switching NORMAL/FAST must never rewrite the ruleset, config fingerprint, RunManifest or evidence lineage of CAND-001.
- FAST-M1 requires its own backtest, OOS/WF, robustness, transaction-cost stress, forward SHADOW and later promotion gates.
- PAPER and LIVE remain unauthorized.

## 2. Preferred market-data architecture

Do not maintain unrelated M1 and M5 market-data truths when one lower-resolution source can deterministically generate both.

Preferred future design:

`validated CLOSED M1 source -> canonical M1 bars -> deterministic 5m aggregation -> M1 candidate and M5 candidate consumers`

This follows the reusable architecture seen in mature public systems: subscribe to the smallest required time resolution and consolidate upward. It also makes M1/M5 parity, gap detection, restart reconstruction and cross-timeframe provenance testable from one stream.

The current verified Windows host path remains CLOSED-M5 only. Therefore M1 is not implemented by this document. Before implementation the project must add and verify a read-only CLOSED-M1 broker feed contract and deterministic M1->M5 parity tests.

## 3. Causality rules

FAST-M1 must preserve the same causal discipline as the current product:

- only CLOSED one-minute bars may alter strategy state;
- no use of the still-open current minute;
- event_time / close_time semantics are explicit;
- duplicate/out-of-order/gap handling is fail-closed;
- transport observation time must not mutate market/strategy identity;
- a signal cannot create a retroactive fill on its own decision bar unless a separately versioned policy is explicitly researched and proven.

## 4. Why small-profit targets need a stricter cost gate

A desire to capture very small moves (for example sub-euro/euro account-level profits) is not by itself evidence of edge. At M1 frequency, spread, slippage, latency and commissions consume a larger fraction of the expected move.

FAST-M1 therefore requires:

- cost-to-gross-edge ratio reporting;
- normal + stressed spread/slippage assumptions;
- minimum expected move after costs;
- trade-frequency and turnover analysis;
- same-bar/gap sensitivity;
- latency sensitivity on the real Windows host;
- no promotion from gross profit alone.

## 5. Proposed future operator control

Web label: `Trading tempo`

Initial conceptual values:

- `NORMAL_M5` — current validated product path.
- `FAST_M1_RESEARCH` — visible only when a separately validated M1 candidate exists; SHADOW first.

A future automatic volatility-driven tempo selector may be researched separately, but it must be a versioned Regime/ControlPolicy with evidence. A manual operator feeling of "the market is moving" may request a validated FAST profile; it must not bypass candidate/risk gates.

## 6. Promotion gates before FAST can affect execution

1. Verified CLOSED-M1 broker data contract.
2. Deterministic M1->M5 aggregation parity.
3. Dedicated Candidate ID/config fingerprint/ruleset.
4. Historical M1 data audit.
5. Backtest + OOS/WF + multiple-testing controls.
6. Explicit high-turnover cost/slippage stress.
7. Restart/duplicate/cross-cycle parity.
8. Forward SHADOW observation.
9. Separate PAPER acceptance and explicit authorization.
10. LIVE remains a later independent authorization boundary.

## 7. Reuse rule

Reuse the existing candidate pipeline, DecisionRecord, host gate, SHADOW lifecycle, publication/idempotency, checkpoint, operator snapshot and recovery architecture wherever semantics match. Do not create a second platform for M1.
