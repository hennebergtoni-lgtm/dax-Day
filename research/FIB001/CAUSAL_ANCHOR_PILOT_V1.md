# FIB001 Causal Anchor Pilot V1

Status: IMPLEMENTATION PILOT / RESEARCH ONLY

## Goal
Prove that Fibonacci impulse anchors and retracement observations can be generated and validated without hindsight before any profitability interpretation.

## Scope
Pilot implements only:
- explicit immutable anchor record;
- explicit anchor rule id;
- anchor confirmation timestamp;
- retracement observation timestamp;
- entry timestamp when linked to a V11.2 setup;
- timing/causality validation;
- fixed coarse zone classification using the existing Fibonacci math core.

## Out of scope
- swing discovery optimization;
- dense Fibonacci ratios;
- profitability selection;
- interaction with BB001/ATR001/STRUCT001;
- entry or exit changes;
- Paper/Live use.

## Initial anchor rules
The implementation accepts only predeclared rule ids:
- OR_COMPLETED_IMPULSE
- CONFIRMED_BREAKOUT_IMPULSE
- STRUCTURE_CONFIRMED_IMPULSE

The validator does not discover these anchors. Upstream feature generators must provide already-causal anchors and their actual confirmation time.

## Timing gate
Eligible observation requires:
- impulse_start_time <= impulse_end_time <= anchor_confirmation_time;
- anchor_confirmation_time < retracement_observation_time;
- retracement_observation_time <= entry_time when an entry is supplied;
- for entry-filter use, anchor/feature state remains strictly before entry.

## Failure behavior
Missing timezone information, unknown anchor rule, reversed timestamps, observation before/equal confirmation, observation after entry, or zero-length impulse fail closed.

## Evidence order
1. unit tests for timing and rule validation;
2. prefix/no-lookahead property test on generated anchors;
3. descriptive distribution on audited 2014–2019 data;
4. only then fixed-zone OOS/WF analysis.

No result from this pilot changes V11.2 or authorizes promotion.
