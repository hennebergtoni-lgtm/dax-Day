# ATR001 V6 Volatility Regime Contract

Status: BINDING RESEARCH SPEC

## Purpose
Define volatility states without leaking OOS information into regime boundaries.

## Allowed boundary modes
### Fixed coarse boundaries
Only where the scale has a defensible economic interpretation and the boundaries are declared before evaluation.

### Per-WF train-only quantiles
Quantile cutoffs are recomputed independently inside each WF training slice and frozen for that WF's OOS segment.

## Forbidden boundary modes
- full-sample quantiles used as if predeclared;
- OOS-derived thresholds reused on the same OOS sample for validation;
- threshold changes selected after inspecting aggregate performance;
- dense threshold sweeps without a separate fresh-validation plan.

## Core regime candidates
### Absolute ATR14
Used mainly as descriptive context; raw values may drift with the DAX price level and broad eras.

### Normalized ATR14
Candidates include:
- ATR14 / prior-day range
- ATR14 / prior completed session close
- ATR14 percentile within the WF training slice

### OR / ATR14
Calculated only after the chosen OR is complete. Existing historical OR/ATR results are provenance/context, not V6 validation.

## Reporting
Every regime test reports:
- regime definition and provenance
- train boundary values by WF when train-derived
- OOS trade count per regime
- Return-R / Avg-R / PF / DD
- positive/negative WF coverage
- normal / 1.5x / 2x cost stress when trade selection changes
- no-trade increase
- broad-era concentration

## Stability rule
A regime is not retained merely because one bucket has high PF. Evidence must survive trade-count, broad-era and neighbouring-boundary checks.

## Interaction rule
Before interaction with BB001, structure or session features, ATR001 must show isolated incremental information beyond raw OR size and the frozen V11.2 OR/ATR dimensions.
