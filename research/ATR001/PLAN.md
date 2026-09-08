# ATR001 — ATR / OR-ATR Regime Research Plan

Status: RESEARCH ONLY. No V11.2 mutation. No promotion implied.

## Research question
Can causally available volatility context improve V11.2 setup selection or explain stability differences without duplicating existing OR structure filters?

## Hypothesis provenance
Prior project evidence suggests OR/ATR is one of the stronger contextual clues. Under V6 this is retained as `LEGACY_OBSERVATION`, not independent validation. All new conclusions require the V6 evidence contract.

## Separate hypothesis families
### ATR001-A — Absolute ATR
Study prior-known ATR14 level as a volatility-state descriptor.

### ATR001-B — Normalized ATR
Study ATR14 relative to prior-day range, price level or train-only distribution so broad market-level changes do not masquerade as regime evidence.

### ATR001-C — OR/ATR
Study completed opening-range size divided by causally available ATR14. This is kept separate from raw OR size.

## Causality contract
- ATR used for an entry decision must be based only on bars completed before the decision cutoff.
- OR/ATR becomes eligible only after the relevant OR is complete.
- no full-sample volatility quantile may be treated as predeclared evidence.
- train-derived boundaries must be recomputed inside each WF training slice.

## First isolated tests
1. descriptive distribution by broad era;
2. fixed/coarse categories where economically interpretable;
3. per-WF train-only quantile regime bins as a separate variant;
4. compare trade count, Return-R, PF, DD and WF stability;
5. normal / 1.5x / 2x cost stress for any trade-selection rule;
6. neighbourhood/adjacent-bin robustness;
7. only then targeted interactions with OR15/retest and BB001.

## Anti-duplication rule
ATR001 must quantify incremental information beyond raw OR size and existing V11.2 OR/ATR filters. A new volatility feature that adds negligible conditional information is not stacked merely because it is individually predictive.

## Non-goals
- no dense ATR threshold grid
- no full-sample quantile tuning counted as OOS proof
- no automatic regime switching
- no strategy promotion from aggregate PF alone
