# FIB001 V6 Causal Anchor Contract

Status: BINDING RESEARCH SPEC / NO PROMOTION

## Purpose
Keep Fibonacci retracement measurement separate from hindsight swing discovery.

## Core rule
`retracement_levels(start, end)` is only valid research evidence when both anchor prices and their timestamps were already known before the first retracement observation being evaluated.

## Allowed anchor families
### A. Opening-range impulse
- start/end are derived from a completed opening-range structure;
- OR completion time must precede any retracement observation;
- no later bar may redefine the completed OR anchor.

### B. Confirmed-breakout impulse
- breakout must be confirmed on a completed candle;
- impulse end may only advance using a predeclared causal rule;
- retracement testing begins only after the impulse-end state is frozen for that observation.

### C. Structure-confirmed impulse
- a BOS/structure event may define an impulse only when the confirmation rule itself uses information available at confirmation time;
- if a pivot needs N future bars for confirmation, its state time is the later confirmation time, not the historical pivot timestamp.

## Forbidden anchors
- visually selected best swing after observing the subsequent retracement;
- future-high/future-low anchors;
- zig-zag or pivot labels backdated to the turning candle when confirmation required future candles;
- choosing between multiple possible anchors based on which gives the best OOS result;
- redefining the impulse after the retracement has already begun.

## Fixed initial zones
The first isolated V6 test keeps the previously declared coarse natural zones only:
- 33.3–38.2%
- 38.2–50.0%
- 50.0–61.8%
- 61.8–66.7%

No dense Fibonacci grid is allowed in the first isolated test.

## Required evidence fields
Each FIB observation must be able to expose:
- impulse_start_price
- impulse_start_time
- impulse_end_price
- impulse_end_time
- anchor_confirmation_time
- retracement_observation_time
- anchor_rule_id
- normalized_retracement
- zone_id
- causality_pass

Mandatory timing relationship for eligible evidence:
`anchor_confirmation_time < retracement_observation_time <= entry_time`

If FIB is used as an entry filter, all anchor/feature state must still satisfy the global V6 rule `state_time < entry_time`.

## First V6 test order
1. anchor-generation causality tests;
2. descriptive retracement distribution;
3. fixed-zone OOS/WF analysis without changing execution;
4. trade-count and broad-era stability;
5. exact cost stress only where the filter changes trade selection;
6. interactions only after isolated evidence is defensible.
