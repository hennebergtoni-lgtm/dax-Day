# ATR001 — Predeclared Re-Test Contract V1

Status: FROZEN RESEARCH HYPOTHESIS. Promotion blocked. V11.2 unchanged.

## Frozen hypothesis
The only candidate allowed into the next ATR001 re-test is:
- OR = 15 minutes
- ATR regime = HIGH
- OR/ATR regime = MID
- regime boundaries = tertiles fit separately per OR family using only the canonical 45-day WF training slice
- boundaries frozen before the corresponding 20-day OOS slice
- both breakout and retest remain included
- existing V11.2 stop, RR, direction, cost and execution semantics remain unchanged

## Discovery provenance
`OOS_DIAGNOSTIC_DERIVED`.
The discovery sample cannot be re-labelled as independent proof.

## Forbidden changes
Before the next independent/prospective evidence stage, do not:
- move q33/q67 boundaries
- replace tertiles with quartiles/deciles
- drop breakout or retest because one looks worse
- add BB/FIB/session/liquidity interactions
- change OR15 to another OR length
- search ATR periods
- choose a different cost model
- change V11.2 execution semantics

Any such change creates a new hypothesis ID and resets evidence maturity.

## Acceptance dimensions for a future re-test
The frozen candidate must be evaluated on:
- trade count
- Return-R
- PF
- max drawdown R
- positive/negative active WFs
- calendar-period stability
- normal / 1.5x / 2x cost stress
- sensitivity to data/feed perturbation where applicable
- prospective/replay evidence before any promotion

No single aggregate PF or Return-R is sufficient.

## Current evidence
Historical OOS diagnostic only. It is promising but not independent validation.

## Promotion state
`promotion_allowed=false`
Paper/Live remain blocked.
