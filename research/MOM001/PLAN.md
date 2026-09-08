# MOM001 — Momentum Research Plan

Status: RESEARCH ONLY. No V11.2 mutation. No promotion implied.

## Research question
Does causally available short-horizon momentum improve V11.2 setup selection beyond market structure, volatility and Bollinger position?

## Initial momentum families
- completed-bar return over fixed short horizons
- consecutive directional closes
- body/range expansion on completed bars
- distance from recent completed-bar mean normalized by ATR

## Causality
Only fully completed bars before `entry_time` may contribute. Same-entry-bar close/body information is not eligible for an entry taken at that bar's open.

## Initial fixed hypotheses
1. directional momentum agreement may improve breakout/retest continuation quality;
2. excessive short-term extension may reduce retest quality;
3. momentum may duplicate BB001 price-position or STRUCT001 state, so incremental contribution must be measured conditionally.

## Parameter discipline
- small fixed horizon set only;
- no exhaustive return-window sweep;
- no OOS-selected momentum cutoff counted as validation;
- train-only normalization allowed if recomputed per WF.

## Required reporting
- trade-count impact
- Return-R / PF / DD
- WF/broad-era stability
- overlap with BB001/STRUCT001/ATR001
- cost stress where selection changes
- no-trade increase

## Non-goals
- no oscillator zoo
- no indicator stacking for its own sake
- no trend prediction claim
- no automatic promotion
