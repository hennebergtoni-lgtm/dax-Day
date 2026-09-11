# Web Operator Controls V2 — Planned Contract

Status: PLANNED / NOT ACTIVE
Updated: 2026-09-11

## Purpose

Define the future operator-control surface requested for DAX-BOT without weakening the binding read-only Web Interface V1 contract before backend controls are independently verified.

Web V1 remains read-only. This document does not authorize browser-side mutation, PAPER, LIVE, broker sizing or strategy switching.

## Proposed controls

### 1. Trading tempo

Display values:
- `NORMAL_M5`
- `FAST_M1_RESEARCH`

Backend owner before activation:
- a separately validated FAST-M1 Candidate/ControlPolicy;
- verified CLOSED-M1 source and deterministic M1→M5 aggregation;
- Candidate ID/config fingerprint/evidence lineage.

Until those gates pass, FAST is rendered disabled with status `RESEARCH_NOT_VALIDATED`.

### 2. Risk / Exposure profile

Display values:
- `BASE`
- `BOOST`
- `HIGH`

Backend owner before activation:
- one verified broker-aware sizing/risk module;
- explicit distinction between allocation, margin/notional and cash loss at stop;
- hard drawdown/daily-loss/cooldown caps.

Operator-requested EUR 500 / EUR 1,000 allocation reference points are research requirements, not approved stop-loss cash risk.

Until broker economics and profile gates pass, controls are disabled with status `BROKER_RISK_SEMANTICS_UNVERIFIED`.

### 3. News / Event handling

Display values:
- `OBSERVE_ONLY`
- `EVENT_GUARD`
- `NEWS_REACTIVE_RESEARCH`

Backend owner before activation:
- validated EventContext/EventRiskSnapshot provider;
- explicit source freshness/provenance;
- versioned admission/risk policy.

`OBSERVE_ONLY` may be surfaced before it can change admission. `EVENT_GUARD` requires historical + SHADOW validation. `NEWS_REACTIVE_RESEARCH` must never be promoted merely because a current headline appears important.

## Request architecture

When a control eventually becomes active, the browser must not mutate strategy state directly.

Preferred flow:

`UI request -> authenticated/audited operator-request boundary -> validated backend policy owner -> accepted/rejected ControlState -> read-only OperatorSnapshot reflection`

The UI displays the accepted effective state. It is never the canonical owner.

## Safety rules

- No browser-side quantity calculation.
- No order submission API in the UI.
- No free-form strategy parameter editing.
- Only discrete prevalidated profiles/modes may become selectable.
- Every accepted control change receives an immutable event ID, operator timestamp and policy/config fingerprint.
- A rejected request must remain visible as rejected; do not pretend the requested state became active.
- Stale/unknown backend state fails closed and disables escalation controls.
- Control elevation may be time/session limited and auto-revert according to the backend policy.
- PAPER and LIVE authorization remain separate gates and are not represented by these controls.

## V1 compatibility

`docs/WEB_INTERFACE_CONTRACT_V1.md` remains binding now. V2 controls can be designed/rendered as disabled research UI, but activation requires a later explicit supersession contract after backend verification.
